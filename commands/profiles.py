import discord
from discord import app_commands

from commands.common import actor_from, private_response
from profiles.service import ProfileService


def register(tree: app_commands.CommandTree, service: ProfileService):
    @tree.command(name="perfil", description="Mostra seus atributos neste servidor.")
    @app_commands.guild_only()
    async def profile(interaction: discord.Interaction):
        actor = actor_from(interaction)
        await interaction.response.defer(ephemeral=True)
        attributes = await service.repository.attributes(actor.guild_id, actor.user_id)
        text = "Seu perfil:\n" + "\n".join(
            f"`{name}`: {value:+d}" for name, value in attributes.items()
        )
        if not attributes:
            text = "Você ainda não tem atributos. Use /atributo definir."
        await private_response(interaction, text)
