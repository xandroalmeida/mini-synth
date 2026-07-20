"""Backend baseado em libfluidsynth via ``pyfluidsynth``.

Este é o backend preferencial: fala diretamente com a libfluidsynth, sem
depender do binário de linha de comando nem do Qsynth.
"""

from __future__ import annotations

import logging

from ..config.models import AudioConfig
from .synthesizer import SynthError

logger = logging.getLogger(__name__)


class FluidSynthBackend:
    """Implementa o protocolo ``SynthesizerBackend`` usando libfluidsynth."""

    def __init__(self, audio: AudioConfig) -> None:
        self._audio = audio
        self._fs = None  # fluidsynth.Synth
        self._running = False

    def start(self) -> None:
        try:
            import fluidsynth  # importado tardiamente para permitir mock nos testes
        except ImportError as exc:
            raise SynthError(
                "A biblioteca pyfluidsynth não está instalada."
            ) from exc

        try:
            fs = fluidsynth.Synth(
                gain=self._audio.gain,
                samplerate=float(self._audio.sample_rate),
            )
            # Ajustes de baixa latência antes de iniciar o driver.
            for name, value in (
                ("audio.period-size", self._audio.buffer_size),
                ("audio.periods", 2),
                ("synth.cpu-cores", 2),
            ):
                try:
                    fs.setting(name, value)
                except Exception:  # pragma: no cover - setting opcional
                    logger.debug("Setting não aplicado: %s", name)

            fs.start(driver=self._audio.driver)
        except Exception as exc:  # pragma: no cover - depende do sistema
            raise SynthError(
                f"Não foi possível iniciar o áudio (driver '{self._audio.driver}')."
            ) from exc

        self._fs = fs
        self._running = True
        logger.info(
            "FluidSynth iniciado (driver=%s, sr=%d, buffer=%d).",
            self._audio.driver,
            self._audio.sample_rate,
            self._audio.buffer_size,
        )

    def stop(self) -> None:
        if self._fs is not None:
            try:
                self._fs.delete()
            except Exception:  # pragma: no cover
                logger.debug("Erro ao liberar FluidSynth", exc_info=True)
        self._fs = None
        self._running = False

    def is_running(self) -> bool:
        return self._running and self._fs is not None

    def load_soundfont(self, path: str) -> int:
        if self._fs is None:
            raise SynthError("Sintetizador não iniciado.")
        sfid = self._fs.sfload(path)
        if sfid == -1:
            raise SynthError("Não foi possível carregar a SoundFont.")
        return sfid

    def program_select(self, channel: int, sfid: int, bank: int, program: int) -> None:
        if self._fs is None:
            return
        self._fs.program_select(channel, sfid, bank, program)

    def set_gain(self, gain: float) -> None:
        if self._fs is None:
            return
        try:
            self._fs.setting("synth.gain", float(gain))
        except Exception:  # pragma: no cover
            logger.debug("Falha ao ajustar ganho", exc_info=True)

    def set_reverb(self, level: float) -> None:
        if self._fs is None:
            return
        try:
            # API nova (pyfluidsynth >= 1.3): set_reverb(roomsize, damping, width, level)
            self._fs.set_reverb(roomsize=0.6, damping=0.3, width=0.5, level=level)
        except TypeError:  # pragma: no cover - APIs antigas
            try:
                self._fs.set_reverb_level(level)  # type: ignore[attr-defined]
            except Exception:
                logger.debug("Falha ao ajustar reverb", exc_info=True)
        except Exception:  # pragma: no cover
            logger.debug("Falha ao ajustar reverb", exc_info=True)

    def note_on(self, channel: int, note: int, velocity: int) -> None:
        if self._fs is not None:
            self._fs.noteon(channel, note, velocity)

    def note_off(self, channel: int, note: int) -> None:
        if self._fs is not None:
            self._fs.noteoff(channel, note)

    def control_change(self, channel: int, control: int, value: int) -> None:
        if self._fs is not None:
            self._fs.cc(channel, control, value)

    def system_reset(self) -> None:
        if self._fs is None:
            return
        try:
            self._fs.system_reset()
        except Exception:  # pragma: no cover
            logger.debug("Falha no system_reset", exc_info=True)
