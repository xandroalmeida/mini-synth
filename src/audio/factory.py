"""Seleção do backend de síntese.

Permite trocar entre libfluidsynth, processo externo e mock sem que o resto
do aplicativo saiba qual está em uso.
"""

from __future__ import annotations

import logging
from typing import Literal

from ..config.models import AudioConfig
from .synthesizer import SynthesizerBackend

logger = logging.getLogger(__name__)

BackendKind = Literal["fluidsynth", "subprocess", "mock", "auto"]


def create_backend(kind: BackendKind, audio: AudioConfig) -> SynthesizerBackend:
    """Cria um backend do tipo pedido.

    ``auto`` tenta libfluidsynth e, se indisponível, cai para o subprocesso.
    """
    if kind in ("fluidsynth", "auto"):
        try:
            import fluidsynth  # noqa: F401
            from .fluidsynth_backend import FluidSynthBackend

            return FluidSynthBackend(audio)
        except ImportError:
            if kind == "fluidsynth":
                raise
            logger.warning("pyfluidsynth indisponível; usando subprocesso.")

    if kind in ("subprocess", "auto"):
        from .subprocess_backend import SubprocessBackend

        return SubprocessBackend(audio)

    if kind == "mock":
        from .mock_backend import MockBackend

        return MockBackend()

    raise ValueError(f"Backend desconhecido: {kind}")
