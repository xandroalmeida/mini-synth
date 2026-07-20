"""Testes da filtragem de portas MIDI físicas (sem hardware)."""

from __future__ import annotations

from src.midi.alsa import (
    MidiPort,
    choose_port,
    filter_physical,
    is_physical_port,
)


def test_physical_keyboard_is_kept():
    assert is_physical_port("MidiKeyboard MIDI 1 20:0")
    assert is_physical_port("Arturia KeyStep 32")


def test_virtual_and_fluid_ports_are_ignored():
    assert not is_physical_port("FLUID Synth (25413):Synth input port")
    assert not is_physical_port("Midi Through Port-0")
    assert not is_physical_port("RtMidi Input Client")
    assert not is_physical_port("System Announce")
    assert not is_physical_port("Mini Synth in")


def test_filter_physical_keeps_only_real_devices():
    ports = [
        MidiPort(0, "Midi Through Port-0"),
        MidiPort(1, "MidiKeyboard MIDI 1"),
        MidiPort(2, "FLUID Synth (999)"),
        MidiPort(3, "Keystation 49"),
    ]
    physical = filter_physical(ports)
    names = [p.name for p in physical]
    assert names == ["MidiKeyboard MIDI 1", "Keystation 49"]


def test_choose_port_picks_first_physical():
    ports = [
        MidiPort(0, "Midi Through Port-0"),
        MidiPort(1, "MidiKeyboard MIDI 1"),
        MidiPort(2, "Keystation 49"),
    ]
    chosen = choose_port(ports)
    assert chosen is not None
    assert chosen.name == "MidiKeyboard MIDI 1"


def test_choose_port_prefers_named_device():
    ports = [
        MidiPort(0, "MidiKeyboard MIDI 1"),
        MidiPort(1, "Keystation 49"),
    ]
    chosen = choose_port(ports, preferred="keystation")
    assert chosen is not None
    assert chosen.name == "Keystation 49"


def test_choose_port_returns_none_without_physical():
    ports = [
        MidiPort(0, "Midi Through Port-0"),
        MidiPort(1, "FLUID Synth (1)"),
    ]
    assert choose_port(ports) is None


def test_app_does_not_connect_to_itself():
    # A porta do próprio app nunca deve ser considerada física.
    ports = [MidiPort(0, "Mini Synth in"), MidiPort(1, "Piano USB")]
    assert [p.name for p in filter_physical(ports)] == ["Piano USB"]


# --------------------------------------------------------------------------
# Reconexão do MidiDeviceManager (usa um rtmidi falso, sem hardware)
# --------------------------------------------------------------------------


def _make_manager(monkeypatch, fake):
    from src.midi import alsa, device_manager

    monkeypatch.setattr(alsa, "create_midi_in", lambda: fake)
    monkeypatch.setattr(device_manager.alsa, "create_midi_in", lambda: fake)
    return device_manager.MidiDeviceManager()


def test_manager_connects_to_physical_device(qapp, monkeypatch, fake_midi_cls):
    from src.midi.device_manager import STATE_CONNECTED

    fake = fake_midi_cls()
    fake.ports = ["Midi Through Port-0", "MidiKeyboard MIDI 1"]
    manager = _make_manager(monkeypatch, fake)

    states: list[tuple[str, str]] = []
    manager.status_changed.connect(lambda s, m: states.append((s, m)))

    manager._poll()
    assert manager.state == STATE_CONNECTED
    assert manager.connected_device == "MidiKeyboard MIDI 1"
    assert fake.opened_index == 1


def test_manager_detects_disconnect_and_reconnect(qapp, monkeypatch, fake_midi_cls):
    from src.midi.device_manager import STATE_CONNECTED, STATE_SEARCHING

    fake = fake_midi_cls()
    fake.ports = ["MidiKeyboard MIDI 1"]
    manager = _make_manager(monkeypatch, fake)

    manager._poll()
    assert manager.state == STATE_CONNECTED

    # Desconecta o teclado.
    fake.ports = []
    manager._poll()
    assert manager.state == STATE_SEARCHING
    assert manager.connected_device == ""

    # Reconecta.
    fake.ports = ["MidiKeyboard MIDI 1"]
    manager._poll()
    assert manager.state == STATE_CONNECTED


def test_manager_forwards_note_events(qapp, monkeypatch, fake_midi_cls):
    fake = fake_midi_cls()
    fake.ports = ["Piano USB"]
    manager = _make_manager(monkeypatch, fake)
    manager._poll()

    notes_on: list[tuple[int, int]] = []
    notes_off: list[int] = []
    manager.note_on.connect(lambda n, v: notes_on.append((n, v)))
    manager.note_off.connect(lambda n: notes_off.append(n))

    fake.emit([0x90, 60, 100])   # note on
    fake.emit([0x90, 60, 0])     # note on com velocidade 0 == note off
    fake.emit([0x80, 62, 0])     # note off

    assert (60, 100) in notes_on
    assert 60 in notes_off
    assert 62 in notes_off
