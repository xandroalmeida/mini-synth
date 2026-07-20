"""Sinal síncrono mínimo (substitui os ``Signal`` do Qt).

Mesma interface usada no código antigo — ``.connect(fn)`` e ``.emit(*args)`` —
para que a migração de PySide6 para pywebview não exija reescrever a fiação de
eventos entre MIDI, síntese e interface. É síncrono: ``emit`` chama cada
inscrito na hora, na thread que emitiu (igual a uma ``Signal`` Qt de conexão
direta).
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class Signal:
    """Lista de callbacks disparados juntos por :meth:`emit`."""

    __slots__ = ("_subscribers",)

    def __init__(self) -> None:
        self._subscribers: list[Callable[..., Any]] = []

    def connect(self, callback: Callable[..., Any]) -> None:
        """Inscreve um callback para ser chamado a cada ``emit``."""
        self._subscribers.append(callback)

    def disconnect(self, callback: Callable[..., Any]) -> None:
        try:
            self._subscribers.remove(callback)
        except ValueError:
            pass

    def emit(self, *args: Any) -> None:
        """Chama todos os inscritos com ``args``. Um erro num deles não impede
        os demais (apenas registra em debug)."""
        for callback in list(self._subscribers):
            try:
                callback(*args)
            except Exception:  # pragma: no cover - defensivo
                logger.debug("Erro em callback de Signal", exc_info=True)
