"""Registro dos temas visuais disponíveis para a interface web."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UiTheme:
    id: str
    label: str


THEMES: tuple[UiTheme, ...] = (
    UiTheme("ms90", "Digital MS-90 · Anos 90"),
    UiTheme("tube60", "Valvulado Hi-Fi · Anos 60"),
)
DEFAULT_THEME = THEMES[0].id
_THEME_IDS = frozenset(theme.id for theme in THEMES)


def normalize_theme(theme_id: str | None) -> str:
    """Retorna um ID conhecido, usando o tema padrão para valores inválidos."""
    candidate = str(theme_id or "")
    return candidate if candidate in _THEME_IDS else DEFAULT_THEME


def theme_options() -> list[dict[str, str]]:
    return [{"id": theme.id, "label": theme.label} for theme in THEMES]
