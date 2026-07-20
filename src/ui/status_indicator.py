"""Indicador de status tipo LED (verde / amarelo / vermelho).

Desenhado à mão para parecer um LED real de painel dos anos 90: anel metálico,
domo de vidro colorido com brilho (halo) e reflexo especular.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QRadialGradient
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from . import styles

_STATE_COLORS = {
    "connected": styles.GREEN,
    "searching": styles.YELLOW,
    "error": styles.RED,
    "idle": "#5a5f66",
}


class _Led(QWidget):
    """LED com bezel metálico, domo de vidro e reflexo."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = QColor(_STATE_COLORS["idle"])
        self.setFixedSize(26, 26)

    def set_color(self, color_hex: str) -> None:
        self._color = QColor(color_hex)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802 (API Qt)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)

        # halo luminoso ao redor
        halo = QRadialGradient(QPointF(13, 13), 13)
        glow = QColor(self._color)
        glow.setAlpha(140)
        halo.setColorAt(0.0, glow)
        halo.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(halo)
        p.drawEllipse(0, 0, 26, 26)

        # anel metálico (bezel)
        bezel = QRadialGradient(QPointF(10, 9), 16)
        bezel.setColorAt(0.0, QColor("#d9dde1"))
        bezel.setColorAt(1.0, QColor("#4b4f55"))
        p.setBrush(bezel)
        p.drawEllipse(3, 3, 20, 20)

        # domo de vidro colorido
        dome = QRadialGradient(QPointF(11, 10), 12)
        bright = QColor(self._color).lighter(150)
        dome.setColorAt(0.0, bright)
        dome.setColorAt(0.6, self._color)
        dome.setColorAt(1.0, QColor(self._color).darker(180))
        p.setBrush(dome)
        p.drawEllipse(6, 6, 14, 14)

        # reflexo especular
        p.setBrush(QColor(255, 255, 255, 190))
        p.drawEllipse(9, 8, 5, 4)


class StatusIndicator(QWidget):
    """Rótulo + LED que mostra o estado de MIDI ou áudio."""

    def __init__(self, caption: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._caption = QLabel(caption)
        self._caption.setProperty("class", "ControlLabel")
        self._led = _Led()

        layout.addWidget(self._caption)
        layout.addWidget(self._led)
        self.set_state("idle")

    def set_state(self, state: str, tooltip: str = "") -> None:
        self._led.set_color(_STATE_COLORS.get(state, _STATE_COLORS["idle"]))
        if tooltip:
            self.setToolTip(tooltip)
