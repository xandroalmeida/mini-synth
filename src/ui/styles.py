"""Paleta e folhas de estilo (Qt Style Sheets).

Estética: **skeuomorfismo de equipamento de som dos anos 90** — faceplate de
alumínio escovado, visor VFD (fluorescente) brilhando, botões chapados com
bisel 3D (outset/inset), LEDs com brilho. Tudo em QSS, sem imagens externas.
"""

from __future__ import annotations

# ---- paleta --------------------------------------------------------------
# Alumínio / metal escovado
METAL_HI = "#e9ecef"
METAL = "#c9cdd2"
METAL_LO = "#a7abb1"
METAL_EDGE = "#6f747b"

# Corpo / plástico escuro (gunmetal)
GUN_HI = "#5b616b"
GUN = "#3f444d"
GUN_LO = "#2a2e35"
GUN_EDGE = "#14161a"

# Visor VFD (fluorescente verde-ciano típico dos anos 90)
VFD_BG_HI = "#0c1a17"
VFD_BG_LO = "#03110d"
VFD_TEXT = "#8dffe0"
VFD_GLOW = "#3fe0b8"
VFD_DIM = "#2a7a68"

TEXT = "#eef2f5"
TEXT_DARK = "#26292e"      # texto "gravado" sobre metal
TEXT_DIM = "#8b919a"

# Botão de instrumento aceso (retroiluminação âmbar)
AMBER = "#ffb320"
AMBER_HI = "#ffd873"
AMBER_LO = "#c77f00"

# LEDs
GREEN = "#54e08a"
YELLOW = "#ffcf3f"
RED = "#ff5a4d"

# Tamanho mínimo de área de clique (touchscreen-friendly, mas responsivo).
MIN_BUTTON_W = 92
MIN_BUTTON_H = 58


# ---- helpers de gradiente ------------------------------------------------
def _brushed(c_hi: str, c_lo: str, bands: int = 46) -> str:
    """Gradiente vertical com estrias finas — imita metal escovado."""
    stops = []
    for i in range(bands + 1):
        pos = i / bands
        stops.append(f"stop:{pos:.4f} {c_hi if i % 2 == 0 else c_lo}")
    return "qlineargradient(x1:0, y1:0, x2:0, y2:1, " + ", ".join(stops) + ")"


def _curved(c_top: str, c_mid: str, c_bot: str) -> str:
    """Gradiente vertical liso — superfície metálica curva (reflexo)."""
    return (
        "qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        f"stop:0 {c_top}, stop:0.14 {c_top}, stop:0.5 {c_mid}, "
        f"stop:0.86 {c_bot}, stop:1 {c_bot})"
    )


def app_stylesheet() -> str:
    """QSS global aplicado à QApplication."""
    metal_body = _brushed(METAL_HI, METAL)
    metal_strip = _brushed("#c4c8cd", "#b0b4ba")
    gun_face = _curved(GUN_HI, GUN, GUN_LO)
    gun_press = _curved(GUN_LO, GUN, GUN_HI)
    amber_face = _curved(AMBER_HI, AMBER, AMBER_LO)
    vfd = _curved(VFD_BG_HI, VFD_BG_LO, "#020c09")

    return f"""
    QWidget {{
        background-color: {METAL};
        color: {TEXT_DARK};
        font-family: "DejaVu Sans", "Noto Sans", "Sans Serif";
        font-size: 18px;
    }}

    /* ===== corpo do aparelho (faceplate de alumínio escovado) ===== */
    #RootPanel {{
        background: {metal_body};
    }}

    /* faixa superior tipo painel de amplificador */
    #HeaderBar {{
        background: {metal_strip};
        border: 2px groove {METAL_HI};
        border-radius: 8px;
    }}

    #Title {{
        color: {TEXT_DARK};
        font-size: 26px;
        font-weight: 800;
        letter-spacing: 4px;
    }}

    /* ===== visor VFD (o painel escuro luminoso) ===== */
    #DisplayCard {{
        background: {vfd};
        border: 4px inset #05100d;
        border-radius: 10px;
    }}
    #DisplayLabel {{
        color: {VFD_DIM};
        font-family: "DejaVu Sans Mono", monospace;
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 4px;
    }}
    #DisplayValue {{
        color: {VFD_TEXT};
        font-family: "DejaVu Sans Mono", monospace;
        font-size: 44px;
        font-weight: 800;
        letter-spacing: 2px;
    }}

    /* ===== área dos botões (painel rebaixado) ===== */
    #ControlsCard {{
        background: {_brushed("#bdc1c6", "#adb1b7")};
        border: 3px inset {METAL_EDGE};
        border-radius: 10px;
    }}
    .Card {{
        background: {_brushed("#bdc1c6", "#adb1b7")};
        border: 2px groove {METAL_HI};
        border-radius: 8px;
    }}

    /* ===== botões de instrumento (teclas chapadas gunmetal) ===== */
    InstrumentButton {{
        background: {gun_face};
        border: 4px outset {GUN_HI};
        border-radius: 9px;
        color: {TEXT};
        font-size: 17px;
        font-weight: 800;
        letter-spacing: 1px;
        padding: 4px;
    }}
    InstrumentButton:pressed {{
        background: {gun_press};
        border-style: inset;
    }}
    InstrumentButton[selected="true"] {{
        background: {amber_face};
        border: 4px outset {AMBER_HI};
        color: #2a1600;
    }}

    /* ===== botões físicos genéricos (+/- do painel) ===== */
    QPushButton.Physical {{
        background: {gun_face};
        border: 4px outset {GUN_HI};
        border-radius: 10px;
        color: {TEXT};
        font-size: 24px;
        font-weight: 800;
        padding: 6px 14px;
    }}
    QPushButton.Physical:pressed {{
        background: {gun_press};
        border-style: inset;
    }}

    /* ===== botão PARAR SOM (grande, vermelho, chapado) ===== */
    QPushButton#PanicButton {{
        background: {_curved("#ff7a63", "#e63b2c", "#a51d13")};
        border: 4px outset #ff8f7a;
        border-radius: 12px;
        color: #2a0400;
        font-size: 22px;
        font-weight: 900;
        letter-spacing: 3px;
        padding: 6px;
    }}
    QPushButton#PanicButton:pressed {{
        background: {_curved("#a51d13", "#e63b2c", "#ff7a63")};
        border-style: inset;
    }}

    /* ===== botões pequenos CONFIG / VOLTAR (metal) ===== */
    QPushButton#ConfigButton, QPushButton#BackButton {{
        background: {_curved("#dfe2e6", "#c3c7cc", "#a9adb3")};
        border: 3px outset {METAL_HI};
        border-radius: 8px;
        color: {TEXT_DARK};
        font-size: 15px;
        font-weight: 800;
        letter-spacing: 2px;
        padding: 8px 14px;
    }}
    QPushButton#ConfigButton:pressed, QPushButton#BackButton:pressed {{
        background: {_curved("#a9adb3", "#c3c7cc", "#dfe2e6")};
        border-style: inset;
    }}

    /* ===== rótulos gravados no metal ===== */
    .ControlLabel {{
        color: {TEXT_DARK};
        font-size: 14px;
        font-weight: 800;
        letter-spacing: 3px;
    }}
    /* mostrador de valor tipo mini-LCD */
    .ControlValue {{
        background: {vfd};
        border: 3px inset #05100d;
        border-radius: 6px;
        color: {VFD_TEXT};
        font-family: "DejaVu Sans Mono", monospace;
        font-size: 28px;
        font-weight: 800;
        padding: 2px 6px;
    }}

    /* ===== tela de configuração ===== */
    #SettingsTitle {{
        color: {TEXT_DARK};
        font-size: 26px;
        font-weight: 800;
        letter-spacing: 3px;
    }}
    #SettingsField {{
        color: {TEXT_DARK};
        font-size: 14px;
        font-weight: 800;
        letter-spacing: 2px;
    }}
    #SettingsValue {{
        background: {vfd};
        border: 3px inset #05100d;
        border-radius: 6px;
        color: {VFD_TEXT};
        font-family: "DejaVu Sans Mono", monospace;
        font-size: 18px;
        font-weight: 700;
        padding: 8px 10px;
    }}
    QComboBox {{
        background: {gun_face};
        border: 3px outset {GUN_HI};
        border-radius: 8px;
        color: {TEXT};
        padding: 8px 12px;
        font-size: 18px;
        min-height: 30px;
    }}
    QComboBox::drop-down {{ border: none; width: 26px; }}
    QComboBox QAbstractItemView {{
        background: {GUN};
        color: {TEXT};
        selection-background-color: {AMBER};
        selection-color: #2a1600;
    }}

    /* ===== caixa de erro ===== */
    #ErrorTitle {{
        color: #b52a1c;
        font-size: 26px;
        font-weight: 900;
        letter-spacing: 2px;
    }}
    #ErrorMessage {{
        color: {TEXT_DARK};
        font-size: 20px;
        font-weight: 600;
    }}
    """
