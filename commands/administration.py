import discord
from discord import app_commands

from commands.common import actor_from, private_response
from profiles.service import ProfileError, ProfileService


@app_commands.guild_only()
class Master(app_commands.Group):
    def __init__(self, service: ProfileService):
        super().__init__(name="mestre", description="Edita atributos de jogadores como mestre.")
        self.service = service

    @app_commands.command(name="definir", description="Define atributo de um jogador.")
    async def define(
        self, interaction: discord.Interaction, jogador: discord.Member, nome: str, valor: int
    ):
        actor = actor_from(interaction)
        await interaction.response.defer(ephemeral=True)
        name = await self.service.define(actor, jogador.id, nome, valor)
        await private_response(interaction, f"{name} do jogador definido como {valor:+d}.")

    @app_commands.command(name="remover", description="Remove atributo de um jogador.")
    async def remove(self, interaction: discord.Interaction, jogador: discord.Member, nome: str):
        actor = actor_from(interaction)
        await interaction.response.defer(ephemeral=True)
        await self.service.remove(actor, jogador.id, nome)
        await private_response(interaction, "Atributo do jogador removido.")


@app_commands.guild_only()
class Configuration(app_commands.Group):
    def __init__(self, service: ProfileService):
        super().__init__(
            name="config",
            description="Configura o bot neste servidor.",
            default_permissions=discord.Permissions(manage_guild=True),
        )
        self.service = service

    @app_commands.command(name="mestre", description="Configura o cargo autorizado como mestre.")
    async def master(self, interaction: discord.Interaction, cargo: discord.Role):
        actor = actor_from(interaction)
        if cargo.guild.id != actor.guild_id or cargo.managed:
            raise ProfileError("Escolha um cargo comum deste servidor.")
        await interaction.response.defer(ephemeral=True)
        await self.service.configure_master(actor, cargo.id)
        await private_response(interaction, "Cargo de mestre configurado.")
