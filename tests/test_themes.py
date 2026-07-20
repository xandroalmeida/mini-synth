"""Testes da arquitetura de temas visuais da interface web."""

from __future__ import annotations

from pathlib import Path

from src.config import loader
from src.ui.themes import DEFAULT_THEME, normalize_theme, theme_options
from src.ui.web_bridge import WebUiBridge


WEB_DIR = Path(__file__).resolve().parents[1] / "assets" / "web"


class _FakeWindow:
    def __init__(self) -> None:
        self.scripts: list[str] = []

    def evaluate_js(self, script: str) -> None:
        self.scripts.append(script)


def test_theme_registry_has_default_and_tube60() -> None:
    options = theme_options()
    assert options[0]["id"] == DEFAULT_THEME == "ms90"
    assert {option["id"] for option in options} == {"ms90", "tube60"}


def test_invalid_theme_falls_back_to_default() -> None:
    assert normalize_theme("desconhecido") == DEFAULT_THEME
    assert normalize_theme("") == DEFAULT_THEME


def test_bridge_initializes_with_saved_theme() -> None:
    bridge = WebUiBridge(loader.load_app_config(), "tube60")
    window = _FakeWindow()
    bridge.attach(window)

    bridge.init_ui()

    assert bridge.theme_id == "tube60"
    assert any('"theme": "tube60"' in script for script in window.scripts)
    assert any('"id": "ms90"' in script for script in window.scripts)
    assert any('"id": "tube60"' in script for script in window.scripts)


def test_bridge_switches_theme_and_sanitizes_unknown_id() -> None:
    bridge = WebUiBridge(loader.load_app_config())
    window = _FakeWindow()
    bridge.attach(window)

    assert bridge.set_theme("tube60") == "tube60"
    assert window.scripts[-1] == 'MS.setTheme("tube60")'

    assert bridge.set_theme("../../invalido") == DEFAULT_THEME
    assert window.scripts[-1] == 'MS.setTheme("ms90")'


def test_api_emits_selected_theme() -> None:
    bridge = WebUiBridge(loader.load_app_config())
    selected: list[str] = []
    bridge.settings_page.theme_selected.connect(selected.append)

    bridge.api.select_theme("tube60")

    assert selected == ["tube60"]


def test_each_theme_has_an_independent_template_and_stylesheet() -> None:
    themes_dir = WEB_DIR / "themes"
    for theme_id in ("ms90", "tube60"):
        theme_dir = themes_dir / theme_id
        assert (theme_dir / "AGENTS.md").is_file()
        assert (theme_dir / "template.js").is_file()
        assert (theme_dir / "style.css").is_file()


def test_tube60_is_structurally_different_from_ms90() -> None:
    themes_dir = WEB_DIR / "themes"
    ms90 = (themes_dir / "ms90" / "template.js").read_text(encoding="utf-8")
    tube60 = (themes_dir / "tube60" / "template.js").read_text(encoding="utf-8")

    assert "rack-footer" in ms90
    assert "speaker-cone" not in ms90
    assert "speaker-cone" in tube60
    assert "valve-window" in tube60
    assert "tube-control-deck" in tube60
    assert "service-grid" in tube60
    assert "<canvas" in ms90
    assert "<canvas" not in tube60
    assert 'data-indicator="mechanical"' in tube60
    assert 'data-indicator="analog"' in tube60
    assert "voice-drum" in tube60


def test_tube60_mechanical_selector_has_motion_and_position_feedback() -> None:
    app = (WEB_DIR / "app.js").read_text(encoding="utf-8")
    tube_css = (WEB_DIR / "themes" / "tube60" / "style.css").read_text(encoding="utf-8")

    assert "rollMechanicalIndicator" in app
    assert "updateMechanicalSelector" in app
    assert "mark.getBoundingClientRect()" in app
    assert "rolling-forward" in tube_css
    assert "rolling-backward" in tube_css
    assert "transition:left" in tube_css


def test_index_is_only_the_shared_theme_host() -> None:
    index = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    assert '<main id="app-shell"></main>' in index
    assert "themes/ms90/template.js" in index
    assert "themes/tube60/template.js" in index
