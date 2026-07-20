"""Testes do sintetizador via MockBackend: panic, ciclo de vida, notas."""

from __future__ import annotations

from src.audio.mock_backend import MockBackend
from src.audio.synthesizer import Synthesizer
from src.config.models import AudioConfig


def test_backend_lifecycle(backend: MockBackend, audio_config: AudioConfig):
    synth = Synthesizer(backend, audio_config)
    assert not synth.is_running
    synth.start()
    assert synth.is_running
    synth.stop()
    assert not synth.is_running


def test_load_soundfont_records_path(backend: MockBackend, audio_config: AudioConfig):
    synth = Synthesizer(backend, audio_config)
    synth.start()
    synth.load_soundfont("/some/path.sf2")
    assert backend.loaded_soundfonts == ["/some/path.sf2"]


def test_panic_sends_all_sound_off_and_all_notes_off(synth: Synthesizer, backend):
    # Toca algumas notas primeiro.
    synth.handle_note_on(60, 100)
    synth.handle_note_on(64, 100)
    assert backend.active_notes

    synth.panic()

    # CC 120 (All Sound Off) e CC 123 (All Notes Off) em todos os 16 canais.
    for channel in range(16):
        assert (channel, 120, 0) in backend.control_changes
        assert (channel, 123, 0) in backend.control_changes
    assert backend.resets == 1
    # Nenhuma nota deve continuar ativa (resolve notas travadas).
    assert backend.active_notes == set()


def test_stop_triggers_panic(backend: MockBackend, audio_config: AudioConfig):
    synth = Synthesizer(backend, audio_config)
    synth.start()
    synth.load_soundfont("/x.sf2")
    synth.handle_note_on(60, 100)
    synth.stop()
    assert backend.resets >= 1
    assert not backend.running


def test_note_off_clears_active_note(synth: Synthesizer, backend):
    synth.handle_note_on(60, 100)
    assert (0, 60) in backend.active_notes
    synth.handle_note_off(60)
    assert (0, 60) not in backend.active_notes


def test_mock_backend_satisfies_protocol():
    from src.audio.synthesizer import SynthesizerBackend

    assert isinstance(MockBackend(), SynthesizerBackend)
