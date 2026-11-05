import logging
import sqlite3
import sys

import discord

from commands.administration import Configuration, Master
from commands.attributes import Attributes
from commands.common import CommandTree
from commands.profiles import register
from config import ROOT, Settings
from message_handler import MessageHandler
from profiles.repository import Repository
from profiles.service import ProfileService
from runtime_lock import AlreadyRunningError, InstanceLock

logger = logging.getLogger(__name__)


class CaldronisClient(discord.Client):
    def __init__(self, settings: Settings):
        intents = discord.Intents.none()
        intents.guilds = True
        intents.guild_messages = True
        intents.message_content = True
        super().__init__(intents=intents, allowed_mentions=discord.AllowedMentions.none())
        self.settings = settings
        self.repository = Repository(settings.database_path)
        service = ProfileService(self.repository)
        self.handler = MessageHandler(self.repository, self.report)
        self.tree = CommandTree(self)
        register(self.tree, service)
        for group in (Attributes(service), Master(service), Configuration(service)):
            self.tree.add_command(group)

    def report(self, code: str, argument: str | int | None = None):
        """Atividade operacional sem conteúdo do chat; o painel desktop a exibe."""

    async def setup_hook(self):
        await self.repository.initialize()
        self.report("database_ready")
        if self.settings.dev_guild_id:
            guild = discord.Object(id=self.settings.dev_guild_id)
            self.tree.copy_global_to(guild=guild)
            self.report("sync_guild")
            synced = await self.tree.sync(guild=guild)
        else:
            self.report("sync_global")
            synced = await self.tree.sync()
        self.report("synced", len(synced))
        logger.info("Comandos sincronizados.")

    async def on_ready(self):
        self.report("ready", len(self.guilds))
        logger.info("Caldronis Dice conectado.")

    async def on_resumed(self):
        self.report("resumed")

    async def on_guild_join(self, guild: discord.Guild):
        self.report("guild_join")

    async def on_guild_remove(self, guild: discord.Guild):
        self.report("guild_remove")

    async def on_app_command_completion(self, interaction: discord.Interaction, command):
        self.report("command", command.qualified_name)

    async def on_message(self, message: discord.Message):
        await self.handler.handle(message)

    async def on_error(self, event_method, *args, **kwargs):
        # O padrão da biblioteca pode incluir repr da mensagem; registrar só a classe do erro.
        error = sys.exc_info()[0]
        logger.error(
            "Falha inesperada em evento do Discord (%s); conteúdo omitido.",
            error.__name__ if error else "desconhecida",
        )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    # Evitar logs internos verbosos com payloads HTTP/Gateway.
    logging.getLogger("discord").setLevel(logging.WARNING)
    try:
        settings = Settings.from_env()
        with InstanceLock(ROOT / "data" / ".bot.lock"):
            CaldronisClient(settings).run(settings.token, log_handler=None)
    except AlreadyRunningError:
        logger.error("O bot já está aberto para este projeto. Encerre a outra instância.")
        return 1
    except ValueError as exc:
        logger.error("%s", exc)
        return 1
    except (discord.DiscordException, sqlite3.Error, OSError):
        logger.error("Falha ao iniciar. Confira token local, intents, rede e acesso ao banco.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
