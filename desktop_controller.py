"""Controle do processo criado pelo painel; não depende de Tkinter ou Discord."""

import os
import queue
import subprocess
import threading
import time
from pathlib import Path

STATES = {
    "starting": "Conectando ao Discord…",
    "online": "Ligado e conectado ao Discord",
    "reconnecting": "Reconectando ao Discord…",
    "stopping": "Desligando…",
    "stopped": "Desligado",
    "missing_config": "Confira DISCORD_TOKEN e DEV_GUILD_ID no arquivo .env do projeto.",
    "already_running": "O bot já está aberto. Desligue a outra instância antes de ligar aqui.",
    "connection_error": "Falha de conexão. Confira token, intents, rede e acesso ao banco.",
    "error": "O bot não conseguiu iniciar. Confira a configuração do projeto.",
}


class BotController:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.process = None
        self.state = "stopped"
        self.events = queue.SimpleQueue()
        self._stop_deadline = None

    @property
    def running(self):
        return self.process is not None and self.process.poll() is None

    def start(self):
        self.poll()
        if self.running:
            return
        executable = self.project_dir / ".venv" / "Scripts" / "python.exe"
        worker = self.project_dir / "desktop_worker.py"
        if not executable.is_file() or not worker.is_file():
            raise FileNotFoundError(
                "Ambiente Python ou arquivos do bot ausentes na pasta do projeto."
            )
        self.events = queue.SimpleQueue()
        environment = os.environ.copy()
        environment["PYTHONIOENCODING"] = "utf-8"
        environment["PYTHONUNBUFFERED"] = "1"
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
        self._stop_deadline = None
        threading.Thread(
            target=self._read_events, args=(self.process, self.events), daemon=True
        ).start()

    @staticmethod
    def _read_events(process, events):
        # Somente estados conhecidos entram no painel; não ecoar logs/payloads do Discord.
        try:
            for line in process.stdout:
                state = line.strip()
                if state.startswith("STATE:") and state[6:] in STATES:
                    events.put(state[6:])
        except (OSError, ValueError):
            pass

    def stop(self):
        if not self.running or self._stop_deadline is not None:
            return
        self.state = "stopping"
        self._stop_deadline = time.monotonic() + 10
        try:
            self.process.stdin.write("STOP\n")
            self.process.stdin.flush()
        except (OSError, ValueError):
            pass

    def poll(self):
        while not self.events.empty():
            state = self.events.get()
            if self._stop_deadline is None:
                self.state = state
        if self.process is None:
            return self.state
        code = self.process.poll()
        if code is None:
            if self._stop_deadline is not None and time.monotonic() >= self._stop_deadline:
                # Último recurso, somente para o processo criado por este controlador.
                self.process.kill()
                self._stop_deadline = time.monotonic() + 10
            return self.state
        if self._stop_deadline is not None or code == 0:
            self.state = "stopped"
        elif self.state not in {"missing_config", "already_running", "connection_error", "error"}:
            self.state = "error"
        for stream in (self.process.stdin, self.process.stdout):
            if stream is not None:
                stream.close()
        self.process = None
        self._stop_deadline = None
        return self.state
