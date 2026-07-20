"""Carregamento da configuração do app e persistência das preferências.

- ``instruments.yaml``  -> :class:`AppConfig` (instrumentos, soundfont, áudio...)
- ``settings.yaml``     -> :class:`UserSettings` (volume, reverb, oitava...)

As preferências do usuário são gravadas em ``~/.config/mini-synth/settings.yaml``.
Se o arquivo não existir, valores padrão são usados.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import yaml

from .models import AppConfig, ConfigError, UserSettings

logger = logging.getLogger(__name__)

# Diretórios padrão para procurar SoundFonts já instaladas no sistema.
SOUNDFONT_SEARCH_DIRS: tuple[Path, ...] = (
    Path("/usr/share/sounds/sf2"),
    Path("/usr/share/sounds/sf3"),
    Path("/usr/share/soundfonts"),
    Path.home() / "SoundFonts",
)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "instruments.yaml"


def _config_home() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "mini-synth"


def settings_path() -> Path:
    return _config_home() / "settings.yaml"


def load_app_config(path: Path | None = None) -> AppConfig:
    """Carrega e valida ``instruments.yaml``.

    Levanta :class:`ConfigError` com mensagem amigável em caso de problema.
    """
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise ConfigError(f"Arquivo de configuração não encontrado: {config_path}")
    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Erro ao ler a configuração: {exc}") from exc
    return AppConfig.from_dict(data or {})


def load_user_settings(path: Path | None = None) -> UserSettings:
    """Carrega as preferências do usuário, ou retorna padrões se não existir."""
    settings_file = path or settings_path()
    if not settings_file.exists():
        logger.info("settings.yaml não encontrado; usando valores padrão.")
        return UserSettings()
    try:
        with settings_file.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return UserSettings.from_dict(data)
    except (yaml.YAMLError, OSError, ValueError) as exc:
        logger.warning("Falha ao ler settings.yaml (%s); usando padrões.", exc)
        return UserSettings()


def save_user_settings(settings: UserSettings, path: Path | None = None) -> None:
    """Grava as preferências do usuário de forma atômica."""
    settings_file = path or settings_path()
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = settings_file.with_suffix(".yaml.tmp")
    try:
        with tmp.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(settings.to_dict(), handle, allow_unicode=True, sort_keys=False)
        os.replace(tmp, settings_file)
    except OSError as exc:  # pragma: no cover - I/O
        logger.error("Não foi possível salvar as preferências: %s", exc)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def find_soundfont(preferred: str | None = None) -> Path | None:
    """Resolve a SoundFont a ser usada.

    Ordem: caminho ``preferred`` (se existir) -> primeira SoundFont encontrada
    nos diretórios padrão do sistema. Retorna ``None`` se nada for encontrado.
    """
    if preferred:
        candidate = Path(preferred).expanduser()
        if candidate.exists():
            return candidate
        logger.warning("SoundFont preferida não encontrada: %s", candidate)

    for directory in SOUNDFONT_SEARCH_DIRS:
        if not directory.is_dir():
            continue
        for pattern in ("*.sf2", "*.sf3"):
            for found in sorted(directory.glob(pattern)):
                if found.is_file():
                    logger.info("SoundFont encontrada automaticamente: %s", found)
                    return found
    return None
