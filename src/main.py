"""Ponto de entrada. Execute com ``python -m src.main`` ou ``./run.sh``."""

from __future__ import annotations

import logging
import os
import signal
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .application import Application
from .config import loader
from .config.models import ConfigError
from .ui import styles

logger = logging.getLogger("mini_synth")


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
    # Também no terminal em modo de desenvolvimento, com nível DEBUG.
    if os.environ.get("MINI_SYNTH_DEBUG"):
        root.setLevel(logging.DEBUG)
        stream = logging.StreamHandler(sys.stderr)
        stream.setFormatter(logging.Formatter("%(levelname)-7s %(name)s: %(message)s"))
        root.addHandler(stream)


def _fatal_error_window(message: str) -> QWidget:
    """Janela mínima para erros que impedem o app de abrir (sem stack trace)."""
    window = QWidget()
    window.setObjectName("RootPanel")
    window.setWindowTitle("Mini Synth")
    window.resize(700, 300)
    layout = QVBoxLayout(window)
    layout.setContentsMargins(50, 50, 50, 50)
    layout.setSpacing(20)

    title = QLabel("Ops!")
    title.setObjectName("ErrorTitle")
    body = QLabel(message)
    body.setObjectName("ErrorMessage")
    body.setWordWrap(True)
    close = QPushButton("FECHAR")
    close.setProperty("class", "Physical")
    close.setMinimumHeight(60)
    close.clicked.connect(window.close)

    layout.addWidget(title)
    layout.addWidget(body)
    layout.addWidget(close)
    return window


def main() -> int:
    setup_logging()
    logger.info("Iniciando Mini Synth.")

    app = QApplication(sys.argv)
    app.setApplicationName("Mini Synth")
    app.setStyleSheet(styles.app_stylesheet())

    icon_path = Path(__file__).resolve().parents[1] / "assets" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Permite encerrar com Ctrl+C no terminal.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        config = loader.load_app_config()
    except ConfigError as exc:
        logger.error("Configuração inválida: %s", exc)
        window = _fatal_error_window(str(exc))
        window.show()
        return app.exec()

    settings = loader.load_user_settings()

    controller = Application(config, settings)
    app.aboutToQuit.connect(controller.shutdown)
    controller.start()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
