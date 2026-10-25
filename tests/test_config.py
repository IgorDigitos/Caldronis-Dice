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
