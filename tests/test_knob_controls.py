"""Testes do mapeamento de knobs (MIDI CC) para ações do app."""

from __future__ import annotations

import pytest

from src.audio.mock_backend import MockBackend
from src.audio.synthesizer import PLAY_CHANNEL, Synthesizer
from src.config import loader
from src.config.models import AudioConfig, ConfigError, ControlsConfig, UserSettings


# ---- configuração --------------------------------------------------------
def test_controls_parse_and_map():
    controls = ControlsConfig.from_dict(
        {"knobs": [
            {"cc": 91, "action": "instrument", "label": "A1"},
            {"cc": 93, "action": "volume"},
            {"cc": 10, "action": "none"},
        ]}
    )
    mapping = controls.action_by_cc()
    assert mapping == {91: "instrument", 93: "volume"}  # 'none' é ignorado


def test_controls_default_empty():
    assert ControlsConfig.from_dict(None).action_by_cc() == {}


def test_invalid_knob_action_raises():
    with pytest.raises(ConfigError):
        ControlsConfig.from_dict({"knobs": [{"cc": 91, "action": "explodir"}]})


def test_invalid_cc_raises():
    with pytest.raises(ConfigError):
        ControlsConfig.from_dict({"knobs": [{"cc": 200, "action": "volume"}]})


def test_real_config_maps_a1_to_instrument():
    # O instruments.yaml versionado deve ter A1 (CC 1) trocando o instrumento.
    config = loader.load_app_config()
    assert config.controls.action_by_cc().get(1) == "instrument"


# ---- comportamento no Application ---------------------------------------
def _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path):
    # Evita escrever settings.yaml real e tocar hardware MIDI.
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    from src.midi import alsa, device_manager

    fake = fake_midi_cls()
    fake.ports = ["Piano USB"]
    monkeypatch.setattr(alsa, "create_midi_in", lambda: fake)
    monkeypatch.setattr(device_manager.alsa, "create_midi_in", lambda: fake)

    from src.application import Application

    config = loader.load_app_config()
    app = Application(config, UserSettings())

    backend = MockBackend()
    synth = Synthesizer(backend, AudioConfig())
    synth.start()
    synth.load_soundfont("/fake.sf2")
    app._synth = synth
    return app, synth, backend, config


def test_knob_a1_selects_instrument_by_position(qapp, monkeypatch, fake_midi_cls, tmp_path):
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    first = config.instruments[0]
    last = config.instruments[-1]

    app._on_control_change(1, 0)      # knob totalmente à esquerda
    assert synth.current_instrument is first

    app._on_control_change(1, 127)    # totalmente à direita
    assert synth.current_instrument is last

    # posição intermediária cai em um instrumento do meio
    app._on_control_change(1, 64)
    mid = synth.current_instrument
    assert mid is not first and mid is not last


def test_knob_a1_updates_display(qapp, monkeypatch, fake_midi_cls, tmp_path):
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    app._on_control_change(1, 127)
    assert app.window.display_value.text() == config.instruments[-1].display_name.upper()


def test_unmapped_cc_is_forwarded_to_synth(qapp, monkeypatch, fake_midi_cls, tmp_path):
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    # CC 64 (sustain) não está mapeado -> deve ir para o synth.
    app._on_control_change(64, 100)
    assert (PLAY_CHANNEL, 64, 100) in backend.control_changes


def test_mapped_instrument_cc_not_forwarded_as_synth_cc(qapp, monkeypatch, fake_midi_cls, tmp_path):
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    app._on_control_change(1, 64)
    # CC 1 mapeado para 'instrument' não deve virar um cc() no synth.
    assert not any(cc == 1 for (_ch, cc, _v) in backend.control_changes)


# ---- Program Change (knob A1 em modo PC) --------------------------------
def test_program_change_selects_instrument(qapp, monkeypatch, fake_midi_cls, tmp_path):
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    app._on_program_change(0)
    assert synth.current_instrument is config.instruments[0]
    app._on_program_change(127)
    assert synth.current_instrument is config.instruments[-1]


def test_program_change_maps_number_to_instrument_1_to_n(qapp, monkeypatch, fake_midi_cls, tmp_path):
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    n = len(config.instruments)
    # valor 1 -> 1º instrumento, ..., valor N -> N-ésimo
    for number in range(1, n + 1):
        app._on_program_change(number)
        assert synth.current_instrument is config.instruments[number - 1]


def test_program_change_above_count_stays_on_last(qapp, monkeypatch, fake_midi_cls, tmp_path):
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    n = len(config.instruments)
    app._on_program_change(n + 1)      # 13, com 12 instrumentos
    assert synth.current_instrument is config.instruments[-1]
    app._on_program_change(50)
    assert synth.current_instrument is config.instruments[-1]
    app._on_program_change(127)
    assert synth.current_instrument is config.instruments[-1]


def test_program_change_can_be_disabled(qapp, monkeypatch, fake_midi_cls, tmp_path):
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    app._config.controls.program_change_selects_instrument = False
    app._on_program_change(0)
    app._on_program_change(127)
    # nada deve ter sido selecionado por Program Change
    assert backend.last_selection is None


def test_device_manager_emits_program_change(qapp, monkeypatch, fake_midi_cls):
    from src.midi import alsa, device_manager

    fake = fake_midi_cls()
    fake.ports = ["Piano USB"]
    monkeypatch.setattr(alsa, "create_midi_in", lambda: fake)
    monkeypatch.setattr(device_manager.alsa, "create_midi_in", lambda: fake)
    manager = device_manager.MidiDeviceManager()
    manager.start()

    received: list[int] = []
    manager.program_change.connect(received.append)
    fake.emit([0xC0, 7])   # Program Change 7
    assert received == [7]
