"""Janela principal — o painel do "mini teclado".

Sem barra de menus, sem menu File/Edit, sem dropdowns na tela principal.
Usa um ``QStackedWidget`` para alternar entre o painel principal, a tela de
CONFIG e uma tela de erro amigável — tudo com a mesma aparência de painel.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..config.models import AppConfig, Bank, Instrument
from .buttons import PanelButton
from .control_panel import ControlPanel
from .decorations import Screw
from .instrument_button import InstrumentButton
from .settings_window import SettingsPage
from .status_indicator import StatusIndicator
from .vfd import VfdDisplay

# Índices das páginas do QStackedWidget.
PAGE_MAIN = 0
PAGE_SETTINGS = 1
PAGE_ERROR = 2


class MainWindow(QWidget):
    """A tela do instrumento. O :class:`Application` faz toda a fiação."""

    instrument_selected = Signal(Instrument)
    bank_selected = Signal(str)  # id do banco
    config_requested = Signal()
    retry_requested = Signal()

    def __init__(self, config: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._buttons: dict[str, InstrumentButton] = {}
        self._bank_buttons: dict[str, PanelButton] = {}
        self._bank_pages: dict[str, int] = {}

        self.setObjectName("RootPanel")
        self.setWindowTitle("Mini Synth")
        self.setMinimumSize(900, 540)

        self._stack = QStackedWidget(self)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._stack)

        self._stack.addWidget(self._build_main_page())      # PAGE_MAIN
        self.settings_page = SettingsPage()
        self._stack.addWidget(self.settings_page)           # PAGE_SETTINGS
        self._stack.addWidget(self._build_error_page())     # PAGE_ERROR

        self.settings_page.back_requested.connect(self.show_main)

    # ------------------------------------------------------------------
    # construção das páginas
    # ------------------------------------------------------------------
    def _build_main_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_display())
        layout.addWidget(self._build_bank_tabs())
        layout.addWidget(self._build_instrument_stack(), stretch=1)
        self.control_panel = ControlPanel()
        layout.addWidget(self.control_panel)
        return page

    def _build_header(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("HeaderBar")
        row = QHBoxLayout(bar)
        row.setContentsMargins(16, 12, 16, 12)
        row.setSpacing(14)

        row.addWidget(Screw(), 0, Qt.AlignmentFlag.AlignVCenter)

        title = QLabel("MINI SYNTH")
        title.setObjectName("Title")
        row.addWidget(title)
        row.addStretch(1)

        self.midi_indicator = StatusIndicator("MIDI")
        self.audio_indicator = StatusIndicator("ÁUDIO")
        row.addWidget(self.midi_indicator)
        row.addSpacing(18)
        row.addWidget(self.audio_indicator)
        row.addSpacing(20)

        self.config_button = PanelButton("CONFIG", role="metal", font_size=15)
        self.config_button.setMinimumSize(120, 46)
        self.config_button.clicked.connect(self.config_requested)
        row.addWidget(self.config_button)
        row.addWidget(Screw(), 0, Qt.AlignmentFlag.AlignVCenter)
        return bar

    def _build_display(self) -> QWidget:
        card = QFrame()
        card.setObjectName("DisplayCard")
        box = QVBoxLayout(card)
        box.setContentsMargins(14, 10, 14, 12)
        box.setSpacing(4)

        caption = QLabel("INSTRUMENTO ATUAL")
        caption.setObjectName("DisplayLabel")

        # Visor dot-matrix real (matriz de pontos 5x7).
        self.display_value = VfdDisplay(min_chars=8, max_dot=9)
        self.display_value.setMinimumHeight(64)

        box.addWidget(caption)
        box.addWidget(self.display_value, stretch=1)
        return card

    def _build_bank_tabs(self) -> QWidget:
        """Fileira de bancos (A1). Sempre visível; um toque troca de banco."""
        bar = QFrame()
        bar.setObjectName("BankTabs")
        row = QHBoxLayout(bar)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(8)
        for bank in self._config.banks:
            # role="dark": a aba do banco ATIVO acende em âmbar (como os
            # instrumentos), deixando claro qual banco está selecionado.
            btn = PanelButton(bank.label, role="dark", font_size=14)
            btn.setMinimumHeight(42)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            btn.clicked.connect(lambda _=False, bid=bank.id: self.bank_selected.emit(bid))
            self._bank_buttons[bank.id] = btn
            row.addWidget(btn)
        return bar

    def _build_instrument_stack(self) -> QWidget:
        """Uma página de grade por banco; só a do banco atual fica visível."""
        self._grid_stack = QStackedWidget()
        for index, bank in enumerate(self._config.banks):
            self._grid_stack.addWidget(self._build_bank_grid(bank))
            self._bank_pages[bank.id] = index
        return self._grid_stack

    def _build_bank_grid(self, bank: Bank) -> QWidget:
        card = QFrame()
        card.setObjectName("ControlsCard")
        grid = QGridLayout(card)
        grid.setContentsMargins(16, 14, 16, 14)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(12)

        columns = max(1, self._config.interface.columns)
        for i, instrument in enumerate(bank.instruments):
            button = InstrumentButton(instrument)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            button.selected.connect(self.instrument_selected)
            self._buttons[instrument.id] = button
            grid.addWidget(button, i // columns, i % columns)
        return card

    def _build_error_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(24)
        layout.addStretch(1)

        self._error_title = QLabel("Ops!")
        self._error_title.setObjectName("ErrorTitle")
        self._error_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._error_message = QLabel("")
        self._error_message.setObjectName("ErrorMessage")
        self._error_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_message.setWordWrap(True)

        self._retry_button = PanelButton("TENTAR NOVAMENTE", role="metal", font_size=20)
        self._retry_button.setMinimumSize(320, 74)
        self._retry_button.clicked.connect(self.retry_requested)

        layout.addWidget(self._error_title)
        layout.addWidget(self._error_message)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self._retry_button)
        row.addStretch(1)
        layout.addLayout(row)
        layout.addStretch(2)
        return page

    # ------------------------------------------------------------------
    # API usada pelo Application
    # ------------------------------------------------------------------
    def set_current_instrument(self, instrument: Instrument) -> None:
        self.display_value.setText(instrument.display_name.upper())
        for inst_id, button in self._buttons.items():
            button.set_selected(inst_id == instrument.id)

    def set_current_bank(self, bank: Bank) -> None:
        """Acende a aba do banco e mostra a grade dele."""
        for bank_id, button in self._bank_buttons.items():
            button.setSelected(bank_id == bank.id)
        index = self._bank_pages.get(bank.id)
        if index is not None:
            self._grid_stack.setCurrentIndex(index)

    def set_midi_status(self, state: str, message: str) -> None:
        self.midi_indicator.set_state(state, message)

    def set_audio_status(self, state: str, message: str = "") -> None:
        self.audio_indicator.set_state(state, message)

    def show_main(self) -> None:
        self._stack.setCurrentIndex(PAGE_MAIN)

    def show_settings(self) -> None:
        self._stack.setCurrentIndex(PAGE_SETTINGS)

    def show_error(self, message: str, *, retryable: bool = True) -> None:
        self._error_message.setText(message)
        self._retry_button.setVisible(retryable)
        self._stack.setCurrentIndex(PAGE_ERROR)

    def is_on_error_page(self) -> bool:
        return self._stack.currentIndex() == PAGE_ERROR

    # ------------------------------------------------------------------
    # tela cheia
    # ------------------------------------------------------------------
    def toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 (API Qt)
        if event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.showNormal()
        elif event.key() == Qt.Key.Key_F11:
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)
