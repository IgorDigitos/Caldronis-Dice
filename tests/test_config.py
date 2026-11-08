import pytest

from config import Settings


def test_missing_token(monkeypatch):
    monkeypatch.setattr("config.load_dotenv", lambda path: None)
    monkeypatch.delenv("DISCORD_TOKEN", raising=False)
    with pytest.raises(ValueError, match="DISCORD_TOKEN"):
        Settings.from_env()


@pytest.mark.parametrize("guild", ["abc", "-1", "0", "１２３"])
def test_bad_guild(monkeypatch, guild):
    monkeypatch.setattr("config.load_dotenv", lambda path: None)
    monkeypatch.setenv("DISCORD_TOKEN", "fake-secret")
    monkeypatch.setenv("DEV_GUILD_ID", guild)
    with pytest.raises(ValueError, match="DEV_GUILD_ID"):
        Settings.from_env()


def test_config_no_secret_in_repr(monkeypatch):
    monkeypatch.setattr("config.load_dotenv", lambda path: None)
    monkeypatch.setenv("DISCORD_TOKEN", "fake-secret")
    monkeypatch.setenv("DEV_GUILD_ID", "123")
    monkeypatch.setenv("DATABASE_PATH", "data/test.sqlite3")
    config = Settings.from_env()
    assert config.dev_guild_id == 123
    assert config.database_path.is_absolute()
    assert "fake-secret" not in repr(config)


def _env_ponte(monkeypatch, **valores):
    monkeypatch.setattr("config.load_dotenv", lambda path: None)
    monkeypatch.setenv("DISCORD_TOKEN", "fake-secret")
    for nome in ("FIREBASE_CREDENCIAL", "WEBHOOK_MESA", "WEBHOOK_MESTRE", "DEV_GUILD_ID"):
        monkeypatch.delenv(nome, raising=False)
    for nome, valor in valores.items():
        monkeypatch.setenv(nome, valor)


def test_ponte_desligada_por_padrao(monkeypatch):
    _env_ponte(monkeypatch)
    config = Settings.from_env()
    assert config.firebase_credencial is None
    assert config.webhook_mesa is None


def test_ponte_configurada_sem_vazar_webhook(monkeypatch):
    url = "https://discord.com/api/webhooks/123/segredo-do-webhook"
    _env_ponte(
        monkeypatch,
        FIREBASE_CREDENCIAL="data/conta.json",
        WEBHOOK_MESA=url,
        WEBHOOK_MESTRE="https://ptb.discord.com/api/webhooks/9/outro_segredo",
    )
    config = Settings.from_env()
    assert config.firebase_credencial.is_absolute()
    assert config.webhook_mesa == url
    assert "segredo" not in repr(config)


@pytest.mark.parametrize(
    "url", ["http://discord.com/api/webhooks/1/a", "https://evil.com/api/webhooks/1/a"]
)
def test_webhook_invalido(monkeypatch, url):
    _env_ponte(monkeypatch, WEBHOOK_MESA=url)
    with pytest.raises(ValueError, match="WEBHOOK_MESA"):
        Settings.from_env()
