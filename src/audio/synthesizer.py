"""Fachada de síntese e protocolo de backend.

A classe :class:`Synthesizer` concentra toda a *lógica musical* de alto nível
(seleção de instrumento, volume, reverb, oitava, panic, notas de teste) e
delega as operações de baixo nível a um :class:`SynthesizerBackend`.

Existem três backends intercambiáveis:

1. :class:`~src.audio.fluidsynth_backend.FluidSynthBackend` — libfluidsynth;
2. :class:`~src.audio.subprocess_backend.SubprocessBackend` — processo externo;
3. :class:`~src.audio.mock_backend.MockBackend` — para testes.

Toda entrada MIDI vinda do teclado é encaminhada para o **canal 0** e o
instrumento selecionado é programado nesse canal. Assim, seja qual for o canal
que o teclado use, a criança sempre ouve o instrumento escolhido.
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from ..config.models import AudioConfig, Instrument

logger = logging.getLogger(__name__)

#: Canal MIDI para o qual todas as notas do teclado são roteadas.
PLAY_CHANNEL = 0

#: Faixa de oitavas permitida (em oitavas de transposição).
MIN_OCTAVE = -2
MAX_OCTAVE = 2

#: Ganho de reverb do FluidSynth para cada nível "amigável" (0..100).
_REVERB_LEVELS = {0: 0.0, 25: 0.3, 50: 0.55, 75: 0.8, 100: 1.0}


class SynthError(RuntimeError):
    """Falha na inicialização ou operação do sintetizador."""


@runtime_checkable
class SynthesizerBackend(Protocol):
    """Contrato de baixo nível implementado por cada backend de síntese."""

    def start(self) -> None:
        """Inicializa o motor e o driver de áudio."""

    def stop(self) -> None:
        """Libera todos os recursos."""

    def is_running(self) -> bool:
        ...

    def load_soundfont(self, path: str) -> int:
        """Carrega um ``.sf2``/``.sf3`` e retorna o id do soundfont."""

    def program_select(self, channel: int, sfid: int, bank: int, program: int) -> None:
        """Bank Select + Program Change em um canal."""

    def set_gain(self, gain: float) -> None:
        ...

    def set_reverb(self, level: float) -> None:
        """Define o nível de reverb (0.0..1.0)."""

    def note_on(self, channel: int, note: int, velocity: int) -> None:
        ...

    def note_off(self, channel: int, note: int) -> None:
        ...

    def control_change(self, channel: int, control: int, value: int) -> None:
        ...

    def system_reset(self) -> None:
        ...


class Synthesizer:
    """Lógica musical de alto nível sobre um :class:`SynthesizerBackend`."""

    def __init__(self, backend: SynthesizerBackend, audio: AudioConfig) -> None:
        self._backend = backend
        self._audio = audio
        self._sfid: int | None = None
        self._current: Instrument | None = None
        self._volume = 70
        self._reverb = 25
        self._octave = 0
        self._max_gain = max(0.1, audio.gain)

    # ---- ciclo de vida -------------------------------------------------
    @property
    def backend(self) -> SynthesizerBackend:
        return self._backend

    @property
    def is_running(self) -> bool:
        return self._backend.is_running()

    def start(self) -> None:
        self._backend.start()

    def stop(self) -> None:
        try:
            self.panic()
        except Exception:  # pragma: no cover - defensivo no shutdown
            pass
        self._backend.stop()

    def load_soundfont(self, path: str) -> None:
        self._sfid = self._backend.load_soundfont(path)
        logger.info("SoundFont carregada (sfid=%s): %s", self._sfid, path)
        # Reaplica o instrumento atual (ou fica pronto para o primeiro select).
        if self._current is not None:
            self.select_instrument(self._current)

    # ---- estado --------------------------------------------------------
    @property
    def current_instrument(self) -> Instrument | None:
        return self._current

    @property
    def volume(self) -> int:
        return self._volume

    @property
    def reverb(self) -> int:
        return self._reverb

    @property
    def octave(self) -> int:
        return self._octave

    # ---- seleção de instrumento ---------------------------------------
    def select_instrument(self, instrument: Instrument) -> None:
        """Envia Bank Select + Program Change para o canal de execução."""
        if self._sfid is None:
            # Guarda a escolha; será aplicada quando a soundfont carregar.
            self._current = instrument
            logger.debug("Instrumento pendente até soundfont carregar: %s", instrument.id)
            return
        self._backend.program_select(
            PLAY_CHANNEL, self._sfid, instrument.bank, instrument.program
        )
        self._current = instrument
        logger.info(
            "Instrumento: %s (bank=%d program=%d)",
            instrument.display_name,
            instrument.bank,
            instrument.program,
        )

    # ---- volume --------------------------------------------------------
    def set_volume(self, volume: int) -> int:
        self._volume = max(0, min(100, int(volume)))
        gain = round(self._max_gain * (self._volume / 100.0), 4)
        self._backend.set_gain(gain)
        return self._volume

    def volume_up(self, step: int = 5) -> int:
        return self.set_volume(self._volume + step)

    def volume_down(self, step: int = 5) -> int:
        return self.set_volume(self._volume - step)

    # ---- reverb --------------------------------------------------------
    def set_reverb(self, percent: int) -> int:
        percent = min(_REVERB_LEVELS, key=lambda a: abs(a - int(percent)))
        self._reverb = percent
        self._backend.set_reverb(_REVERB_LEVELS[percent])
        return self._reverb

    def reverb_up(self) -> int:
        steps = sorted(_REVERB_LEVELS)
        idx = min(steps.index(self._reverb) + 1, len(steps) - 1)
        return self.set_reverb(steps[idx])

    def reverb_down(self) -> int:
        steps = sorted(_REVERB_LEVELS)
        idx = max(steps.index(self._reverb) - 1, 0)
        return self.set_reverb(steps[idx])

    # ---- oitava --------------------------------------------------------
    def set_octave(self, octave: int) -> int:
        self._octave = max(MIN_OCTAVE, min(MAX_OCTAVE, int(octave)))
        return self._octave

    def octave_up(self) -> int:
        return self.set_octave(self._octave + 1)

    def octave_down(self) -> int:
        return self.set_octave(self._octave - 1)

    def octave_reset(self) -> int:
        return self.set_octave(0)

    def transpose(self, note: int) -> int | None:
        """Aplica a transposição de oitava. Retorna ``None`` se sair de 0..127."""
        transposed = note + 12 * self._octave
        if 0 <= transposed <= 127:
            return transposed
        return None

    # ---- notas (entrada MIDI / teste) ---------------------------------
    def handle_note_on(self, note: int, velocity: int) -> None:
        if velocity == 0:
            self.handle_note_off(note)
            return
        transposed = self.transpose(note)
        if transposed is not None:
            self._backend.note_on(PLAY_CHANNEL, transposed, velocity)

    def handle_note_off(self, note: int) -> None:
        transposed = self.transpose(note)
        if transposed is not None:
            self._backend.note_off(PLAY_CHANNEL, transposed)

    def handle_control_change(self, control: int, value: int) -> None:
        self._backend.control_change(PLAY_CHANNEL, control, value)

    # ---- panic ---------------------------------------------------------
    def panic(self) -> None:
        """Interrompe qualquer som travado em todos os canais.

        Envia All Sound Off (CC120) e All Notes Off (CC123) em todos os 16
        canais e faz um reset do sistema MIDI.
        """
        for channel in range(16):
            self._backend.control_change(channel, 120, 0)  # All Sound Off
            self._backend.control_change(channel, 123, 0)  # All Notes Off
        self._backend.system_reset()
        logger.info("PANIC: notas e som interrompidos em todos os canais.")

    # ---- som de teste --------------------------------------------------
    def play_test_sequence(self, notes: tuple[int, ...] = (60, 64, 67, 72)) -> None:
        """Toca uma pequena sequência para verificar o áudio.

        Usa notas diretas (sem transposição) no canal de execução com o
        instrumento atualmente selecionado.
        """
        for note in notes:
            self._backend.note_on(PLAY_CHANNEL, note, 100)
            self._backend.note_off(PLAY_CHANNEL, note)
