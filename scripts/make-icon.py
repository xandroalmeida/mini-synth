#!/usr/bin/env python3
"""Gera um ícone simples localmente (sem imagens externas).

Desenha um teclado estilizado com QPainter e grava em ``assets/icon.png``.
Uso:  python scripts/make-icon.py
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QPainter, QPixmap  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

SIZE = 256


def draw_icon() -> QPixmap:
    pix = QPixmap(SIZE, SIZE)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # corpo arredondado escuro
    painter.setBrush(QColor("#191d27"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(QRectF(12, 12, SIZE - 24, SIZE - 24), 40, 40)

    # display âmbar no topo
    painter.setBrush(QColor("#ffb020"))
    painter.drawRoundedRect(QRectF(48, 52, SIZE - 96, 44), 12, 12)

    # teclas brancas
    keys_top = 120
    keys_h = 84
    white_w = (SIZE - 96) / 7
    painter.setBrush(QColor("#e8eef5"))
    for i in range(7):
        x = 48 + i * white_w
        painter.drawRoundedRect(QRectF(x + 2, keys_top, white_w - 4, keys_h), 4, 4)

    # teclas pretas
    painter.setBrush(QColor("#101319"))
    for i in (0, 1, 3, 4, 5):
        x = 48 + (i + 1) * white_w - white_w * 0.3
        painter.drawRoundedRect(QRectF(x, keys_top, white_w * 0.6, keys_h * 0.6), 3, 3)

    painter.end()
    return pix


def main() -> None:
    app = QApplication([])  # noqa: F841 (necessário para QPixmap)
    out_dir = Path(__file__).resolve().parents[1] / "assets"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / "icon.png"
    draw_icon().save(str(out))
    print(f"Ícone gerado em: {out}")


if __name__ == "__main__":
    main()
