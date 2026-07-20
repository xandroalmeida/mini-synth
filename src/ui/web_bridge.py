"""Ponte entre o núcleo Python e a interface web (pywebview).

Expõe ao :class:`~src.application.Application` os sinais (``instrument_selected``,
``bank_selected``…), o ``control_panel``, a ``settings_page`` e os métodos
``set_current_instrument`` / ``set_current_bank`` / ``show_main`` etc.

Dois sentidos de comunicação:

* **JS -> Python**: a classe :class:`Api` é exposta ao JavaScript como
  ``pywebview.api``; cada método traduz um clique num ``Signal`` que o
  Application escuta.
* **Python -> JS**: os métodos ``set_*`` chamam ``window.evaluate_js('MS.…')``
  para atualizar a tela. Antes da janela existir (nos testes), guardam apenas o
  estado em atributos Python — por isso tudo continua testável sem interface.
"""

from __future__ import annotations

import json
import logging

from ..config.models import AppConfig, Bank, Instrument
from ..util.signal import Signal
from .themes import DEFAULT_THEME, normalize_theme, theme_options

logger = logging.getLogger(__name__)


def _instrument_dict(inst: Instrument) -> dict:
    return {
        "id": inst.id,
        "label": inst.label,
        "display_name": inst.display_name,
        "icon": inst.icon,
        "percussion": inst.percussion,
    }


def _bank_dict(bank: Bank) -> dict:
    return {
        "id": bank.id,
        "label": bank.label,
        "icon": bank.icon,
        "instruments": [_instrument_dict(i) for i in bank.instruments],
    }


class _TextHolder:
    """Imita o ``VfdDisplay`` (só o ``text()``), usado pelos testes."""

    def __init__(self) -> None:
        self._text = ""

    def text(self) -> str:
        return self._text

    def setText(self, text: str) -> None:  # noqa: N802 (nome camelCase da API da UI)
        self._text = text


class ControlPanelProxy:
    """Painel de controles: sinais de clique + mostradores."""

    def __init__(self, bridge: "WebUiBridge") -> None:
        self._bridge = bridge
        self.volume_up = Signal()
        self.volume_down = Signal()
        self.reverb_up = Signal()
        self.reverb_down = Signal()
        self.octave_up = Signal()
        self.octave_down = Signal()
        self.octave_reset = Signal()
        self.panic = Signal()
        self.volume = 0
        self.reverb = 0
        self.octave = 0

    def set_volume(self, value: int) -> None:
        self.volume = value
        self._bridge._push(f"MS.setControl('volume', {json.dumps(str(value))})")

    def set_reverb(self, value: int) -> None:
        self.reverb = value
        self._bridge._push(f"MS.setControl('reverb', {json.dumps(str(value))})")

    def set_octave(self, value: int) -> None:
        self.octave = value
        text = f"{value:+d}" if value else "0"
        self._bridge._push(f"MS.setControl('octave', {json.dumps(text)})")


class SettingsPageProxy:
    """Página de ajustes: sinais + preenchimento de campos."""

    def __init__(self, bridge: "WebUiBridge") -> None:
        self._bridge = bridge
        self.soundfont_chosen = Signal()
        self.rescan_requested = Signal()
        self.midi_device_selected = Signal()
        self.test_sound_requested = Signal()
        self.theme_selected = Signal()

    def set_soundfont(self, path: str) -> None:
        self._bridge._push(f"MS.setSetting('soundfont', {json.dumps(path or '—')})")

    def set_audio_driver(self, driver: str) -> None:
        self._bridge._push(f"MS.setSetting('driver', {json.dumps(driver or '—')})")

    def set_midi_devices(self, names: list[str], current: str) -> None:
        self._bridge._push(
            f"MS.setMidiDevices({json.dumps(names)}, {json.dumps(current or '')})"
        )

    def set_theme(self, theme_id: str) -> str:
        return self._bridge.set_theme(theme_id)


class Api:
    """Objeto exposto ao JavaScript como ``pywebview.api``.

    Cada método é chamado por um clique/evento na página e o traduz num sinal
    que o :class:`Application` já sabe tratar.
    """

    def __init__(self, bridge: "WebUiBridge") -> None:
        self._bridge = bridge

    # --- seleção principal ---
    def select_instrument(self, instrument_id: str) -> None:
        inst = self._bridge.config.instrument_by_id(instrument_id)
        if inst is not None:
            self._bridge.instrument_selected.emit(inst)

    def select_bank(self, bank_id: str) -> None:
        self._bridge.bank_selected.emit(bank_id)

    def open_config(self) -> None:
        self._bridge.config_requested.emit()

    def back(self) -> None:
        self._bridge.show_main()

    def retry(self) -> None:
        self._bridge.retry_requested.emit()

    # --- painel de controles ---
    def volume(self, direction: int) -> None:
        cp = self._bridge.control_panel
        (cp.volume_up if direction > 0 else cp.volume_down).emit()

    def reverb(self, direction: int) -> None:
        cp = self._bridge.control_panel
        (cp.reverb_up if direction > 0 else cp.reverb_down).emit()

    def octave(self, direction: int) -> None:
        cp = self._bridge.control_panel
        if direction > 0:
            cp.octave_up.emit()
        elif direction < 0:
            cp.octave_down.emit()
        else:
            cp.octave_reset.emit()

    def panic(self) -> None:
        self._bridge.control_panel.panic.emit()

    # --- tela de configuração ---
    def rescan(self) -> None:
        self._bridge.settings_page.rescan_requested.emit()

    def select_midi(self, name: str) -> None:
        self._bridge.settings_page.midi_device_selected.emit(name)

    def test_sound(self) -> None:
        self._bridge.settings_page.test_sound_requested.emit()

    def select_theme(self, theme_id: str) -> None:
        self._bridge.settings_page.theme_selected.emit(theme_id)

    def choose_soundfont(self) -> None:
        """Abre o diálogo nativo do pywebview para escolher uma SoundFont."""
        window = self._bridge.window_handle
        if window is None:
            return
        try:
            import webview

            result = window.create_file_dialog(
                webview.OPEN_DIALOG,
                directory="/usr/share/sounds",
                file_types=("SoundFonts (*.sf2;*.sf3)", "Todos os arquivos (*.*)"),
            )
        except Exception:  # pragma: no cover - depende do backend
            logger.debug("Falha ao abrir diálogo de arquivo", exc_info=True)
            return
        if result:
            path = result[0] if isinstance(result, (list, tuple)) else result
            self._bridge.settings_page.soundfont_chosen.emit(path)


class WebUiBridge:
    """Fachada da interface: API pública consumida pelo ``Application``."""

    def __init__(self, config: AppConfig, theme: str = DEFAULT_THEME) -> None:
        self.config = config
        self._window = None  # webview.Window, atribuído em attach()

        # sinais emitidos para o Application
        self.instrument_selected = Signal()
        self.bank_selected = Signal()
        self.config_requested = Signal()
        self.retry_requested = Signal()

        self.control_panel = ControlPanelProxy(self)
        self.settings_page = SettingsPageProxy(self)
        self.display_value = _TextHolder()
        self.api = Api(self)

        self._current_instrument: Instrument | None = None
        self._current_bank: Bank | None = None
        self._page = "main"
        self._fullscreen = False
        self._theme_id = normalize_theme(theme)

    # ------------------------------------------------------------------
    # ligação com a janela pywebview
    # ------------------------------------------------------------------
    def attach(self, window) -> None:
        """Associa a janela pywebview (chamado quando ela é criada)."""
        self._window = window

    @property
    def window_handle(self):
        return self._window

    def _push(self, js: str) -> None:
        """Executa JS na página, se a janela existir (no-op nos testes)."""
        if self._window is None:
            return
        try:
            self._window.evaluate_js(js)
        except Exception:  # pragma: no cover - depende do runtime
            logger.debug("evaluate_js falhou: %s", js, exc_info=True)

    def init_ui(self) -> None:
        """Envia a configuração (bancos + instrumentos) para o JS montar a tela."""
        payload = {
            "banks": [_bank_dict(b) for b in self.config.banks],
            "columns": self.config.interface.columns,
            "theme": self._theme_id,
            "themes": theme_options(),
        }
        # WebKitGTK recebe de pywebview o comprimento do script separadamente.
        # Escapar Unicode evita que caracteres multibyte façam o backend cortar
        # o payload grande antes do fechamento ("Unexpected end of script").
        self._push(f"MS.init({json.dumps(payload, ensure_ascii=True)})")

    # ------------------------------------------------------------------
    # API consumida pelo Application
    # ------------------------------------------------------------------
    def set_current_instrument(self, instrument: Instrument) -> None:
        self._current_instrument = instrument
        text = instrument.display_name.upper()
        self.display_value.setText(text)
        self._push(
            f"MS.setCurrentInstrument({json.dumps(instrument.id)}, {json.dumps(text)})"
        )

    def set_current_bank(self, bank: Bank) -> None:
        self._current_bank = bank
        self._push(f"MS.setCurrentBank({json.dumps(bank.id)})")

    def set_midi_status(self, state: str, message: str) -> None:
        self._push(f"MS.setStatus('midi', {json.dumps(state)}, {json.dumps(message)})")

    def set_audio_status(self, state: str, message: str = "") -> None:
        self._push(f"MS.setStatus('audio', {json.dumps(state)}, {json.dumps(message)})")

    @property
    def theme_id(self) -> str:
        return self._theme_id

    def set_theme(self, theme_id: str) -> str:
        normalized = normalize_theme(theme_id)
        if normalized != self._theme_id:
            self._theme_id = normalized
            self._push(f"MS.setTheme({json.dumps(self._theme_id)})")
        return self._theme_id

    def show_main(self) -> None:
        self._page = "main"
        self._push("MS.showPage('main')")

    def show_settings(self) -> None:
        self._page = "settings"
        self._push("MS.showPage('settings')")

    def show_error(self, message: str, *, retryable: bool = True) -> None:
        self._page = "error"
        self._push(f"MS.showError({json.dumps(message)}, {json.dumps(bool(retryable))})")

    def is_on_error_page(self) -> bool:
        return self._page == "error"

    # ------------------------------------------------------------------
    # tela cheia (a janela é gerida pelo pywebview)
    # ------------------------------------------------------------------
    def isFullScreen(self) -> bool:  # noqa: N802 (nome camelCase usado no Application)
        return self._fullscreen

    def set_fullscreen(self, on: bool) -> None:
        self._fullscreen = bool(on)

    # ------------------------------------------------------------------
    # auxiliares de teste
    # ------------------------------------------------------------------
    @property
    def current_display_text(self) -> str:
        """Texto atualmente no visor VFD (usado pelos testes)."""
        return self.display_value.text()
