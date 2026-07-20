"""Fixtures compartilhadas pelos testes."""

from __future__ import annotations

import os

# Permite instanciar QObjects (device manager) sem servidor gráfico.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from src.audio.mock_backend import MockBackend
from src.audio.synthesizer import Synthesizer
from src.config.models import AudioConfig, Instrument


@pytest.fixture
def audio_config() -> AudioConfig:
    return AudioConfig(driver="mock", gain=0.8, sample_rate=44100, buffer_size=256)


@pytest.fixture
def backend() -> MockBackend:
    return MockBackend()


@pytest.fixture
def synth(backend: MockBackend, audio_config: AudioConfig) -> Synthesizer:
    s = Synthesizer(backend, audio_config)
    s.start()
    s.load_soundfont("/fake/soundfont.sf2")
    return s


@pytest.fixture
def piano() -> Instrument:
    return Instrument(id="grand_piano", label="PIANO", display_name="Grand Piano",
                      bank=0, program=0)


@pytest.fixture
def organ() -> Instrument:
    return Instrument(id="organ", label="ÓRGÃO", display_name="Órgão",
                      bank=0, program=19)


@pytest.fixture(scope="session")
def qapp():
    """QApplication (offscreen) para testes com QObject/Signal/QTimer/QWidget."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


class FakeMidiIn:
    """Substituto de ``rtmidi.MidiIn`` para testes sem hardware."""

    def __init__(self) -> None:
        self.ports: list[str] = []
        self.opened_index: int | None = None
        self.callback = None

    # API usada por src.midi.alsa / device_manager
    def get_ports(self) -> list[str]:
        return list(self.ports)

    def ignore_types(self, **_kwargs) -> None:
        pass

    def open_port(self, index: int, name: str = "") -> None:
        self.opened_index = index

    def set_callback(self, callback) -> None:
        self.callback = callback

    def cancel_callback(self) -> None:
        self.callback = None

    def close_port(self) -> None:
        self.opened_index = None

    def delete(self) -> None:
        pass

    # helper de teste: injeta uma mensagem MIDI
    def emit(self, message: list[int]) -> None:
        if self.callback is not None:
            self.callback((message, 0.0), None)


@pytest.fixture
def fake_midi_cls() -> type[FakeMidiIn]:
    return FakeMidiIn
