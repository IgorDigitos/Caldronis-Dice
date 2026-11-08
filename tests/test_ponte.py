import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest

from ponte.servico import (
    ATRASO_MAXIMO_ENVIO,
    ESPERA_MAXIMA,
    ROLAGENS_POR_JANELA,
    PonteMesa,
    atributos_da_ficha,
)
from ponte.webhook import EnviadorWebhook, nome_seguro

AGORA = 1_800_000_000.0
SKAR = {
    "nome": "Skar Lionet",
    "nivel": 2,
    "atributos": {
        "FOR": {"base": 8},
        "DES": {"base": 2, "extra": 1},
        "CON": {"base": 5, "perda": 2},
        "INT": {"base": 2},
        "SAB": {"base": 3},
        "CAR": {"base": 2},
    },
}


class ArmazemFalso:
    def __init__(self, pedidos=None, fichas=None):
        self.docs = {("mesa", k): dict(v) for k, v in (pedidos or {}).items()}
        self.fichas = fichas or {}
        self.escritas = []

    def reservar(self, canal, doc_id):
        dados = self.docs.get((canal, doc_id))
        if not dados or dados.get("estado") != "pendente":
            return None
        dados["estado"] = "rolando"
        return dict(dados)

    def ficha(self, ficha_id):
        return self.fichas.get(ficha_id)

    def concluir(self, canal, doc_id, campos):
        self.docs[(canal, doc_id)].update(campos)
        self.escritas.append(campos)


def pedido(texto="d30+FOR ataque", **extra):
    base = {
        "tipo": "rolagem",
        "estado": "pendente",
        "texto": texto,
        "autorUid": "u1",
        "fichaId": "skar",
        "nome": "Skar Lionet",
        "criadoEm": int(AGORA * 1000) - 500,
        "recebidoEm": datetime.fromtimestamp(AGORA - 0.2, tz=timezone.utc),
    }
    return {**base, **extra}


def montar(pedidos, enviado=True, sorteio=lambda lados: lados - 1):
    armazem = ArmazemFalso(pedidos, {"skar": SKAR})
    enviar = AsyncMock(return_value=enviado)
    relatos = []
    ponte = PonteMesa(
        armazem,
        enviar,
        agora=lambda: AGORA,
        random_source=sorteio,
        report=lambda code, argument=None: relatos.append(code),
    )
    return ponte, armazem, enviar, relatos


def processar(ponte, armazem, doc_id="p1", canal="mesa"):
    asyncio.run(ponte.processar(canal, doc_id, armazem.docs[(canal, doc_id)]))
    return armazem.docs[(canal, doc_id)]


def test_atributos_da_ficha_usa_valor_atual_e_nivel():
    assert atributos_da_ficha(SKAR) == {
        "FOR": 8,
        "DES": 3,
        "CON": 3,
        "INT": 2,
        "SAB": 3,
        "CAR": 2,
        "NIVEL": 2,
    }
    assert atributos_da_ficha(None) == {}


def test_rola_com_atributo_da_ficha_grava_e_posta_com_nome():
    ponte, armazem, enviar, relatos = montar({"p1": pedido()})
    doc = processar(ponte, armazem)
    assert doc["estado"] == "feita"
    assert doc["totais"] == [38]  # 30 (dado máximo) + FOR 8
    assert "FOR=+8" in doc["resultado"][-1]
    assert "ataque" in doc["resultado"][-1]
    assert doc["discord"] == "enviado"
    enviar.assert_awaited_once_with("mesa", "Skar Lionet", tuple(doc["resultado"]))
    assert relatos == ["mesa_roll"]
    # O resultado foi gravado ANTES de postar.
    assert armazem.escritas[0]["estado"] == "feita"
    assert armazem.escritas[1] == {"discord": "enviado"}


def test_atributo_que_a_ficha_nao_tem_vira_erro():
    ponte, armazem, enviar, _ = montar({"p1": pedido("d30+XYZ")})
    doc = processar(ponte, armazem)
    assert doc["estado"] == "erro"
    assert "XYZ" in doc["erro"]
    enviar.assert_not_awaited()


def test_mestre_sem_ficha_rola_so_dados():
    p = pedido("2d30+5", nome="Mestre")
    del p["fichaId"]
    ponte, armazem, _, _ = montar({"p1": p})
    assert processar(ponte, armazem)["totais"] == [65]


def test_canal_do_mestre_vai_para_o_webhook_secreto():
    ponte, armazem, enviar, _ = montar({})
    armazem.docs[("mestre", "s1")] = pedido("d30", nome="Mestre")
    asyncio.run(ponte.processar("mestre", "s1", armazem.docs[("mestre", "s1")]))
    assert enviar.await_args.args[0] == "mestre"


def test_discord_falhou_mas_rolagem_continua_salva():
    ponte, armazem, _, relatos = montar({"p1": pedido()}, enviado=False)
    doc = processar(ponte, armazem)
    assert doc["estado"] == "feita"
    assert doc["discord"] == "falhou"
    assert "mesa_discord" in relatos


def test_expressao_invalida_vira_erro():
    ponte, armazem, enviar, relatos = montar({"p1": pedido("d30 * 2")})
    doc = processar(ponte, armazem)
    assert doc["estado"] == "erro"
    assert "Operador" in doc["erro"]
    assert relatos == ["roll_rejected"]
    enviar.assert_not_awaited()


def test_texto_que_nao_e_rolagem_vira_erro():
    ponte, armazem, _, _ = montar({"p1": pedido("quero rolar d30")})
    assert processar(ponte, armazem)["estado"] == "erro"


@pytest.mark.parametrize(
    "extra, trecho",
    [
        ({"criadoEm": int((AGORA - ATRASO_MAXIMO_ENVIO - 5) * 1000)}, "sem internet"),
        (
            {
                "criadoEm": int((AGORA - ESPERA_MAXIMA - 10) * 1000),
                "recebidoEm": datetime.fromtimestamp(AGORA - ESPERA_MAXIMA - 10, tz=timezone.utc),
            },
            "desligado",
        ),
    ],
)
def test_pedido_velho_expira_sem_rolar(extra, trecho):
    ponte, armazem, enviar, _ = montar({"p1": pedido(**extra)})
    doc = processar(ponte, armazem)
    assert doc["estado"] == "expirada"
    assert trecho in doc["erro"]
    assert "resultado" not in doc
    enviar.assert_not_awaited()


def test_nao_rola_duas_vezes_nem_o_que_nao_e_pendente():
    ponte, armazem, enviar, _ = montar({"p1": pedido(), "p2": pedido(estado="feita")})
    processar(ponte, armazem)
    processar(ponte, armazem)  # mesmo pedido chegando de novo
    processar(ponte, armazem, "p2")
    assert enviar.await_count == 1


def test_limite_de_rolagens_por_pessoa():
    pedidos = {f"p{i}": pedido("d30") for i in range(ROLAGENS_POR_JANELA + 1)}
    ponte, armazem, _, relatos = montar(pedidos)
    for i in range(ROLAGENS_POR_JANELA + 1):
        processar(ponte, armazem, f"p{i}")
    ultimo = armazem.docs[("mesa", f"p{ROLAGENS_POR_JANELA}")]
    assert ultimo["estado"] == "erro"
    assert "Muitas rolagens" in ultimo["erro"]
    assert relatos.count("mesa_limite") == 1


def test_falha_inesperada_nao_derruba_a_ponte():
    ponte, armazem, _, relatos = montar({"p1": pedido()})
    armazem.reservar = lambda *a: (_ for _ in ()).throw(RuntimeError("rede"))
    processar(ponte, armazem)
    assert relatos == ["mesa_falha"]


@pytest.mark.parametrize(
    "nome, esperado",
    [
        ("Skar Lionet", "Skar Lionet"),
        ("@everyone", "everyone"),
        ("Discord Mod", "Mod"),
        ("clyde", "Caldron Sheets"),
        ("x" * 100, "x" * 80),
    ],
)
def test_nome_seguro_para_o_webhook(nome, esperado):
    assert nome_seguro(nome) == esperado


def _http_erro(status):
    return discord.HTTPException(SimpleNamespace(status=status, reason="x"), "erro")


def _enviador(monkeypatch, efeitos):
    webhook = SimpleNamespace(send=AsyncMock(side_effect=efeitos))
    monkeypatch.setattr(discord.Webhook, "from_url", lambda url, session: webhook)
    urls = {"mesa": "https://discord.com/api/webhooks/1/a", "mestre": None}
    return EnviadorWebhook(urls, session=object(), espera=0), webhook


def test_webhook_posta_cada_parte_com_nome_e_sem_mencoes(monkeypatch):
    enviar, webhook = _enviador(monkeypatch, [None, None])
    assert asyncio.run(enviar("mesa", "Skar", ("a", "b"))) is True
    assert webhook.send.await_count == 2
    kwargs = webhook.send.await_args.kwargs
    assert kwargs["username"] == "Skar"
    assert kwargs["allowed_mentions"].everyone is False


def test_webhook_tenta_de_novo_quando_discord_recusa_com_5xx(monkeypatch):
    enviar, webhook = _enviador(monkeypatch, [_http_erro(503), None])
    assert asyncio.run(enviar("mesa", "Skar", ("a",))) is True
    assert webhook.send.await_count == 2


def test_webhook_desiste_em_4xx_e_em_erro_de_rede_sem_repetir(monkeypatch):
    enviar, webhook = _enviador(monkeypatch, [_http_erro(404)])
    assert asyncio.run(enviar("mesa", "Skar", ("a",))) is False
    assert webhook.send.await_count == 1
    enviar, webhook = _enviador(monkeypatch, [OSError()])
    assert asyncio.run(enviar("mesa", "Skar", ("a",))) is False
    assert webhook.send.await_count == 1


def test_canal_sem_webhook_configurado_nao_posta(monkeypatch):
    enviar, webhook = _enviador(monkeypatch, [None])
    assert asyncio.run(enviar("mestre", "Mestre", ("a",))) is False
    webhook.send.assert_not_awaited()
