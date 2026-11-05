"""Processo sem janela do bot; estados seguros via stdout e parada via stdin."""

import asyncio
import logging
import sqlite3
import sys
import threading

import discord

from bot import CaldronisClient
from config import ROOT, Settings
from runtime_lock import AlreadyRunningError, InstanceLock


def emit(state: str):
    try:
        print("STATE:" + state, flush=True)
    except (OSError, ValueError):
        pass


class ManagedClient(CaldronisClient):
    async def on_ready(self):
        await super().on_ready()
        emit("online")

    async def on_disconnect(self):
        if not self.is_closed():
            emit("reconnecting")


async def serve(client, control_stream):
    loop = asyncio.get_running_loop()
    task = asyncio.current_task()

    def listen_for_stop():
        try:
            for line in control_stream:
                if line.strip() == "STOP":
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
            pass


def main() -> int:
    logging.getLogger("discord").setLevel(logging.CRITICAL)
    try:
        with InstanceLock(ROOT / "data" / ".bot.lock"):
            try:
                settings = Settings.from_env()
            except ValueError:
                emit("missing_config")
                return 1
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
