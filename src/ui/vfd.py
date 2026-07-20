"""Display dot-matrix (VFD) desenhado ponto a ponto.

Renderiza texto como uma matriz de pontos 5x7 por caractere, com pontos acesos
brilhando (halo), pontos apagados como "fantasma", scanlines e reflexo de vidro
— para parecer um display real de equipamento de som dos anos 90.
"""

from __future__ import annotations

import unicodedata

from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from . import styles

# Fonte 5x7 (largura 5, altura 7). '#' = ponto aceso.
_FONT: dict[str, tuple[str, ...]] = {
    " ": ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
    "-": ("     ", "     ", "     ", "#####", "     ", "     ", "     "),
    "+": ("     ", "  #  ", "  #  ", "#####", "  #  ", "  #  ", "     "),
    ".": ("     ", "     ", "     ", "     ", "     ", " ##  ", " ##  "),
    ":": ("     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", "     "),
    "/": ("    #", "    #", "   # ", "  #  ", " #   ", "#    ", "#    "),
    "0": (" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "),
    "1": ("  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    "2": (" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
    "3": ("#####", "   # ", "  #  ", "   # ", "    #", "#   #", " ### "),
    "4": ("   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "),
    "5": ("#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "),
    "6": (" ### ", "#   #", "#    ", "#### ", "#   #", "#   #", " ### "),
    "7": ("#####", "    #", "   # ", "  #  ", " #   ", " #   ", " #   "),
    "8": (" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "),
    "9": (" ### ", "#   #", "#   #", " ####", "    #", "#   #", " ### "),
    "A": (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "B": ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    "C": (" ### ", "#   #", "#    ", "#    ", "#    ", "#   #", " ### "),
    "D": ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
    "E": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    "F": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    "G": (" ### ", "#   #", "#    ", "# ###", "#   #", "#   #", " ### "),
    "H": ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "I": (" ### ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    "J": ("  ###", "   # ", "   # ", "   # ", "#  # ", "#  # ", " ##  "),
    "K": ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    "L": ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    "M": ("#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"),
    "N": ("#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"),
    "O": (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "P": ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    "Q": (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    "R": ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    "S": (" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "V": ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
    "W": ("#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"),
    "X": ("#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"),
    "Y": ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    "Z": ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
}

_GLYPH_W = 5
_GLYPH_H = 7
_GAP = 1  # colunas de espaço entre caracteres (em unidades de ponto)


def _normalize(text: str) -> str:
    """Remove acentos e coloca em maiúsculas (displays 90s não tinham acento)."""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.upper()


class VfdDisplay(QWidget):
    """Widget que renderiza texto como matriz de pontos luminosa."""

    def __init__(
        self,
        min_chars: int = 6,
        max_dot: int = 8,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._raw = ""
        self._render = ""
        self._min_chars = min_chars
        self._max_dot = max_dot
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    # API compatível com QLabel usada pelo restante do código.
    def setText(self, text: str) -> None:  # noqa: N802 (API estilo Qt)
        self._raw = text
        self._render = _normalize(text)
        self.update()

    def text(self) -> str:
        return self._raw

    def minimumSizeHint(self) -> QSize:  # noqa: N802 (API Qt)
        dot = 3
        w = self._min_chars * (_GLYPH_W + _GAP) * dot + 16
        h = _GLYPH_H * dot + 14
        return QSize(w, h)

    def sizeHint(self) -> QSize:  # noqa: N802 (API Qt)
        dot = min(self._max_dot, 6)
        n = max(self._min_chars, len(self._render))
        w = n * (_GLYPH_W + _GAP) * dot + 20
        h = _GLYPH_H * dot + 16
        return QSize(w, h)

    def paintEvent(self, _event) -> None:  # noqa: N802 (API Qt)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # vidro do display (fundo verde-quase-preto)
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0.0, QColor("#0c1c17"))
        bg.setColorAt(1.0, QColor("#020d09"))
        p.fillRect(self.rect(), bg)

        text = self._render or ""
        n = max(1, len(text))
        pad = 8
        total_cols = n * _GLYPH_W + (n - 1) * _GAP
        avail_w = max(1, w - 2 * pad)
        avail_h = max(1, h - 2 * pad)
        dot = min(avail_w / total_cols, avail_h / _GLYPH_H, float(self._max_dot))
        dot = max(dot, 1.0)

        grid_w = total_cols * dot
        grid_h = _GLYPH_H * dot
        x0 = (w - grid_w) / 2
        y0 = (h - grid_h) / 2
        r = dot * 0.42

        on_color = QColor(styles.VFD_TEXT)
        off_color = QColor(styles.VFD_TEXT)
        off_color.setAlpha(26)
        glow = QColor(styles.VFD_GLOW)
        glow.setAlpha(110)

        p.setPen(Qt.PenStyle.NoPen)
        for ci, ch in enumerate(text):
            glyph = _FONT.get(ch, _FONT[" "])
            cx = x0 + ci * (_GLYPH_W + _GAP) * dot
            for row in range(_GLYPH_H):
                line = glyph[row]
                for col in range(_GLYPH_W):
                    dx = cx + col * dot + dot / 2
                    dy = y0 + row * dot + dot / 2
                    if line[col] == "#":
                        p.setBrush(glow)
                        p.drawEllipse(QPointF(dx, dy), r * 1.8, r * 1.8)
                        p.setBrush(on_color)
                        p.drawEllipse(QPointF(dx, dy), r, r)
                    else:
                        p.setBrush(off_color)
                        p.drawEllipse(QPointF(dx, dy), r * 0.8, r * 0.8)

        # scanlines horizontais
        p.setPen(QPen(QColor(0, 0, 0, 55), 1))
        y = 0
        while y < h:
            p.drawLine(0, y, w, y)
            y += 3

        # reflexo de vidro no topo
        refl = QLinearGradient(0, 0, 0, h * 0.55)
        refl.setColorAt(0.0, QColor(255, 255, 255, 24))
        refl.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.fillRect(0, 0, w, int(h * 0.55), refl)
