import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Settings:
    token: str = field(repr=False)
    dev_guild_id: int | None = None
    database_path: Path = ROOT / "data" / "caldronis.sqlite3"

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
        return cls(token, int(guild) if guild else None, ROOT / path)
