"""Botões físicos desenhados à mão (skeuomorfismo real).

Nada de ``border: outset`` do Qt (que fica chapado). Cada botão é pintado com
QPainter: sombra projetada por baixo (levanta o botão da superfície), corpo com
gradiente convexo, reflexo especular no topo, contorno com bisel e texto em
relevo. Ao pressionar, o botão "afunda" (sombra some e conteúdo desce).
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QAbstractButton, QWidget


@dataclass(frozen=True)
class _Skin:
    top: str
    mid: str
    bot: str
    border_hi: str
    border_lo: str
    text: str
    text_shadow: tuple[int, int, int, int]  # RGBA do relevo do texto
    shadow_dy: int                            # deslocamento do relevo do texto
    gloss: int                                # alpha do brilho especular
    glow: str | None = None                   # halo (selecionado / pânico)


_SKINS: dict[str, _Skin] = {
    # botão escuro (gunmetal) — instrumentos e +/-
    "dark": _Skin(
        top="#828892", mid="#4b515a", bot="#262a31",
        border_hi="#969ca6", border_lo="#0e1013",
        text="#eef2f6", text_shadow=(0, 0, 0, 170), shadow_dy=1, gloss=60,
    ),
    # botão aceso (instrumento selecionado) — retroiluminação âmbar
    "amber": _Skin(
        top="#ffe08a", mid="#ffb62c", bot="#d5860a",
        border_hi="#fff0c0", border_lo="#7a4d00",
        text="#2a1600", text_shadow=(255, 240, 200, 90), shadow_dy=-1, gloss=120,
        glow="#ffbe3a",
    ),
    # botão vermelho grande (PARAR SOM)
    "panic": _Skin(
        top="#ff9a82", mid="#ec4636", bot="#a01a0e",
        border_hi="#ffc0b2", border_lo="#5c0d04",
        text="#2c0500", text_shadow=(255, 210, 200, 70), shadow_dy=-1, gloss=90,
        glow="#ff5236",
    ),
    # botão de metal claro (CONFIG / VOLTAR / ações da config)
    "metal": _Skin(
        top="#f4f6f8", mid="#d4d8dc", bot="#a9afb5",
        border_hi="#ffffff", border_lo="#82888f",
        text="#24272c", text_shadow=(255, 255, 255, 150), shadow_dy=-1, gloss=150,
    ),
}


class PanelButton(QAbstractButton):
    """Botão físico pintado à mão. Reutilizável por papel (``role``)."""

    def __init__(
        self,
        text: str = "",
        role: str = "dark",
        font_size: int = 18,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._role = role
        self._selected = False
        self.setText(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        font = QFont("DejaVu Sans")
        font.setPixelSize(font_size)
        font.setWeight(QFont.Weight.ExtraBold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.0)
        self.setFont(font)
        # repinta ao pressionar/soltar
        self.pressed.connect(self.update)
        self.released.connect(self.update)

    # ---- estado de seleção (iluminação) ----
    def setSelected(self, on: bool) -> None:  # noqa: N802 (API estilo Qt)
        if self._selected != on:
            self._selected = on
            self.update()

    def isSelected(self) -> bool:  # noqa: N802
        return self._selected

    def _skin(self) -> _Skin:
        if self._selected and self._role == "dark":
            return _SKINS["amber"]
        return _SKINS[self._role]

    def sizeHint(self) -> QSize:  # noqa: N802
        fm = self.fontMetrics()
        w = fm.horizontalAdvance(self.text()) + 44
        h = fm.height() + 30
        return QSize(max(w, 90), max(h, 52))

    # ---- pintura ----
    def paintEvent(self, _event) -> None:  # noqa: N802 (API Qt)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        skin = self._skin()
        pressed = self.isDown()

        rect = QRectF(self.rect())
        # geometria do corpo: reserva espaço embaixo para a sombra projetada
        # (mantida curta para NÃO vazar sobre o botão de baixo)
        top_in = 3.0 if not pressed else 5.0
        bot_in = 8.0 if not pressed else 6.0
        body = QRectF(
            rect.left() + 3,
            rect.top() + top_in,
            rect.width() - 6,
            rect.height() - top_in - bot_in,
        )
        if body.height() < 6 or body.width() < 6:
            return
        radius = min(14.0, body.height() * 0.30)

        # 1) sombra projetada (só quando não pressionado) — 3 camadas = "blur"
        if not pressed:
            p.setPen(Qt.PenStyle.NoPen)
            for dy, alpha in ((2, 85), (4, 50), (6, 26)):
                p.setBrush(QColor(0, 0, 0, alpha))
                p.drawRoundedRect(body.translated(0, dy), radius, radius)

        # 2) halo (selecionado / pânico)
        if skin.glow is not None:
            p.setPen(Qt.PenStyle.NoPen)
            for gw, alpha in ((7, 55), (3, 95)):
                gc = QColor(skin.glow)
                gc.setAlpha(alpha)
                p.setBrush(gc)
                p.drawRoundedRect(
                    body.adjusted(-gw, -gw, gw, gw), radius + gw, radius + gw
                )

        # 3) corpo com gradiente convexo (claro em cima, escuro embaixo)
        grad = QLinearGradient(body.topLeft(), body.bottomLeft())
        grad.setColorAt(0.0, QColor(skin.top))
        grad.setColorAt(0.5, QColor(skin.mid))
        grad.setColorAt(1.0, QColor(skin.bot))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawRoundedRect(body, radius, radius)

        # 4) reflexo especular no topo (recortado pelo corpo)
        path = QPainterPath()
        path.addRoundedRect(body, radius, radius)
        p.save()
        p.setClipPath(path)
        gloss = QRectF(body.left(), body.top(), body.width(), body.height() * 0.48)
        gg = QLinearGradient(gloss.topLeft(), gloss.bottomLeft())
        gg.setColorAt(0.0, QColor(255, 255, 255, skin.gloss))
        gg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(gg)
        p.drawRect(gloss)
        p.restore()

        # 5) contorno com bisel: aro escuro externo + fio de luz interno no topo
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(skin.border_lo), 1.4))
        p.drawRoundedRect(body, radius, radius)
        p.setClipPath(path)
        hi = QColor(skin.border_hi)
        hi.setAlpha(220)
        p.setPen(QPen(hi, 1.4))
        p.drawRoundedRect(body.adjusted(1.2, 1.2, -1.2, -1.2), radius, radius)
        p.setClipping(False)

        # 6) texto em relevo
        text_rect = body
        if pressed:
            text_rect = body.translated(0, 1)
        p.setFont(self.font())
        p.setPen(QColor(*skin.text_shadow))
        p.drawText(
            text_rect.translated(0, skin.shadow_dy),
            Qt.AlignmentFlag.AlignCenter,
            self.text(),
        )
        p.setPen(QColor(skin.text))
        p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text())
