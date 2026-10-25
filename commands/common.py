import logging
import sqlite3

import discord
from discord import app_commands

from profiles.service import Actor, ProfileError

logger = logging.getLogger(__name__)


def actor_from(interaction: discord.Interaction) -> Actor:
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        raise ProfileError("Use este comando em um servidor.")
    user = interaction.user
    return Actor(
        interaction.guild.id,
        user.id,
        frozenset(role.id for role in user.roles),
        interaction.guild.owner_id == user.id,
        user.guild_permissions.manage_guild,
    )


async def private_response(interaction: discord.Interaction, text: str):
    if interaction.response.is_done():
        await interaction.followup.send(
            text, ephemeral=True, allowed_mentions=discord.AllowedMentions.none()
        )
    else:
        await interaction.response.send_message(
            text, ephemeral=True, allowed_mentions=discord.AllowedMentions.none()
        )


class CommandTree(app_commands.CommandTree):
    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        cause = getattr(error, "original", error)
        if isinstance(cause, ProfileError):
            text = str(cause)
        elif isinstance(cause, (sqlite3.Error, OSError)):
            text = "Banco ou conexão indisponível. Tente novamente em instantes."
        elif isinstance(cause, app_commands.CheckFailure):
            text = "Você não pode usar este comando neste contexto."
        else:
            text = "Não foi possível concluir o comando. Contate o responsável pelo bot."
        # Registrar apenas classe do erro; nunca token, argumentos ou conteúdo do chat.
        logger.warning("Comando não concluído (%s).", type(cause).__name__)
        try:
            await private_response(interaction, text)
        except (discord.HTTPException, OSError):
            logger.warning("Falha ao responder comando no Discord.")
