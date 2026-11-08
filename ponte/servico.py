"""Ponte com o Caldron Sheets: rola os pedidos que chegam do app e posta no Discord.

O app grava um pedido no Firestore (coleção `mesa` ou `mesaMestre`, `estado: 'pendente'`). Aqui:
1. confere se o pedido não é velho (ficou na fila sem internet, ou o bot estava desligado);
2. reserva o pedido numa transação (nunca rola duas vezes);
3. lê os atributos ATUAIS direto da ficha (o app não manda valores; ninguém inventa FOR 50);
4. rola com o mesmo motor do Discord e grava o resultado ANTES de postar;
5. posta pelo webhook do canal (mesa ou Mestre) com o nome do personagem.

Esta parte não conhece Firestore nem Discord: recebe um `Armazem` e uma função `enviar`, para os
testes rodarem sem rede.
"""

import asyncio
import logging
import secrets
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Protocol

from dice.models import DiceError
from dice.parser import parse
from dice.roller import roll_many
from message_handler import format_batch

logger = logging.getLogger(__name__)

Canal = Literal["mesa", "mestre"]

ATRIBUTOS = ("FOR", "DES", "CON", "INT", "SAB", "CAR")

# Pedido que levou mais que isto entre o aparelho e o servidor ficou parado sem internet.
ATRASO_MAXIMO_ENVIO = 60
# Pedido esperando mais que isto no servidor: o bot estava desligado.
ESPERA_MAXIMA = 5 * 60
# Limite por pessoa, contra spam.
ROLAGENS_POR_JANELA = 6
JANELA_SEGUNDOS = 30


class Armazem(Protocol):
    def reservar(self, canal: Canal, doc_id: str) -> dict[str, Any] | None:
        """Troca 'pendente' por 'rolando' numa transação; None se outro já pegou."""

    def ficha(self, ficha_id: str) -> dict[str, Any] | None: ...

    def concluir(self, canal: Canal, doc_id: str, campos: dict[str, Any]) -> None: ...


Enviar = Callable[[Canal, str, tuple[str, ...]], Awaitable[bool]]


def atributos_da_ficha(ficha: Mapping[str, Any] | None) -> dict[str, int]:
    """Atributo atual = base + extra − perda (igual ao app), mais o NIVEL."""
    if not ficha:
        return {}
    saida: dict[str, int] = {}
    atributos = ficha.get("atributos") or {}
    for sigla in ATRIBUTOS:
        valor = atributos.get(sigla)
        if isinstance(valor, Mapping):
            atual = valor.get("base", 0) + valor.get("extra", 0) - valor.get("perda", 0)
            saida[sigla] = int(round(atual))
    if isinstance(ficha.get("nivel"), int | float):
        saida["NIVEL"] = int(ficha["nivel"])
    return saida


def _segundos(valor: Any) -> float | None:
    """Timestamp do Firestore (datetime) ou milissegundos do app → segundos desde 1970."""
    if isinstance(valor, datetime):
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=timezone.utc)
        return valor.timestamp()
    if isinstance(valor, int | float):
        return valor / 1000
    return None


@dataclass
class PonteMesa:
    armazem: Armazem
    enviar: Enviar
    agora: Callable[[], float] = time.time
    random_source: Callable[[int], int] = secrets.randbelow
    report: Callable[..., None] = lambda code, argument=None: None
    _recentes: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))

    def motivo_expirada(self, pedido: Mapping[str, Any]) -> str | None:
        criado = _segundos(pedido.get("criadoEm"))
        recebido = _segundos(pedido.get("recebidoEm"))
        if criado is not None and recebido is not None and recebido - criado > ATRASO_MAXIMO_ENVIO:
            return "Enviada sem internet: não foi rolada."
        if recebido is not None and self.agora() - recebido > ESPERA_MAXIMA:
            return "O bot estava desligado: não foi rolada."
        return None

    def _excedeu_limite(self, autor: str) -> bool:
        agora = self.agora()
        fila = self._recentes[autor]
        while fila and agora - fila[0] > JANELA_SEGUNDOS:
            fila.popleft()
        if len(fila) >= ROLAGENS_POR_JANELA:
            return True
        fila.append(agora)
        return False

    async def processar(self, canal: Canal, doc_id: str, pedido: Mapping[str, Any]) -> None:
        """Chamado para cada pedido 'pendente' que aparece. Nunca lança."""
        try:
            await self._processar(canal, doc_id, pedido)
        except Exception:  # noqa: BLE001 - um pedido ruim não pode derrubar a ponte
            logger.exception("Falha inesperada ao processar pedido da mesa.")
            self.report("mesa_falha")

    async def _processar(self, canal: Canal, doc_id: str, pedido: Mapping[str, Any]) -> None:
        if pedido.get("tipo") != "rolagem" or pedido.get("estado") != "pendente":
            return
        motivo = self.motivo_expirada(pedido)
        # O Firestore é síncrono (rede): roda fora do event loop do Discord.
        reservado = await asyncio.to_thread(self.armazem.reservar, canal, doc_id)
        if reservado is None:
            return
        if motivo:
            await asyncio.to_thread(
                self.armazem.concluir, canal, doc_id, {"estado": "expirada", "erro": motivo}
            )
            self.report("mesa_expirada")
            return
        if self._excedeu_limite(str(reservado.get("autorUid", ""))):
            await asyncio.to_thread(
                self.armazem.concluir,
                canal,
                doc_id,
                {"estado": "erro", "erro": "Muitas rolagens seguidas. Espere alguns segundos."},
            )
            self.report("mesa_limite")
            return
        try:
            expressao = parse(str(reservado.get("texto", "")))
            if expressao is None:
                raise DiceError("A mensagem não começa com uma rolagem.")
            ficha_id = reservado.get("fichaId")
            atributos = (
                atributos_da_ficha(await asyncio.to_thread(self.armazem.ficha, ficha_id))
                if expressao.attributes and isinstance(ficha_id, str)
                else {}
            )
            resultados = roll_many(expressao, atributos, self.random_source)
        except DiceError as exc:
            await asyncio.to_thread(
                self.armazem.concluir, canal, doc_id, {"estado": "erro", "erro": str(exc)}
            )
            self.report("roll_rejected")
            return

        conteudo = format_batch(resultados)
        # Grava ANTES de postar: se o Discord falhar, a rolagem continua valendo no app.
        await asyncio.to_thread(
            self.armazem.concluir,
            canal,
            doc_id,
            {
                "estado": "feita",
                "resultado": list(conteudo),
                "totais": [r.total for r in resultados],
                "roladaEm": int(self.agora() * 1000),
            },
        )
        self.report("mesa_roll")
        nome = str(reservado.get("nome") or "Mestre")
        enviado = await self.enviar(canal, nome, conteudo)
        await asyncio.to_thread(
            self.armazem.concluir, canal, doc_id, {"discord": "enviado" if enviado else "falhou"}
        )
        if not enviado:
            self.report("mesa_discord")
