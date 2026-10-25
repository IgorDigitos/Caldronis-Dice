import logging
import re
import sqlite3

import discord

from dice.models import DiceError, RollResult
from dice.parser import parse
from dice.roller import roll_many
from profiles.repository import Repository

logger = logging.getLogger(__name__)


def safe_text(text: str) -> str:
    return discord.utils.escape_markdown(discord.utils.escape_mentions(text))


def text_length(text: str) -> int:
    # Uma margem abaixo de 2000, contando também pares UTF-16 de emojis.
    return len(text.encode("utf-16-le")) // 2


def _result_parts(result: RollResult, total_width: int | None = None) -> list[str]:
    tokens = re.findall(
        r"[0-9]*d[0-9]+!|[0-9]+d[0-9]+|[A-Za-z][A-Za-z0-9_]*|[0-9]+",
        re.split(r">>|<<", result.expression.original, maxsplit=1)[0],
        flags=re.IGNORECASE | re.ASCII,
    )
    # Espaços inseparáveis preservam a margem dentro do código inline no Discord.
    number = str(result.total)
    padded = number.center(total_width or len(number), "\u00a0")
    parts = [f"`\u00a0{padded}\u00a0` ⟵"]
    for index, (term, detail, token) in enumerate(
        zip(result.expression.terms, result.details, tokens, strict=True)
    ):
        prefix = " " if index == 0 else (" - " if term.sign < 0 else " + ")
        if term.kind == "dice":
            ordered = sorted(detail.values, reverse=True)
            values = ", ".join(
                f"**{value}**" if value in (1, term.value) else str(value) for value in ordered
            )
            if result.expression.repeat_count is not None:
                token = detail.label
            parts.append(f"{prefix}[{values}] {token}")
        else:
            parts.append(f"{prefix}{token}")
    if result.expression.count_target is not None:
        parts.append(f" {result.expression.count_operator} {result.expression.count_target}")
    return parts


def _notes(result: RollResult) -> list[str]:
    parts = []
    attributes = {
        str(term.value): detail.values[0]
        for term, detail in zip(result.expression.terms, result.details, strict=True)
        if term.kind == "attribute"
    }
    for index, (name, value) in enumerate(attributes.items()):
        separator = "\n" if index == 0 else " · "
        parts.append(f"{separator}{name}={value:+d}")
    if result.expression.comment:
        # Escapar cada trecho separadamente mantém Markdown e menções seguros na divisão.
        comment = " ".join(result.expression.comment.splitlines())
        for start in range(0, len(comment), 400):
            parts.append("\n> " + safe_text(comment[start : start + 400]))
    return parts


def _pack(parts: list[str]) -> tuple[str, ...]:
    messages = [""]
    for part in parts:
        if text_length(messages[-1] + part) > 1900:
            messages.append("↳ ")
        messages[-1] += part
    return tuple(message.rstrip() for message in messages)


def format_result(result: RollResult) -> tuple[str, ...]:
    """Resposta compacta; divide por termos, sem truncar ou sortear novamente."""
    return _pack(_result_parts(result) + _notes(result))


def format_batch(results: tuple[RollResult, ...]) -> tuple[str, ...]:
    """Um total por linha; atributos e comentário compartilhados aparecem só no final."""
    parts = []
    total_width = max(len(str(result.total)) for result in results)
    for index, result in enumerate(results):
        if index:
            parts.append("\n")
        parts.extend(_result_parts(result, total_width))
    parts.extend(_notes(results[0]))
    return _pack(parts)


class MessageHandler:
    def __init__(self, repository: Repository):
        self.repository = repository

    async def handle(self, message):
        if message.guild is None or message.author.bot or message.webhook_id is not None:
            return
        try:
            expression = parse(message.content)
            if expression is None:
                return
            attributes = (
                await self.repository.attributes(message.guild.id, message.author.id)
                if expression.attributes
                else {}
            )
            results = roll_many(expression, attributes)
            for content in format_batch(results):
                if not await self._reply(message, content=content):
                    break
        except DiceError as exc:
            # Mensagens de canal não podem ser ephemeral. Não ecoar conteúdo do chat.
            await self._reply(message, content=f"Não foi possível rolar: {exc}", delete_after=15)
        except (sqlite3.Error, OSError):
            logger.warning("Falha de armazenamento ao processar rolagem.")
            await self._reply(
                message,
                content="Banco indisponível. Tente novamente em instantes.",
                delete_after=15,
            )

    async def _reply(self, message, **kwargs):
        try:
            await message.reply(
                **kwargs, mention_author=False, allowed_mentions=discord.AllowedMentions.none()
            )
            return True
        except (discord.HTTPException, OSError):
            # Não repetir a rolagem em outro envio após erro de rede ambíguo.
            logger.warning("Não foi possível enviar uma resposta de rolagem ao Discord.")
            return False
