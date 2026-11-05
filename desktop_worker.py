"""Processo sem janela do bot; estados e códigos de atividade via stdout, parada via stdin."""

import asyncio
import logging
import re
import sqlite3
import sys
import threading

import discord

from bot import CaldronisClient
from config import ROOT, Settings
from runtime_lock import AlreadyRunningError, InstanceLock

SAFE_ARGUMENT = re.compile(r"[a-z0-9][a-z0-9 _-]{0,39}", re.ASCII)


def _write(line: str):
    try:
        print(line, flush=True)
    except (OSError, ValueError):
        pass


def emit(state: str):
    _write("STATE:" + state)


def emit_log(code: str, argument: str | int | None = None):
    """Envia apenas um código conhecido e, no máximo, um argumento curto sem dados do chat."""
    if argument is None:
        _write("LOG:" + code)
        return
    text = str(argument).lower()
    if SAFE_ARGUMENT.fullmatch(text):
        _write(f"LOG:{code}:{text}")


class LibraryActivity(logging.Handler):
    """Traduz avisos da biblioteca em códigos fixos, sem formatar argumentos ou payloads."""

    def emit(self, record: logging.LogRecord):
        template = record.msg if isinstance(record.msg, str) else ""
        if "rate limit" in template.lower():
            emit_log("rate_limited")
        elif record.levelno >= logging.WARNING:
            emit_log("library_warning")


class ManagedClient(CaldronisClient):
    def report(self, code: str, argument: str | int | None = None):
        emit_log(code, argument)

    async def login(self, token: str):
        self.report("login")
        await super().login(token)

    async def connect(self, *, reconnect: bool = True):
        self.report("gateway")
        await super().connect(reconnect=reconnect)

    async def on_ready(self):
        await super().on_ready()
        emit("online")

    async def on_resumed(self):
        await super().on_resumed()
        emit("online")

    async def on_disconnect(self):
        if not self.is_closed():
            self.report("disconnected")
            emit("reconnecting")


async def serve(client, control_stream):
    loop = asyncio.get_running_loop()
    task = asyncio.current_task()

    def listen_for_stop():
        try:
            for line in control_stream:
                if line.strip() == "STOP":
                    emit_log("stop_received")
                    break
        finally:
            # EOF também encerra o bot se o painel for fechado abruptamente.
            try:
                loop.call_soon_threadsafe(task.cancel)
            except RuntimeError:
                pass

    async with client:
        threading.Thread(target=listen_for_stop, daemon=True).start()
        try:
            await client.start(client.settings.token)
        except asyncio.CancelledError:
            emit_log("closing")


def main() -> int:
    library = logging.getLogger("discord")
    library.setLevel(logging.WARNING)
    library.propagate = False
    library.addHandler(LibraryActivity())
    try:
        with InstanceLock(ROOT / "data" / ".bot.lock"):
            try:
                settings = Settings.from_env()
            except ValueError:
                emit("missing_config")
                return 1
            emit_log("config_loaded")
            emit("starting")
            asyncio.run(serve(ManagedClient(settings), sys.stdin))
    except AlreadyRunningError:
        emit("already_running")
        return 1
    except (discord.DiscordException, sqlite3.Error, OSError):
        emit("connection_error")
        return 1
    except Exception:
        emit("error")
        return 1
    emit("stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
