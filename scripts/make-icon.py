#!/usr/bin/env python3
"""Gera um ícone simples localmente (sem imagens externas).

Desenha um teclado estilizado com Pillow e grava em ``assets/icon.png``.
Uso:  python scripts/make-icon.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 256
#: Fator de supersampling: desenha grande e reduz com LANCZOS para suavizar as
#: bordas (o Pillow não faz antialiasing de formas nativamente).
SS = 4


def draw_icon() -> Image.Image:
    s = SIZE * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def rrect(x: float, y: float, w: float, h: float, r: float, fill: str) -> None:
        d.rounded_rectangle(
            [x * SS, y * SS, (x + w) * SS, (y + h) * SS],
            radius=r * SS,
            fill=fill,
        )

    # corpo arredondado escuro
    rrect(12, 12, SIZE - 24, SIZE - 24, 40, "#191d27")

    # display âmbar no topo
    rrect(48, 52, SIZE - 96, 44, 12, "#ffb020")

    # teclas brancas
    keys_top = 120
    keys_h = 84
    white_w = (SIZE - 96) / 7
    for i in range(7):
        x = 48 + i * white_w
        rrect(x + 2, keys_top, white_w - 4, keys_h, 4, "#e8eef5")

    # teclas pretas
    for i in (0, 1, 3, 4, 5):
        x = 48 + (i + 1) * white_w - white_w * 0.3
        rrect(x, keys_top, white_w * 0.6, keys_h * 0.6, 3, "#101319")

    return img.resize((SIZE, SIZE), Image.LANCZOS)


def main() -> None:
    out_dir = Path(__file__).resolve().parents[1] / "assets"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / "icon.png"
    draw_icon().save(str(out))
    print(f"Ícone gerado em: {out}")


if __name__ == "__main__":
    main()
