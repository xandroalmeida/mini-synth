"""Utilitários de baixo nível para portas MIDI de entrada (ALSA via rtmidi).

A lógica de *filtragem* de portas físicas é mantida em funções puras para poder
ser testada sem hardware nem ALSA (ver ``tests/test_midi_device_filter.py``).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

#: Trechos de nome que indicam portas *não* físicas (virtuais / do sistema /
#: criadas pelo próprio FluidSynth). Comparação sem diferenciar maiúsculas.
VIRTUAL_PORT_MARKERS: tuple[str, ...] = (
    "fluid",            # portas do próprio FluidSynth — nunca conectar em si
    "midi through",
    "through port",
    "rtmidi",
    "announce",
    "timer",
    "system",
    "pipewire",
    "mini synth",       # o nome do nosso próprio cliente
    "mini-synth",
)


@dataclass(frozen=True, slots=True)
class MidiPort:
    """Uma porta de entrada MIDI descoberta."""

    index: int
    name: str

    @property
    def is_physical(self) -> bool:
        return is_physical_port(self.name)


def is_physical_port(name: str) -> bool:
    """True se o nome parece ser de um teclado/controlador físico real."""
    lowered = name.lower()
    return not any(marker in lowered for marker in VIRTUAL_PORT_MARKERS)


def filter_physical(ports: list[MidiPort]) -> list[MidiPort]:
    """Mantém apenas portas físicas, preservando a ordem."""
    return [port for port in ports if port.is_physical]


def choose_port(
    ports: list[MidiPort], preferred: str | None = None
) -> MidiPort | None:
    """Escolhe a porta a usar.

    Prioriza uma que contenha ``preferred`` no nome; caso contrário, a primeira
    porta física disponível. Retorna ``None`` se não houver candidata.
    """
    physical = filter_physical(ports)
    if not physical:
        return None
    if preferred:
        pref = preferred.lower()
        for port in physical:
            if pref in port.name.lower():
                return port
    return physical[0]


def list_input_ports(midi_in: object) -> list[MidiPort]:
    """Lista as portas de entrada de um ``rtmidi.MidiIn`` já criado."""
    try:
        names = midi_in.get_ports()  # type: ignore[attr-defined]
    except Exception as exc:  # pragma: no cover - depende do rtmidi
        logger.error("Falha ao listar portas MIDI: %s", exc)
        return []
    return [MidiPort(index=i, name=name) for i, name in enumerate(names)]


def create_midi_in() -> object | None:
    """Cria um ``rtmidi.MidiIn`` com o cliente nomeado, ou ``None`` se falhar."""
    try:
        import rtmidi
    except ImportError:
        logger.error("python-rtmidi não está instalado.")
        return None
    try:
        midi_in = rtmidi.MidiIn(name="Mini Synth")
        midi_in.ignore_types(sysex=True, timing=True, active_sense=True)
        return midi_in
    except Exception as exc:  # pragma: no cover - depende do sistema
        logger.error("Não foi possível criar entrada MIDI: %s", exc)
        return None
