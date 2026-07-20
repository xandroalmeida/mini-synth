"""Orquestração do aplicativo: liga configuração, síntese, MIDI e interface."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QTimer

from .audio.factory import create_backend
from .audio.synthesizer import Synthesizer, SynthError
from .config import loader
from .config.models import AppConfig, Instrument, UserSettings
from .midi.device_manager import (
    STATE_CONNECTED,
    STATE_ERROR,
    STATE_SEARCHING,
    MidiDeviceManager,
)
from .ui.main_window import MainWindow

logger = logging.getLogger(__name__)

TEST_SEQUENCE = (60, 64, 67, 72)
TEST_NOTE_MS = 350


def _scale(value: int, top: int) -> int:
    """Converte um valor de knob (0..127) para a escala 0..top."""
    return round(max(0, min(127, value)) / 127 * top)


class Application(QObject):
    """Controlador central. Não contém lógica de síntese nem de UI, só as liga."""

    def __init__(self, config: AppConfig, settings: UserSettings) -> None:
        super().__init__()
        self._config = config
        self._settings = settings

        self._synth: Synthesizer | None = None
        self._soundfont_path: str = ""
        self._audio_ready = False

        # Mapa {numero_cc: acao} dos knobs configurados (ex.: A1 -> instrument).
        self._knob_actions = config.controls.action_by_cc()

        self.window = MainWindow(config)
        self._midi = MidiDeviceManager(preferred_device=settings.preferred_midi_device)

        self._test_timer = QTimer(self)
        self._test_timer.setInterval(TEST_NOTE_MS)
        self._test_timer.timeout.connect(self._test_tick)
        self._test_notes: list[int] = []
        self._test_prev: int | None = None

        self._wire_ui()
        self._wire_midi()

    # ------------------------------------------------------------------
    # inicialização
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Executa a sequência de inicialização descrita na especificação."""
        if self._config.interface.fullscreen or self._settings.fullscreen:
            self.window.showFullScreen()
        else:
            # App infantil: abre maximizado para usar toda a tela e dar espaço
            # aos botões (evita a janela abrir no tamanho mínimo e apertar tudo).
            self.window.showMaximized()

        self._start_audio()
        self._midi.start()

    def _start_audio(self) -> bool:
        """Inicializa áudio + soundfont. Mostra tela de erro amigável se falhar."""
        self.window.set_audio_status("searching")
        try:
            self._soundfont_path = self._resolve_soundfont()
            backend = create_backend("auto", self._config.audio)
            synth = Synthesizer(backend, self._config.audio)
            synth.start()
            synth.load_soundfont(self._soundfont_path)
        except SynthError as exc:
            logger.error("Falha ao iniciar o áudio: %s", exc)
            self.window.set_audio_status("error")
            self.window.show_error(self._friendly_audio_error(exc))
            self._audio_ready = False
            return False
        except FileNotFoundError as exc:
            logger.error("SoundFont ausente: %s", exc)
            self.window.set_audio_status("error")
            self.window.show_error("SoundFont não encontrada.")
            self._audio_ready = False
            return False

        self._synth = synth
        self._audio_ready = True
        self.window.set_audio_status("connected", self._config.audio.driver)
        self._apply_initial_settings()
        self.window.show_main()
        logger.info("Áudio pronto.")
        return True

    def _resolve_soundfont(self) -> str:
        preferred = self._settings.last_soundfont or self._config.soundfont.path
        found = loader.find_soundfont(preferred)
        if found is None:
            raise FileNotFoundError("Nenhuma SoundFont encontrada.")
        return str(found)

    def _apply_initial_settings(self) -> None:
        assert self._synth is not None
        self._synth.set_volume(self._settings.volume)
        self._synth.set_reverb(self._settings.reverb)
        self._synth.set_octave(self._settings.octave)

        instrument = self._pick_initial_instrument()
        self._synth.select_instrument(instrument)

        self.window.set_current_instrument(instrument)
        self.window.control_panel.set_volume(self._synth.volume)
        self.window.control_panel.set_reverb(self._synth.reverb)
        self.window.control_panel.set_octave(self._synth.octave)
        self._refresh_settings_page()

    def _pick_initial_instrument(self) -> Instrument:
        if self._settings.last_instrument:
            inst = self._config.instrument_by_id(self._settings.last_instrument)
            if inst is not None:
                return inst
        # Padrão: grand piano se existir, senão o primeiro da lista.
        return self._config.instrument_by_id("grand_piano") or self._config.instruments[0]

    # ------------------------------------------------------------------
    # fiação da interface
    # ------------------------------------------------------------------
    def _wire_ui(self) -> None:
        self.window.instrument_selected.connect(self._on_instrument_selected)
        self.window.config_requested.connect(self._on_config_requested)
        self.window.retry_requested.connect(self._on_retry)

        cp = self.window.control_panel
        cp.volume_up.connect(lambda: self._on_volume(+1))
        cp.volume_down.connect(lambda: self._on_volume(-1))
        cp.reverb_up.connect(lambda: self._on_reverb(+1))
        cp.reverb_down.connect(lambda: self._on_reverb(-1))
        cp.octave_up.connect(lambda: self._on_octave(+1))
        cp.octave_down.connect(lambda: self._on_octave(-1))
        cp.octave_reset.connect(lambda: self._on_octave(0))
        cp.panic.connect(self._on_panic)

        sp = self.window.settings_page
        sp.soundfont_chosen.connect(self._on_soundfont_chosen)
        sp.rescan_requested.connect(self._on_rescan)
        sp.midi_device_selected.connect(self._on_midi_device_selected)
        sp.test_sound_requested.connect(self._on_test_sound)

    def _wire_midi(self) -> None:
        self._midi.status_changed.connect(self._on_midi_status)
        self._midi.note_on.connect(self._on_note_on)
        self._midi.note_off.connect(self._on_note_off)
        self._midi.control_change.connect(self._on_control_change)
        self._midi.program_change.connect(self._on_program_change)

    # ------------------------------------------------------------------
    # eventos de instrumento / controles
    # ------------------------------------------------------------------
    def _on_instrument_selected(self, instrument: Instrument) -> None:
        if self._synth is not None:
            self._synth.select_instrument(instrument)
        self.window.set_current_instrument(instrument)
        self._settings.last_instrument = instrument.id
        self._persist()

    def _on_volume(self, direction: int) -> None:
        if self._synth is None:
            return
        value = self._synth.volume_up() if direction > 0 else self._synth.volume_down()
        self.window.control_panel.set_volume(value)
        self._settings.volume = value
        self._persist()

    def _on_reverb(self, direction: int) -> None:
        if self._synth is None:
            return
        value = self._synth.reverb_up() if direction > 0 else self._synth.reverb_down()
        self.window.control_panel.set_reverb(value)
        self._settings.reverb = value
        self._persist()

    def _on_octave(self, direction: int) -> None:
        if self._synth is None:
            return
        if direction > 0:
            value = self._synth.octave_up()
        elif direction < 0:
            value = self._synth.octave_down()
        else:
            value = self._synth.octave_reset()
        self.window.control_panel.set_octave(value)
        self._settings.octave = value
        self._persist()

    def _on_panic(self) -> None:
        if self._synth is not None:
            self._synth.panic()

    # ------------------------------------------------------------------
    # eventos MIDI vindos do teclado
    # ------------------------------------------------------------------
    def _on_note_on(self, note: int, velocity: int) -> None:
        if self._synth is not None:
            self._synth.handle_note_on(note, velocity)

    def _on_note_off(self, note: int) -> None:
        if self._synth is not None:
            self._synth.handle_note_off(note)

    def _on_control_change(self, control: int, value: int) -> None:
        if self._synth is None:
            return
        action = self._knob_actions.get(control)
        logger.debug("CC %d = %d -> ação: %s", control, value, action or "(synth)")
        if action is None:
            # CC não mapeado (pedal de sustain, etc.) segue para o synth.
            self._synth.handle_control_change(control, value)
            return
        if action == "instrument":
            self._knob_change_instrument(value)
        elif action == "volume":
            self._settings.volume = self._synth.set_volume(_scale(value, 100))
            self.window.control_panel.set_volume(self._settings.volume)
            self._persist()
        elif action == "reverb":
            self._settings.reverb = self._synth.set_reverb(_scale(value, 100))
            self.window.control_panel.set_reverb(self._settings.reverb)
            self._persist()
        elif action == "octave":
            # 0..127 -> -2..+2 em cinco faixas.
            self._settings.octave = self._synth.set_octave(round(value / 127 * 4) - 2)
            self.window.control_panel.set_octave(self._settings.octave)
            self._persist()

    def _on_program_change(self, program: int) -> None:
        """Program Change do teclado (ex.: knob A1 em modo PC) troca o instrumento.

        Mapeamento direto: valor 1 -> 1º instrumento, ..., valor 12 -> 12º.
        Acima do número de instrumentos, permanece no último (não avança).
        """
        if self._synth is None:
            return
        logger.debug("Program Change %d recebido", program)
        if self._config.controls.program_change_selects_instrument:
            self._select_instrument_by_number(program)

    def _select_instrument_by_number(self, number: int) -> None:
        """Seleciona o instrumento pelo número 1..N; fora da faixa fica no extremo."""
        instruments = self._config.instruments
        if not instruments:
            return
        index = max(0, min(len(instruments) - 1, number - 1))
        instrument = instruments[index]
        if self._synth is not None and self._synth.current_instrument is instrument:
            return
        self._on_instrument_selected(instrument)

    def _knob_change_instrument(self, value: int) -> None:
        """Gira o knob A1 pelos instrumentos (posição absoluta 0..127)."""
        instruments = self._config.instruments
        if not instruments:
            return
        index = min(len(instruments) - 1, round(value / 127 * (len(instruments) - 1)))
        instrument = instruments[index]
        # Só troca quando realmente muda de instrumento (evita repetição).
        if self._synth is not None and self._synth.current_instrument is instrument:
            return
        self._on_instrument_selected(instrument)

    def _on_midi_status(self, state: str, message: str) -> None:
        self.window.set_midi_status(state, message)
        if state == STATE_CONNECTED:
            self._settings.preferred_midi_device = message
            self._persist()
        self._refresh_settings_page()

    # ------------------------------------------------------------------
    # tela de configuração
    # ------------------------------------------------------------------
    def _on_config_requested(self) -> None:
        self._refresh_settings_page()
        self.window.show_settings()

    def _refresh_settings_page(self) -> None:
        sp = self.window.settings_page
        sp.set_soundfont(self._soundfont_path or self._config.soundfont.path)
        sp.set_audio_driver(self._config.audio.driver)
        names = [p.name for p in self._midi.list_ports() if p.is_physical]
        sp.set_midi_devices(names, self._midi.connected_device)

    def _on_soundfont_chosen(self, path: str) -> None:
        if self._synth is None:
            return
        try:
            self._synth.load_soundfont(path)
        except SynthError as exc:
            logger.error("Falha ao carregar SoundFont: %s", exc)
            self.window.show_error("SoundFont não encontrada.")
            return
        self._soundfont_path = path
        self._settings.last_soundfont = path
        self._persist()
        self._refresh_settings_page()

    def _on_rescan(self) -> None:
        self._midi.rescan()
        self._refresh_settings_page()

    def _on_midi_device_selected(self, name: str) -> None:
        self._midi.set_preferred_device(name)
        self._settings.preferred_midi_device = name
        self._midi.rescan()
        self._persist()

    # ------------------------------------------------------------------
    # som de teste (QTimer, quatro notas)
    # ------------------------------------------------------------------
    def _on_test_sound(self) -> None:
        if self._synth is None or self._test_timer.isActive():
            return
        self._test_notes = list(TEST_SEQUENCE)
        self._test_prev = None
        self._test_timer.start()
        self._test_tick()

    def _test_tick(self) -> None:
        assert self._synth is not None
        if self._test_prev is not None:
            self._synth.handle_note_off(self._test_prev)
            self._test_prev = None
        if not self._test_notes:
            self._test_timer.stop()
            return
        note = self._test_notes.pop(0)
        self._synth.handle_note_on(note, 100)
        self._test_prev = note

    # ------------------------------------------------------------------
    # erro / retry / persistência / shutdown
    # ------------------------------------------------------------------
    def _on_retry(self) -> None:
        logger.info("Tentando iniciar o áudio novamente...")
        self._start_audio()

    def _persist(self) -> None:
        self._settings.fullscreen = self.window.isFullScreen()
        loader.save_user_settings(self._settings)

    def shutdown(self) -> None:
        logger.info("Encerrando aplicativo.")
        self._persist()
        try:
            self._midi.stop()
        except Exception:  # pragma: no cover
            logger.debug("Erro ao parar MIDI", exc_info=True)
        if self._synth is not None:
            self._synth.stop()

    @staticmethod
    def _friendly_audio_error(exc: SynthError) -> str:
        text = str(exc)
        if "pyfluidsynth" in text or "não está instalada" in text:
            return "FluidSynth não está instalado."
        if "fluidsynth' não está instalado" in text:
            return "FluidSynth não está instalado."
        if "áudio" in text.lower():
            return "Não foi possível iniciar o áudio."
        return "Não foi possível iniciar o som."
