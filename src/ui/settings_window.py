"""Tela CONFIG — painel simples para ajustes menos frequentes.

Continua com aparência de equipamento físico. É a única tela onde um dropdown
é aceitável (para escolher o dispositivo MIDI), conforme as regras do projeto.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from .buttons import PanelButton


def _field_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("SettingsField")
    return label


def _value_label(text: str = "") -> QLabel:
    label = QLabel(text)
    label.setObjectName("SettingsValue")
    label.setWordWrap(True)
    return label


def _action_button(text: str) -> PanelButton:
    btn = PanelButton(text, role="metal", font_size=18)
    btn.setMinimumHeight(58)
    return btn


class SettingsPage(QWidget):
    """Página de configuração exibida dentro do QStackedWidget principal."""

    soundfont_chosen = Signal(str)
    rescan_requested = Signal()
    midi_device_selected = Signal(str)
    test_sound_requested = Signal()
    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._updating_combo = False

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 30)
        root.setSpacing(20)

        header = QHBoxLayout()
        title = QLabel("CONFIGURAÇÃO")
        title.setObjectName("SettingsTitle")
        header.addWidget(title)
        header.addStretch(1)
        self._back = PanelButton("◄  VOLTAR", role="metal", font_size=16)
        self._back.setMinimumSize(150, 50)
        self._back.clicked.connect(self.back_requested)
        header.addWidget(self._back)
        root.addLayout(header)

        card = QFrame()
        card.setProperty("class", "Card")
        grid = QGridLayout(card)
        grid.setContentsMargins(28, 24, 28, 24)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(18)

        # --- SoundFont ---
        grid.addWidget(_field_label("SOUNDFONT ATUAL"), 0, 0)
        self._soundfont_value = _value_label("—")
        grid.addWidget(self._soundfont_value, 0, 1)
        choose = _action_button("Escolher outro arquivo")
        choose.clicked.connect(self._choose_soundfont)
        grid.addWidget(choose, 0, 2)

        # --- MIDI ---
        grid.addWidget(_field_label("DISPOSITIVO MIDI"), 1, 0)
        self._midi_combo = QComboBox()
        self._midi_combo.setMinimumWidth(280)
        self._midi_combo.currentIndexChanged.connect(self._on_midi_changed)
        grid.addWidget(self._midi_combo, 1, 1)
        rescan = _action_button("Detectar novamente")
        rescan.clicked.connect(self.rescan_requested)
        grid.addWidget(rescan, 1, 2)

        # --- Áudio ---
        grid.addWidget(_field_label("DRIVER DE ÁUDIO"), 2, 0)
        self._audio_value = _value_label("—")
        grid.addWidget(self._audio_value, 2, 1)
        test = _action_button("Testar som")
        test.clicked.connect(self.test_sound_requested)
        grid.addWidget(test, 2, 2)

        grid.setColumnStretch(1, 1)
        root.addWidget(card)
        root.addStretch(1)

    # ---- API para o Application preencher os valores ----
    def set_soundfont(self, path: str) -> None:
        self._soundfont_value.setText(path or "—")

    def set_audio_driver(self, driver: str) -> None:
        self._audio_value.setText(driver or "—")

    def set_midi_devices(self, names: list[str], current: str) -> None:
        """Popula o dropdown de dispositivos MIDI sem disparar sinais."""
        self._updating_combo = True
        self._midi_combo.clear()
        if not names:
            self._midi_combo.addItem("Nenhum teclado encontrado")
            self._midi_combo.setEnabled(False)
        else:
            self._midi_combo.setEnabled(True)
            self._midi_combo.addItems(names)
            if current in names:
                self._midi_combo.setCurrentIndex(names.index(current))
        self._updating_combo = False

    # ---- eventos internos ----
    def _choose_soundfont(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Escolher SoundFont",
            "/usr/share/sounds",
            "SoundFonts (*.sf2 *.sf3);;Todos os arquivos (*)",
        )
        if path:
            self.soundfont_chosen.emit(path)

    def _on_midi_changed(self, _index: int) -> None:
        if self._updating_combo or not self._midi_combo.isEnabled():
            return
        self.midi_device_selected.emit(self._midi_combo.currentText())
