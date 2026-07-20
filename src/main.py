"""Ponto de entrada. Execute com ``python -m src.main`` ou ``./run.sh``.

Interface em pywebview (backend GTK/WebKit): a janela carrega ``assets/web`` e
o :class:`~src.ui.web_bridge.WebUiBridge` faz a ponte com o núcleo Python. Sem
Qt — o pacote fica muito mais leve.
"""

from __future__ import annotations

import logging
import os
import signal
import sys
from html import escape
from logging.handlers import RotatingFileHandler
from pathlib import Path

import webview

from .application import Application
from .config import loader
from .config.models import ConfigError

logger = logging.getLogger("mini_synth")

WEB_DIR = Path(__file__).resolve().parents[1] / "assets" / "web"


def _state_dir() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "mini-synth"


def setup_logging() -> None:
    log_dir = _state_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_dir / "mini-synth.log", maxBytes=512_000, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    if os.environ.get("MINI_SYNTH_DEBUG"):
        root.setLevel(logging.DEBUG)
        stream = logging.StreamHandler(sys.stderr)
        stream.setFormatter(logging.Formatter("%(levelname)-7s %(name)s: %(message)s"))
        root.addHandler(stream)


def _fatal_error_html(message: str) -> str:
    """Página mínima para erros que impedem o app de abrir (sem stack trace)."""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
    <style>
      body{{margin:0;height:100vh;display:flex;flex-direction:column;gap:20px;
        align-items:center;justify-content:center;text-align:center;padding:50px;
        font-family:sans-serif;background:#c9cdd2;color:#26292e}}
      h1{{color:#b52a1c;font-size:34px;margin:0}}
      p{{font-size:20px;max-width:640px;line-height:1.4}}
    </style></head><body>
      <h1>Ops!</h1><p>{escape(message)}</p>
    </body></html>"""


def _run_fatal_window(message: str) -> int:
    webview.create_window("Mini Synth", html=_fatal_error_html(message),
                          width=720, height=320)
    webview.start(gui="gtk")
    return 0


def main() -> int:
    setup_logging()
    logger.info("Iniciando Mini Synth.")

    # Permite encerrar com Ctrl+C no terminal.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        config = loader.load_app_config()
    except ConfigError as exc:
        logger.error("Configuração inválida: %s", exc)
        return _run_fatal_window(str(exc))

    settings = loader.load_user_settings()
    controller = Application(config, settings)

    fullscreen = config.interface.fullscreen or settings.fullscreen
    # Carrega via file:// (sem http server): os assets relativos resolvem contra
    # o diretório do index.html e não fazemos fetch/XHR, então não há CORS.
    index_url = (WEB_DIR / "index.html").as_uri()
    window = webview.create_window(
        "Mini Synth",
        index_url,
        js_api=controller.window.api,
        width=1100,
        height=720,
        min_size=(900, 540),
        fullscreen=fullscreen,
        background_color="#c9cdd2",
    )
    controller.window.attach(window)

    def on_loaded() -> None:
        # Monta a interface a partir da config e sobe áudio + MIDI.
        controller.window.init_ui()
        controller.start()

    window.events.loaded += on_loaded

    try:
        webview.start(gui="gtk")
    finally:
        controller.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
