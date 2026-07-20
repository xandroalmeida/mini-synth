"""Botão grande de instrumento — botão físico pintado à mão."""

from __future__ import annotations

from PySide6.QtCore import Signal

from ..config.models import Instrument
from . import styles
from .buttons import PanelButton


class InstrumentButton(PanelButton):
    """Botão que representa um instrumento selecionável.

    Emite :attr:`selected` com o :class:`Instrument` ao ser clicado. Fica
    "iluminado" (retroiluminação âmbar) quando é o instrumento ativo.
    """

    selected = Signal(Instrument)

    def __init__(self, instrument: Instrument, parent=None) -> None:
        super().__init__(instrument.label, role="dark", font_size=17, parent=parent)
        self._instrument = instrument
        self.setMinimumSize(styles.MIN_BUTTON_W, styles.MIN_BUTTON_H)
        self.clicked.connect(self._on_clicked)

    @property
    def instrument(self) -> Instrument:
        return self._instrument

    def _on_clicked(self) -> None:
        self.selected.emit(self._instrument)

    def set_selected(self, is_selected: bool) -> None:
        """Liga/desliga a retroiluminação do botão."""
        self.setSelected(is_selected)
