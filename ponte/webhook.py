"""Posta as rolagens do app no Discord pelo webhook do canal, com o nome do personagem."""

import asyncio
import logging
import re

import aiohttp
import discord

logger = logging.getLogger(__name__)

NOME_PADRAO = "Caldron Sheets"
# O Discord recusa nomes de webhook com estes trechos.
PROIBIDO_NO_NOME = re.compile(r"discord|clyde|```|[@#:]", re.IGNORECASE)


def nome_seguro(nome: str) -> str:
    limpo = PROIBIDO_NO_NOME.sub("", nome).strip()[:80]
    return limpo or NOME_PADRAO


class EnviadorWebhook:
    """Um webhook por canal ('mesa' e 'mestre'). Tenta de novo só quando o Discord RECUSOU
    claramente (429 ou 5xx); erro de rede ambíguo não repete, para não postar duas vezes."""

    def __init__(self, urls: dict[str, str | None], session: aiohttp.ClientSession, espera=2.0):
        self.urls = urls
        self.session = session
        self.espera = espera

    async def __call__(self, canal: str, nome: str, conteudos: tuple[str, ...]) -> bool:
        url = self.urls.get(canal)
        if not url:
            return False
        webhook = discord.Webhook.from_url(url, session=self.session)
        for conteudo in conteudos:
            if not await self._enviar_um(webhook, nome_seguro(nome), conteudo):
                return False
        return True

    async def _enviar_um(self, webhook, nome: str, conteudo: str) -> bool:
        for tentativa in range(2):
            try:
                await webhook.send(
                    content=conteudo,
                    username=nome,
                    allowed_mentions=discord.AllowedMentions.none(),
                    wait=True,
                )
                return True
            except discord.HTTPException as exc:
                if tentativa == 0 and (exc.status == 429 or exc.status >= 500):
                    await asyncio.sleep(self.espera)
                    continue
                logger.warning("Webhook do Discord recusou a rolagem (HTTP %s).", exc.status)
                return False
            except (aiohttp.ClientError, OSError, TimeoutError):
                logger.warning("Não foi possível falar com o webhook do Discord.")
                return False
        return False
