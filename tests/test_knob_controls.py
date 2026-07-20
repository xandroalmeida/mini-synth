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


def test_real_config_maps_a1_to_bank_and_a2_to_instrument():
    # No modelo de bancos: A1 (CC 1) troca o banco; A2 troca o instrumento.
    config = loader.load_app_config()
    mapping = config.controls.action_by_cc()
    assert mapping.get(1) == "bank"
    assert "instrument" in mapping.values()


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


def _instrument_cc(config) -> int:
    """CC do knob de instrumento (A3) definido no config real."""
    for cc, action in config.controls.action_by_cc().items():
        if action == "instrument":
            return cc
    raise AssertionError("Nenhum knob mapeado para 'instrument' no config.")


def test_knob_a1_selects_bank_by_direct_index(qapp, monkeypatch, fake_midi_cls, tmp_path):
    # Mapeamento direto: cada valor de CC = um banco (0->1º, 1->2º, ...).
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)

    for i, bank in enumerate(config.banks):
        app._on_control_change(1, i)   # valor i -> (i+1)-ésimo banco
        assert app._current_bank is bank
        assert synth.current_instrument is bank.instruments[0]


def test_knob_a1_clamps_at_last_bank(qapp, monkeypatch, fake_midi_cls, tmp_path):
    # Acima da quantidade de bancos, trava no último (não altera mais).
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    n = len(config.banks)
    app._on_control_change(1, n - 1)
    assert app._current_bank is config.banks[-1]
    for value in (n, n + 3, 100, 127):
        app._on_control_change(1, value)
        assert app._current_bank is config.banks[-1]


def test_knob_a3_selects_instrument_by_direct_index(qapp, monkeypatch, fake_midi_cls, tmp_path):
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    cc = _instrument_cc(config)
    bank = next(b for b in config.banks if len(b.instruments) > 1)
    app._select_bank(bank)

    # valor k -> (k+1)-ésimo instrumento do banco
    for i, inst in enumerate(bank.instruments):
        app._on_control_change(cc, i)
        assert synth.current_instrument is inst


def test_knob_a3_clamps_at_last_instrument(qapp, monkeypatch, fake_midi_cls, tmp_path):
    # Passou da quantidade de instrumentos do banco -> fica no último.
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    cc = _instrument_cc(config)
    bank = next(b for b in config.banks if len(b.instruments) > 1)
    app._select_bank(bank)
    n = len(bank.instruments)
    for value in (n - 1, n, n + 2, 127):
        app._on_control_change(cc, value)
        assert synth.current_instrument is bank.instruments[-1]


def test_knob_a1_updates_display(qapp, monkeypatch, fake_midi_cls, tmp_path):
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    app._on_control_change(1, 127)    # trava no último banco -> mostra seu 1º instrumento
    expected = config.banks[-1].instruments[0].display_name.upper()
    assert app.window.display_value.text() == expected


def test_bank_remembers_last_instrument(qapp, monkeypatch, fake_midi_cls, tmp_path):
    # Ao voltar a um banco, retoma o último instrumento usado nele (não o 1º).
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    bank = next(b for b in config.banks if len(b.instruments) > 1)
    other = next(b for b in config.banks if b is not bank)

    app._select_bank(bank)
    app._on_instrument_selected(bank.instruments[1])   # escolhe o 2º do banco
    assert app._settings.bank_instruments[bank.id] == bank.instruments[1].id

    app._select_bank(other)                            # sai do banco
    app._select_bank(bank)                             # volta
    assert synth.current_instrument is bank.instruments[1]   # retomou onde estava


def test_bank_first_visit_uses_first_instrument(qapp, monkeypatch, fake_midi_cls, tmp_path):
    # Sem histórico, o banco começa no 1º instrumento.
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    bank = next(b for b in config.banks if len(b.instruments) > 1 and b is not app._current_bank)
    app._select_bank(bank)
    assert synth.current_instrument is bank.instruments[0]


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


# ---- Program Change (knob A1 em modo PC) troca o BANCO ------------------
def test_program_change_selects_bank(qapp, monkeypatch, fake_midi_cls, tmp_path):
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    app._on_program_change(0)
    assert app._current_bank is config.banks[0]
    app._on_program_change(127)
    assert app._current_bank is config.banks[-1]


def test_program_change_maps_number_to_bank_1_to_n(qapp, monkeypatch, fake_midi_cls, tmp_path):
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    n = len(config.banks)
    # valor 1 -> 1º banco, ..., valor N -> N-ésimo
    for number in range(1, n + 1):
        app._on_program_change(number)
        assert app._current_bank is config.banks[number - 1]


def test_program_change_above_count_stays_on_last_bank(qapp, monkeypatch, fake_midi_cls, tmp_path):
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    n = len(config.banks)
    app._on_program_change(n + 1)
    assert app._current_bank is config.banks[-1]
    app._on_program_change(50)
    assert app._current_bank is config.banks[-1]
    app._on_program_change(127)
    assert app._current_bank is config.banks[-1]


def test_program_change_can_be_disabled(qapp, monkeypatch, fake_midi_cls, tmp_path):
    app, synth, backend, config = _make_app(qapp, monkeypatch, fake_midi_cls, tmp_path)
    app._config.controls.program_change_selects_bank = False
    app._current_bank = None
    app._on_program_change(0)
    app._on_program_change(127)
    # nada deve ter mudado de banco por Program Change
    assert app._current_bank is None


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
