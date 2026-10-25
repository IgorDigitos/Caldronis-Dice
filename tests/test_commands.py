import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord import app_commands

from bot import CaldronisClient
from commands.common import actor_from
from config import Settings
from profiles.service import ProfileError


def interaction(*, guild_id=1, user_id=10, owner_id=11, roles=(), manage=False):
    user = MagicMock(spec=discord.Member)
    user.id = user_id
    user.roles = [SimpleNamespace(id=role) for role in roles]
    user.guild_permissions = discord.Permissions(manage_guild=manage)
    return SimpleNamespace(
        guild=SimpleNamespace(id=guild_id, owner_id=owner_id),
        user=user,
        response=SimpleNamespace(defer=AsyncMock(), is_done=lambda: True),
        followup=SimpleNamespace(send=AsyncMock()),
    )


def test_registered_commands_and_intents(tmp_path):
    client = CaldronisClient(Settings("unused", database_path=tmp_path / "db"))
    assert {command.qualified_name for command in client.tree.walk_commands()} == {
        "perfil",
        "atributo",
        "atributo definir",
        "atributo remover",
        "mestre",
        "mestre definir",
        "mestre remover",
        "config",
        "config mestre",
    }
    assert client.intents.message_content
    assert client.intents.guild_messages
    assert not client.intents.members
    assert not client.intents.presences


def test_slash_callbacks_and_backend_authorization(tmp_path):
    async def scenario():
        client = CaldronisClient(Settings("unused", database_path=tmp_path / "db"))
        await client.repository.initialize()
        own = client.tree.get_command("atributo")
        master = client.tree.get_command("mestre")
        config = client.tree.get_command("config")
        actor = interaction()
        await own.get_command("definir").callback(own, actor, "for", 8)
        assert await client.repository.attributes(1, 10) == {"FOR": 8}
        assert actor.followup.send.await_args.kwargs["ephemeral"]
        with pytest.raises(ProfileError):
            await master.get_command("definir").callback(
                master, actor, SimpleNamespace(id=20), "FOR", 9
            )
        role = SimpleNamespace(id=99, guild=SimpleNamespace(id=1), managed=False)
        with pytest.raises(ProfileError):
            await config.get_command("mestre").callback(config, actor, role)
        admin = interaction(manage=True)
        await config.get_command("mestre").callback(config, admin, role)
        gm = interaction(roles=[99])
        await master.get_command("definir").callback(master, gm, SimpleNamespace(id=20), "CON", -3)
        assert await client.repository.attributes(1, 20) == {"CON": -3}
        await master.get_command("remover").callback(master, gm, SimpleNamespace(id=20), "CON")
        await own.get_command("remover").callback(own, actor, "FOR")
        profile = client.tree.get_command("perfil")
        await profile.callback(actor)
        assert "ainda não tem" in actor.followup.send.await_args.args[0]
        for bad_role in [
            SimpleNamespace(id=1, guild=SimpleNamespace(id=1), managed=False),
            SimpleNamespace(id=99, guild=SimpleNamespace(id=2), managed=False),
            SimpleNamespace(id=99, guild=SimpleNamespace(id=1), managed=True),
        ]:
            with pytest.raises(ProfileError):
                await config.get_command("mestre").callback(config, admin, bad_role)

    asyncio.run(scenario())


def test_dm_backend_rejection():
    with pytest.raises(ProfileError):
        actor_from(SimpleNamespace(guild=None))


@pytest.mark.parametrize("development", [True, False])
def test_startup_sync_without_network(tmp_path, development):
    async def scenario():
        client = CaldronisClient(Settings("unused", 123 if development else None, tmp_path / "db"))
        client.tree.sync = AsyncMock()
        await client.setup_hook()
        if development:
            assert client.tree.sync.await_args.kwargs["guild"].id == 123
            assert len(client.tree.get_commands(guild=discord.Object(id=123))) == 4
        else:
            client.tree.sync.assert_awaited_once_with()

    asyncio.run(scenario())


def test_command_error_private_and_sanitized(tmp_path):
    async def scenario():
        client = CaldronisClient(Settings("unused", database_path=tmp_path / "db"))
        actor = interaction()
        error = app_commands.CommandInvokeError(MagicMock(), RuntimeError("sensitive payload"))
        await client.tree.on_error(actor, error)
        assert actor.followup.send.await_args.kwargs["ephemeral"]
        assert "sensitive" not in actor.followup.send.await_args.args[0]

    asyncio.run(scenario())
