"""Elementos decorativos skeuomórficos (parafusos de painel)."""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget


class Screw(QWidget):
    """Um parafuso Phillips metálico embutido, como nos painéis de rack 90s."""

    def __init__(self, size: int = 22, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, _event) -> None:  # noqa: N802 (API Qt)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        s = self._size

        # cabeça metálica embutida (mais clara em cima, sombra embaixo)
        head = QRadialGradient(QPointF(s * 0.38, s * 0.34), s * 0.75)
        head.setColorAt(0.0, QColor("#eef1f3"))
        head.setColorAt(0.55, QColor("#b9bdc2"))
        head.setColorAt(1.0, QColor("#787c82"))
        p.setBrush(head)
        p.drawEllipse(1, 1, s - 2, s - 2)

        # anel de sombra interno (parafuso afundado)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(0, 0, 0, 70), 1.5))
        p.drawEllipse(2, 2, s - 4, s - 4)

        # fenda em cruz (Phillips)
        cx = cy = s / 2
        arm = s * 0.28
        p.setPen(QPen(QColor(40, 43, 47, 220), max(2, int(s * 0.11))))
        p.drawLine(QPointF(cx - arm, cy), QPointF(cx + arm, cy))
        p.drawLine(QPointF(cx, cy - arm), QPointF(cx, cy + arm))

        # leve reflexo na fenda
        p.setPen(QPen(QColor(255, 255, 255, 60), 1))
        p.drawLine(QPointF(cx - arm, cy - 1), QPointF(cx + arm, cy - 1))
