"""Testes de transposição de oitava."""

from __future__ import annotations

from src.audio.synthesizer import PLAY_CHANNEL, Synthesizer


def test_octave_clamped_between_minus2_and_plus2(synth: Synthesizer):
    assert synth.set_octave(5) == 2
    assert synth.set_octave(-5) == -2
    assert synth.octave_reset() == 0


def test_octave_up_down(synth: Synthesizer):
    synth.set_octave(0)
    assert synth.octave_up() == 1
    assert synth.octave_up() == 2
    assert synth.octave_up() == 2  # não passa de +2
    assert synth.octave_down() == 1


def test_transpose_shifts_by_twelve_per_octave(synth: Synthesizer):
    synth.set_octave(1)
    assert synth.transpose(60) == 72
    synth.set_octave(-1)
    assert synth.transpose(60) == 48


def test_transpose_out_of_range_returns_none(synth: Synthesizer):
    synth.set_octave(2)
    assert synth.transpose(120) is None  # 120 + 24 = 144 > 127


def test_note_on_is_transposed(synth: Synthesizer, backend):
    synth.set_octave(1)
    synth.handle_note_on(60, 100)
    assert (PLAY_CHANNEL, 72, 100) in backend.notes_on


def test_note_on_velocity_zero_is_note_off(synth: Synthesizer, backend):
    synth.set_octave(0)
    synth.handle_note_on(60, 0)
    assert (PLAY_CHANNEL, 60) in backend.notes_off
    assert not backend.notes_on


def test_out_of_range_note_is_dropped(synth: Synthesizer, backend):
    synth.set_octave(2)
    synth.handle_note_on(120, 100)  # transpõe para fora de 0..127
    assert not backend.notes_on
