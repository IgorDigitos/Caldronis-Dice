import logging
import sqlite3

import discord

from commands.administration import Configuration, Master
from commands.attributes import Attributes
from commands.common import CommandTree
from commands.profiles import register
from config import Settings
from message_handler import MessageHandler
from profiles.repository import Repository
from profiles.service import ProfileService

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
        self.handler = MessageHandler(self.repository)
        self.tree = CommandTree(self)
        register(self.tree, service)
        for group in (Attributes(service), Master(service), Configuration(service)):
            self.tree.add_command(group)

    async def setup_hook(self):
        await self.repository.initialize()
        if self.settings.dev_guild_id:
            guild = discord.Object(id=self.settings.dev_guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()
        logger.info("Comandos sincronizados.")

    async def on_ready(self):
        logger.info("Caldronis Dice conectado.")

    async def on_message(self, message: discord.Message):
        await self.handler.handle(message)

    async def on_error(self, event_method, *args, **kwargs):
        # O padrão da biblioteca pode incluir repr da mensagem; não usá-lo.
        logger.error("Falha inesperada em evento do Discord; conteúdo omitido.")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    # Evitar logs internos verbosos com payloads HTTP/Gateway.
    logging.getLogger("discord").setLevel(logging.WARNING)
    try:
        settings = Settings.from_env()
        CaldronisClient(settings).run(settings.token, log_handler=None)
    except ValueError as exc:
        logger.error("%s", exc)
        return 1
    except (discord.DiscordException, sqlite3.Error, OSError):
        logger.error("Falha ao iniciar. Confira token local, intents, rede e acesso ao banco.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
