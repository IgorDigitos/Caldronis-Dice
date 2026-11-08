"""Controle do processo criado pelo painel; não depende de Tkinter ou Discord."""

import os
import queue
import re
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

STATES = {
    "starting": "Conectando ao Discord…",
    "online": "Ligado e conectado ao Discord",
    "reconnecting": "Reconectando ao Discord…",
    "stopping": "Desligando…",
    "stopped": "Desligado",
    "missing_config": "Confira DISCORD_TOKEN (e DEV_GUILD_ID, se usado) no .env do projeto.",
    "already_running": "O bot já está aberto. Desligue a outra instância antes de ligar aqui.",
    "connection_error": "Falha de conexão. Confira token, intents, rede e acesso ao banco.",
    "error": "O bot não conseguiu iniciar. Confira a configuração do projeto.",
}
ERROR_STATES = {"missing_config", "already_running", "connection_error", "error"}

# Somente estes códigos viram texto no painel; o worker nunca envia texto livre.
# Nível: info, ok, warn ou error. "{}" recebe um argumento curto e validado.
LOG_MESSAGES = {
    "config_loaded": ("info", "Configuração local carregada (.env)."),
    "database_ready": ("info", "Banco de dados de atributos pronto."),
    "sync_global": ("info", "Sincronizando comandos slash globais…"),
    "sync_guild": ("info", "Sincronizando comandos slash no servidor de testes…"),
    "synced": ("info", "{} comandos slash sincronizados."),
    "login": ("info", "Autenticando na API do Discord via HTTPS…"),
    "gateway": ("info", "Abrindo conexão segura com o gateway do Discord (WSS)…"),
    "ready": ("ok", "Conectado e pronto em {} servidor(es)."),
    "resumed": ("ok", "Sessão com o Discord retomada."),
    "disconnected": ("warn", "Conexão com o Discord perdida; tentando reconectar…"),
    "rate_limited": ("warn", "O Discord limitou as requisições; aguardando liberação."),
    "library_warning": ("warn", "Aviso interno da biblioteca do Discord (detalhes omitidos)."),
    "guild_join": ("info", "Bot adicionado a um servidor."),
    "guild_remove": ("info", "Bot removido de um servidor."),
    "roll": ("info", "Rolagem respondida."),
    "roll_rejected": ("warn", "Rolagem recusada: expressão inválida ou fora dos limites."),
    "storage_error": ("error", "Falha ao acessar o banco de dados."),
    "command": ("info", "Comando /{} executado."),
    "mesa_ready": ("ok", "Ponte com o Caldron Sheets ligada."),
    "mesa_off": ("info", "Ponte com o Caldron Sheets desligada (sem FIREBASE_CREDENCIAL no .env)."),
    "mesa_error": ("error", "Falha ao ligar a ponte com o Caldron Sheets. Confira a credencial."),
    "mesa_roll": ("info", "Rolagem do app respondida."),
    "mesa_expirada": ("warn", "Rolagem do app expirada (sem internet ou bot desligado)."),
    "mesa_limite": ("warn", "Rolagens do app em excesso; pedido recusado."),
    "mesa_discord": ("warn", "Rolagem do app feita, mas o webhook do Discord falhou."),
    "mesa_falha": ("error", "Falha inesperada ao processar rolagem do app."),
    "command_error": ("warn", "Um comando slash não foi concluído."),
    "stop_received": ("info", "Pedido de desligamento recebido pelo bot."),
    "closing": ("info", "Encerrando a conexão com o Discord…"),
}
LOG_ARGUMENT = re.compile(r"[a-z0-9][a-z0-9 _-]{0,39}", re.ASCII)
MAX_LOG_ENTRIES = 500


@dataclass(frozen=True)
class LogEntry:
    time: datetime
    level: str
    text: str


def decode_event(line: str):
    """Converte uma linha do worker em estado (str) ou log (LogEntry); ignora o resto."""
    line = line.strip()
    if line.startswith("STATE:"):
        state = line[6:]
        return state if state in STATES else None
    if not line.startswith("LOG:"):
        return None
    code, _, argument = line[4:].partition(":")
    if code not in LOG_MESSAGES:
        return None
    level, template = LOG_MESSAGES[code]
    needs_argument = "{}" in template
    if needs_argument != bool(argument):
        return None
    if needs_argument:
        if not LOG_ARGUMENT.fullmatch(argument):
            return None
        template = template.format(argument)
    return LogEntry(datetime.now(), level, template)


class BotController:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.process = None
        self.state = "stopped"
        self.events = queue.SimpleQueue()
        self.online_since = None
        self._stop_deadline = None
        self._killed = False
        self._pending_logs: list[LogEntry] = []

    @property
    def running(self):
        return self.process is not None and self.process.poll() is None

    def _log(self, level: str, text: str):
        self._pending_logs.append(LogEntry(datetime.now(), level, text))
        del self._pending_logs[:-MAX_LOG_ENTRIES]

    def take_logs(self) -> list[LogEntry]:
        """Entrega os registros novos uma única vez, na ordem em que ocorreram."""
        self.poll()
        logs, self._pending_logs = self._pending_logs, []
        return logs

    def start(self):
        self.poll()
        if self.running:
            return
        executable = self.project_dir / ".venv" / "Scripts" / "python.exe"
        worker = self.project_dir / "desktop_worker.py"
        if not executable.is_file() or not worker.is_file():
            self._log("error", "Ambiente .venv ou desktop_worker.py ausente na pasta do projeto.")
            raise FileNotFoundError(
                "Ambiente Python ou arquivos do bot ausentes na pasta do projeto."
            )
        self.events = queue.SimpleQueue()
        environment = os.environ.copy()
        environment["PYTHONIOENCODING"] = "utf-8"
        environment["PYTHONUNBUFFERED"] = "1"
        self._log("info", "Iniciando o processo do bot…")
        self.process = subprocess.Popen(
            [str(executable), "-u", str(worker)],
            cwd=self.project_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=environment,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        self.state = "starting"
        self.online_since = None
        self._stop_deadline = None
        self._killed = False
        threading.Thread(
            target=self._read_events, args=(self.process, self.events), daemon=True
        ).start()

    @staticmethod
    def _read_events(process, events):
        # Somente estados e códigos conhecidos entram no painel; não ecoar logs do Discord.
        try:
            for line in process.stdout:
                event = decode_event(line)
                if event is not None:
                    events.put(event)
        except (OSError, ValueError):
            pass

    def stop(self):
        if not self.running or self._stop_deadline is not None:
            return
        self.state = "stopping"
        self.online_since = None
        self._stop_deadline = time.monotonic() + 10
        self._log("info", "Desligamento solicitado.")
        try:
            self.process.stdin.write("STOP\n")
            self.process.stdin.flush()
        except (OSError, ValueError):
            pass

    def _set_state(self, state: str):
        if state == self.state:
            return
        self.state = state
        self.online_since = time.monotonic() if state == "online" else None
        if state in ERROR_STATES:
            self._log("error", STATES[state])

    def poll(self):
        while not self.events.empty():
            event = self.events.get()
            if isinstance(event, LogEntry):
                self._log(event.level, event.text)
            elif self._stop_deadline is None:
                self._set_state(event)
        if self.process is None:
            return self.state
        code = self.process.poll()
        if code is None:
            if self._stop_deadline is not None and time.monotonic() >= self._stop_deadline:
                # Último recurso, somente para o processo criado por este controlador.
                self.process.kill()
                self._killed = True
                self._log("warn", "O bot não respondeu em 10 s; processo encerrado à força.")
                self._stop_deadline = time.monotonic() + 10
            return self.state
        if self._stop_deadline is not None or code == 0:
            self._set_state("stopped")
            self._log("ok", "Bot desligado.")
        elif self.state not in ERROR_STATES:
            self._set_state("error")
        for stream in (self.process.stdin, self.process.stdout):
            if stream is not None:
                stream.close()
        self.process = None
        self._stop_deadline = None
        return self.state
