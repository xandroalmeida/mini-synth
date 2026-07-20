"""Painel de controles físicos: Volume, Reverb, Oitava e Parar Som."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .buttons import PanelButton
from .vfd import VfdDisplay


def _physical_button(text: str, width: int = 52) -> PanelButton:
    btn = PanelButton(text, role="dark", font_size=24)
    btn.setMinimumSize(width, 52)
    btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    return btn


class _Control(QFrame):
    """Um controle com rótulo, valor central e botões -/+ (e opcional '0')."""

    def __init__(self, caption: str, with_reset: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.setProperty("class", "Card")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 10)
        outer.setSpacing(6)

        label = QLabel(caption)
        label.setProperty("class", "ControlLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        outer.addWidget(label)

        row = QHBoxLayout()
        row.setSpacing(3)

        self.minus = _physical_button("−")
        # mostrador dot-matrix (até 3 caracteres: "100", "+1", "-2")
        self.value = VfdDisplay(min_chars=3, max_dot=6)
        self.value.setMinimumWidth(72)
        self.value.setMinimumHeight(40)
        self.plus = _physical_button("+")

        row.addWidget(self.minus, 1)
        if with_reset:
            self.reset = _physical_button("0")
            row.addWidget(self.value, 2)
            row.addWidget(self.reset, 1)
        else:
            self.reset = None
            row.addWidget(self.value, 2)
        row.addWidget(self.plus, 1)
        outer.addLayout(row)

    def set_value(self, text: str) -> None:
        self.value.setText(text)


class ControlPanel(QWidget):
    """Reúne Volume, Reverb, Oitava e o botão PARAR SOM."""

    volume_up = Signal()
    volume_down = Signal()
    reverb_up = Signal()
    reverb_down = Signal()
    octave_up = Signal()
    octave_down = Signal()
    octave_reset = Signal()
    panic = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        controls = QHBoxLayout()
        controls.setSpacing(10)

        self._volume = _Control("VOLUME")
        self._reverb = _Control("REVERB")
        self._octave = _Control("OITAVA", with_reset=True)

        controls.addWidget(self._volume)
        controls.addWidget(self._reverb)
        controls.addWidget(self._octave)
        root.addLayout(controls)

        self.panic_button = PanelButton("PARAR SOM", role="panic", font_size=24)
        self.panic_button.setMinimumHeight(60)
        root.addWidget(self.panic_button)

        # ligações
        self._volume.plus.clicked.connect(self.volume_up)
        self._volume.minus.clicked.connect(self.volume_down)
        self._reverb.plus.clicked.connect(self.reverb_up)
        self._reverb.minus.clicked.connect(self.reverb_down)
        self._octave.plus.clicked.connect(self.octave_up)
        self._octave.minus.clicked.connect(self.octave_down)
        if self._octave.reset is not None:
            self._octave.reset.clicked.connect(self.octave_reset)
        self.panic_button.clicked.connect(self.panic)

    # ---- atualização dos mostradores ----
    def set_volume(self, value: int) -> None:
        self._volume.set_value(str(value))

    def set_reverb(self, value: int) -> None:
        self._reverb.set_value(str(value))

    def set_octave(self, value: int) -> None:
        self._octave.set_value(f"{value:+d}" if value else "0")
