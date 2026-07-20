"""Testes de carregamento e validação de configuração e persistência."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from src.config import loader
from src.config.models import AppConfig, ConfigError, UserSettings


VALID_YAML = """
soundfont:
  path: "/tmp/fake.sf2"
audio:
  driver: "pulseaudio"
  gain: 0.8
  sample_rate: 44100
  buffer_size: 256
midi:
  auto_connect: true
interface:
  fullscreen: false
  columns: 4
instruments:
  - id: grand_piano
    label: "PIANO"
    display_name: "Grand Piano"
    bank: 0
    program: 0
  - id: organ
    label: "ÓRGÃO"
    display_name: "Órgão"
    bank: 0
    program: 19
"""


def _write(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "instruments.yaml"
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def test_load_valid_config(tmp_path: Path) -> None:
    config = loader.load_app_config(_write(tmp_path, VALID_YAML))
    assert isinstance(config, AppConfig)
    assert len(config.instruments) == 2
    assert config.audio.driver == "pulseaudio"
    assert config.interface.columns == 4
    assert config.instrument_by_id("organ").program == 19


def test_the_real_project_config_loads() -> None:
    # O instruments.yaml versionado deve ser válido e ter >= 12 instrumentos.
    config = loader.load_app_config()
    assert len(config.instruments) >= 12
    assert config.instrument_by_id("grand_piano") is not None


def test_missing_instruments_raises(tmp_path: Path) -> None:
    yaml_no_instruments = """
    soundfont:
      path: "/tmp/x.sf2"
    instruments: []
    """
    with pytest.raises(ConfigError):
        loader.load_app_config(_write(tmp_path, yaml_no_instruments))


def test_duplicate_ids_raise(tmp_path: Path) -> None:
    dup = VALID_YAML.replace('id: organ', 'id: grand_piano')
    with pytest.raises(ConfigError):
        loader.load_app_config(_write(tmp_path, dup))


def test_program_out_of_range_raises(tmp_path: Path) -> None:
    bad = VALID_YAML.replace("program: 19", "program: 999")
    with pytest.raises(ConfigError):
        loader.load_app_config(_write(tmp_path, bad))


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        loader.load_app_config(tmp_path / "inexistente.yaml")


def test_user_settings_defaults_when_absent(tmp_path: Path) -> None:
    settings = loader.load_user_settings(tmp_path / "settings.yaml")
    assert settings.volume == 70
    assert settings.octave == 0


def test_user_settings_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "settings.yaml"
    original = UserSettings(volume=55, reverb=50, octave=1, last_instrument="organ")
    loader.save_user_settings(original, path)
    assert path.exists()
    reloaded = loader.load_user_settings(path)
    assert reloaded.volume == 55
    assert reloaded.reverb == 50
    assert reloaded.octave == 1
    assert reloaded.last_instrument == "organ"


def test_user_settings_clamps_and_quantizes() -> None:
    s = UserSettings(volume=250, reverb=40, octave=9)
    assert s.volume == 100
    assert s.reverb == 50  # quantizado para o mais próximo de {0,25,50,75,100}
    assert s.octave == 2


def test_find_soundfont_prefers_existing(tmp_path: Path) -> None:
    sf = tmp_path / "meu.sf2"
    sf.write_bytes(b"fake")
    assert loader.find_soundfont(str(sf)) == sf
