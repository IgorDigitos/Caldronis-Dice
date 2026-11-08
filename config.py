import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent

URL_WEBHOOK = re.compile(
    r"https://(?:(?:ptb|canary)\.)?discord(?:app)?\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+",
    re.ASCII,
)


@dataclass(frozen=True)
class Settings:
    token: str = field(repr=False)
    dev_guild_id: int | None = None
    database_path: Path = ROOT / "data" / "caldronis.sqlite3"
    # Ponte com o app Caldron Sheets (opcional): conta de serviço do Firebase e webhooks.
    firebase_credencial: Path | None = None
    firebase_projeto: str | None = None
    webhook_mesa: str | None = field(default=None, repr=False)
    webhook_mestre: str | None = field(default=None, repr=False)

    @classmethod
    def from_env(cls):
        load_dotenv(ROOT / ".env")
        token = os.getenv("DISCORD_TOKEN", "").strip()
        if not token:
            raise ValueError(
                "Preencha DISCORD_TOKEN no arquivo .env local. Não envie o token no chat."
            )
        guild = os.getenv("DEV_GUILD_ID", "").strip()
        if guild and (not guild.isascii() or not guild.isdigit() or int(guild) <= 0):
            raise ValueError("DEV_GUILD_ID deve ser o ID numérico positivo do servidor.")
        path = Path(os.getenv("DATABASE_PATH", "").strip() or "data/caldronis.sqlite3")
        credencial = os.getenv("FIREBASE_CREDENCIAL", "").strip()
        webhooks = {}
        for nome in ("WEBHOOK_MESA", "WEBHOOK_MESTRE"):
            url = os.getenv(nome, "").strip()
            if url and not URL_WEBHOOK.fullmatch(url):
                raise ValueError(f"{nome} não parece um link de webhook do Discord.")
            webhooks[nome] = url or None
        return cls(
            token,
            int(guild) if guild else None,
            ROOT / path,
            firebase_credencial=ROOT / credencial if credencial else None,
            firebase_projeto=os.getenv("FIREBASE_PROJETO", "").strip() or None,
            webhook_mesa=webhooks["WEBHOOK_MESA"],
            webhook_mestre=webhooks["WEBHOOK_MESTRE"],
        )
