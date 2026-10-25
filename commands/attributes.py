import discord
from discord import app_commands

from commands.common import actor_from, private_response
from profiles.service import ProfileService


@app_commands.guild_only()
class Attributes(app_commands.Group):
    def __init__(self, service: ProfileService):
        super().__init__(name="atributo", description="Gerencia seus atributos.")
        self.service = service

    @app_commands.command(name="definir", description="Cria ou atualiza um atributo seu.")
    async def define(self, interaction: discord.Interaction, nome: str, valor: int):
        actor = actor_from(interaction)
        await interaction.response.defer(ephemeral=True)
        name = await self.service.define(actor, actor.user_id, nome, valor)
        await private_response(interaction, f"{name} definido como {valor:+d}.")

    @app_commands.command(name="remover", description="Remove um atributo seu.")
    async def remove(self, interaction: discord.Interaction, nome: str):
        actor = actor_from(interaction)
        await interaction.response.defer(ephemeral=True)
        await self.service.remove(actor, actor.user_id, nome)
        await private_response(interaction, "Atributo removido.")
