"""Firestore do Caldron Sheets: escuta pedidos pendentes e grava resultados (Admin SDK).

A conta de serviço fica só neste PC (FIREBASE_CREDENCIAL no .env), como o token do Discord.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore
from google.auth.credentials import AnonymousCredentials
from google.cloud.firestore_v1.base_query import FieldFilter

from ponte.servico import Canal, PonteMesa

logger = logging.getLogger(__name__)

COLECOES: dict[Canal, str] = {"mesa": "mesa", "mestre": "mesaMestre"}


def conectar(credencial: Path | None, projeto: str | None = None):
    """Com credencial: projeto real. Sem ela, só com FIRESTORE_EMULATOR_HOST (testes)."""
    if credencial is None:
        if not (os.getenv("FIRESTORE_EMULATOR_HOST") and projeto):
            raise ValueError("Ponte sem credencial do Firebase.")
        return firestore.Client(project=projeto, credentials=AnonymousCredentials())
    nome = "caldron-sheets-ponte"
    try:
        app = firebase_admin.get_app(nome)
    except ValueError:
        app = firebase_admin.initialize_app(credentials.Certificate(str(credencial)), name=nome)
    return firestore.client(app)


class ArmazemFirestore:
    def __init__(self, db):
        self.db = db

    def _ref(self, canal: Canal, doc_id: str):
        return self.db.collection(COLECOES[canal]).document(doc_id)

    def reservar(self, canal: Canal, doc_id: str) -> dict[str, Any] | None:
        ref = self._ref(canal, doc_id)

        @firestore.transactional
        def _reservar(tx):
            snap = ref.get(transaction=tx)
            if not snap.exists:
                return None
            dados = snap.to_dict()
            if dados.get("estado") != "pendente":
                return None
            tx.update(ref, {"estado": "rolando"})
            return dados

        return _reservar(self.db.transaction())

    def ficha(self, ficha_id: str) -> dict[str, Any] | None:
        snap = self.db.collection("personagens").document(ficha_id).get()
        return snap.to_dict() if snap.exists else None

    def concluir(self, canal: Canal, doc_id: str, campos: dict[str, Any]) -> None:
        self._ref(canal, doc_id).update(campos)

    def recuperar_interrompidas(self) -> int:
        """Pedidos que ficaram 'rolando' porque o bot fechou no meio: viram erro, sem rolar."""
        total = 0
        for canal, colecao in COLECOES.items():
            consulta = self.db.collection(colecao).where(
                filter=FieldFilter("estado", "==", "rolando")
            )
            for snap in consulta.stream():
                self.concluir(
                    canal, snap.id, {"estado": "erro", "erro": "O bot fechou durante a rolagem."}
                )
                total += 1
        return total


def escutar(db, ponte: PonteMesa, loop: asyncio.AbstractEventLoop) -> list:
    """Escuta os pendentes das duas coleções. O SDK chama de outra thread; o trabalho vai para o
    event loop do bot. Devolve os 'watches' (chame .unsubscribe() para parar)."""
    watches = []
    for canal, colecao in COLECOES.items():

        def aviso(snaps, mudancas, _hora, canal=canal):
            for mudanca in mudancas:
                if mudanca.type.name != "ADDED":
                    continue
                doc = mudanca.document
                asyncio.run_coroutine_threadsafe(
                    ponte.processar(canal, doc.id, doc.to_dict() or {}), loop
                )

        consulta = db.collection(colecao).where(filter=FieldFilter("estado", "==", "pendente"))
        watches.append(consulta.on_snapshot(aviso))
    return watches
