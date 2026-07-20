"""Modelos de dados da configuração.

Toda a configuração é validada aqui com ``dataclasses``. Nenhum número de
banco ou programa MIDI deve aparecer espalhado pelo restante do código: eles
vivem exclusivamente em :class:`Instrument`, montado a partir do YAML.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Erro de validação de configuração, com mensagem amigável."""


def _require(data: dict[str, Any], key: str, context: str) -> Any:
    if key not in data:
        raise ConfigError(f"Campo obrigatório '{key}' ausente em {context}.")
    return data[key]


def _as_int(value: Any, key: str, context: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - mensagem
        raise ConfigError(f"'{key}' em {context} deve ser inteiro.") from exc


@dataclass(slots=True)
class SoundfontConfig:
    path: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SoundfontConfig":
        return cls(path=str(_require(data, "path", "soundfont")))

    @property
    def resolved_path(self) -> Path:
        return Path(self.path).expanduser()


@dataclass(slots=True)
class AudioConfig:
    driver: str = "pulseaudio"
    gain: float = 0.8
    sample_rate: int = 44100
    buffer_size: int = 256

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AudioConfig":
        data = data or {}
        return cls(
            driver=str(data.get("driver", "pulseaudio")),
            gain=float(data.get("gain", 0.8)),
            sample_rate=_as_int(data.get("sample_rate", 44100), "sample_rate", "audio"),
            buffer_size=_as_int(data.get("buffer_size", 256), "buffer_size", "audio"),
        )


@dataclass(slots=True)
class MidiConfig:
    auto_connect: bool = True
    preferred_device: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "MidiConfig":
        data = data or {}
        return cls(
            auto_connect=bool(data.get("auto_connect", True)),
            preferred_device=str(data.get("preferred_device", "") or ""),
        )


@dataclass(slots=True)
class InterfaceConfig:
    fullscreen: bool = False
    columns: int = 4

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "InterfaceConfig":
        data = data or {}
        columns = _as_int(data.get("columns", 4), "columns", "interface")
        if columns < 1:
            raise ConfigError("'columns' em interface deve ser >= 1.")
        return cls(
            fullscreen=bool(data.get("fullscreen", False)),
            columns=columns,
        )


@dataclass(slots=True)
class Instrument:
    """Um instrumento selecionável — a única fonte de bank/program MIDI."""

    id: str
    label: str
    display_name: str
    bank: int = 0
    program: int = 0
    icon: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Instrument":
        ctx = f"instrumento '{data.get('id', '?')}'"
        bank = _as_int(data.get("bank", 0), "bank", ctx)
        program = _as_int(data.get("program", 0), "program", ctx)
        if not 0 <= bank <= 16383:
            raise ConfigError(f"'bank' fora do intervalo em {ctx} (0..16383).")
        if not 0 <= program <= 127:
            raise ConfigError(f"'program' fora do intervalo em {ctx} (0..127).")
        return cls(
            id=str(_require(data, "id", "instrumentos")),
            label=str(_require(data, "label", ctx)),
            display_name=str(data.get("display_name", data.get("label", ""))),
            bank=bank,
            program=program,
            icon=str(data.get("icon", "")),
        )


#: Ações que um knob (MIDI CC) pode disparar na interface.
KNOB_ACTIONS = ("instrument", "volume", "reverb", "octave", "none")


@dataclass(slots=True)
class KnobControl:
    """Mapeia um knob (número de MIDI Control Change) para uma ação do app."""

    cc: int
    action: str
    label: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnobControl":
        cc = _as_int(_require(data, "cc", "controls.knobs"), "cc", "controls.knobs")
        if not 0 <= cc <= 127:
            raise ConfigError(f"'cc' fora do intervalo em controls.knobs (0..127): {cc}.")
        action = str(_require(data, "action", "controls.knobs"))
        if action not in KNOB_ACTIONS:
            raise ConfigError(
                f"Ação de knob inválida: '{action}'. Use uma de: {', '.join(KNOB_ACTIONS)}."
            )
        return cls(cc=cc, action=action, label=str(data.get("label", "")))


@dataclass(slots=True)
class ControlsConfig:
    """Configuração dos controles físicos (knobs) do teclado."""

    knobs: list[KnobControl] = field(default_factory=list)
    #: Se um Program Change vindo do teclado (ex.: knob A1 em modo PC) deve
    #: trocar o instrumento na tela.
    program_change_selects_instrument: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ControlsConfig":
        data = data or {}
        knobs = [KnobControl.from_dict(item) for item in (data.get("knobs") or [])]
        return cls(
            knobs=knobs,
            program_change_selects_instrument=bool(
                data.get("program_change_selects_instrument", True)
            ),
        )

    def action_by_cc(self) -> dict[int, str]:
        """Retorna {numero_cc: acao}, ignorando ações 'none'."""
        return {k.cc: k.action for k in self.knobs if k.action != "none"}


@dataclass(slots=True)
class AppConfig:
    """Configuração completa do aplicativo (config/instruments.yaml)."""

    soundfont: SoundfontConfig
    audio: AudioConfig
    midi: MidiConfig
    interface: InterfaceConfig
    instruments: list[Instrument] = field(default_factory=list)
    controls: ControlsConfig = field(default_factory=ControlsConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        if not isinstance(data, dict):
            raise ConfigError("O arquivo de configuração está vazio ou inválido.")
        raw_instruments = data.get("instruments") or []
        if not raw_instruments:
            raise ConfigError("Nenhum instrumento definido na configuração.")
        instruments = [Instrument.from_dict(item) for item in raw_instruments]

        ids = [inst.id for inst in instruments]
        duplicates = {i for i in ids if ids.count(i) > 1}
        if duplicates:
            raise ConfigError(f"IDs de instrumento duplicados: {', '.join(sorted(duplicates))}.")

        return cls(
            soundfont=SoundfontConfig.from_dict(_require(data, "soundfont", "configuração")),
            audio=AudioConfig.from_dict(data.get("audio")),
            midi=MidiConfig.from_dict(data.get("midi")),
            interface=InterfaceConfig.from_dict(data.get("interface")),
            instruments=instruments,
            controls=ControlsConfig.from_dict(data.get("controls")),
        )

    def instrument_by_id(self, instrument_id: str) -> Instrument | None:
        for inst in self.instruments:
            if inst.id == instrument_id:
                return inst
        return None


@dataclass(slots=True)
class UserSettings:
    """Preferências do usuário persistidas em ~/.config/mini-synth/settings.yaml."""

    volume: int = 70
    reverb: int = 25
    octave: int = 0
    last_instrument: str = ""
    last_soundfont: str = ""
    preferred_midi_device: str = ""
    fullscreen: bool = False

    def __post_init__(self) -> None:
        self.volume = max(0, min(100, int(self.volume)))
        self.reverb = self._quantize_reverb(int(self.reverb))
        self.octave = max(-2, min(2, int(self.octave)))

    @staticmethod
    def _quantize_reverb(value: int) -> int:
        allowed = (0, 25, 50, 75, 100)
        return min(allowed, key=lambda a: abs(a - value))

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "UserSettings":
        data = data or {}
        return cls(
            volume=int(data.get("volume", 70)),
            reverb=int(data.get("reverb", 25)),
            octave=int(data.get("octave", 0)),
            last_instrument=str(data.get("last_instrument", "") or ""),
            last_soundfont=str(data.get("last_soundfont", "") or ""),
            preferred_midi_device=str(data.get("preferred_midi_device", "") or ""),
            fullscreen=bool(data.get("fullscreen", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "volume": self.volume,
            "reverb": self.reverb,
            "octave": self.octave,
            "last_instrument": self.last_instrument,
            "last_soundfont": self.last_soundfont,
            "preferred_midi_device": self.preferred_midi_device,
            "fullscreen": self.fullscreen,
        }
