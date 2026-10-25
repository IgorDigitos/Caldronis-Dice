import re
from dataclasses import dataclass

from profiles.repository import Repository


class ProfileError(ValueError):
    """Falha de validação ou autorização com texto seguro para o usuário."""


@dataclass(frozen=True)
class Actor:
    guild_id: int
    user_id: int
    role_ids: frozenset[int] = frozenset()
    is_owner: bool = False
    can_manage_guild: bool = False


def normalize_name(name: str) -> str:
    name = name.strip().upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,31}", name, re.ASCII):
        raise ProfileError(
            "Nome: 1 a 32 caracteres, começando por letra A-Z; use letras, números e _."
        )
    if re.fullmatch(r"D[0-9]+", name):
        raise ProfileError("Nomes como D20 são reservados para dados. Use outro nome.")
    return name


class ProfileService:
    def __init__(self, repository: Repository):
        self.repository = repository

    async def authorize_edit(self, actor: Actor, target_id: int):
        if actor.user_id == target_id:
            return
        role = await self.repository.master_role(actor.guild_id)
        if role is None:
            raise ProfileError(
                "Cargo de mestre não configurado. Peça ao administrador: /config mestre."
            )
        if role not in actor.role_ids:
            raise ProfileError(
                "Você precisa do cargo de mestre configurado para editar outro jogador."
            )

    async def define(self, actor: Actor, target_id: int, name: str, value: int) -> str:
        await self.authorize_edit(actor, target_id)
        name = normalize_name(name)
        if type(value) is not int or not -1_000_000_000 <= value <= 1_000_000_000:
            raise ProfileError("Valor deve ser inteiro entre -1.000.000.000 e 1.000.000.000.")
        try:
            await self.repository.set_attribute(actor.guild_id, target_id, name, value)
        except ValueError as exc:
            raise ProfileError(str(exc)) from exc
        return name

    async def remove(self, actor: Actor, target_id: int, name: str):
        await self.authorize_edit(actor, target_id)
        if not await self.repository.remove_attribute(
            actor.guild_id, target_id, normalize_name(name)
        ):
            raise ProfileError("Atributo não cadastrado nesse perfil.")

    async def configure_master(self, actor: Actor, role_id: int):
        if not (actor.is_owner or actor.can_manage_guild):
            raise ProfileError(
                "Somente o dono ou quem tem Gerenciar Servidor pode configurar o mestre."
            )
        if role_id == actor.guild_id:
            raise ProfileError("O cargo @everyone não pode ser mestre.")
        await self.repository.set_master_role(actor.guild_id, role_id)
