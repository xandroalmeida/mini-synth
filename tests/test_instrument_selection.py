"""Testes de seleção de instrumento (bank/program) e som de teste."""

from __future__ import annotations

from src.audio.mock_backend import MockBackend
from src.audio.synthesizer import PLAY_CHANNEL, Synthesizer
from src.config.models import AudioConfig, Instrument


def test_selecting_instrument_sends_bank_and_program(synth: Synthesizer, backend, organ):
    synth.select_instrument(organ)
    sel = backend.last_selection
    assert sel is not None
    assert sel.channel == PLAY_CHANNEL
    assert sel.bank == 0
    assert sel.program == 19
    assert synth.current_instrument is organ


def test_switching_instruments_updates_program(synth: Synthesizer, backend, piano, organ):
    synth.select_instrument(piano)
    synth.select_instrument(organ)
    assert backend.last_selection.program == 19
    assert synth.current_instrument is organ


def test_selection_before_soundfont_is_deferred(piano):
    backend = MockBackend()
    synth = Synthesizer(backend, AudioConfig())
    synth.start()
    # Sem soundfont carregada, a seleção fica pendente.
    synth.select_instrument(piano)
    assert backend.last_selection is None
    assert synth.current_instrument is piano
    # Ao carregar a soundfont, o instrumento pendente é aplicado.
    synth.load_soundfont("/fake.sf2")
    assert backend.last_selection is not None
    assert backend.last_selection.program == 0


def test_program_numbers_only_from_instrument(synth: Synthesizer, backend):
    custom = Instrument(id="x", label="X", display_name="X", bank=1, program=42)
    synth.select_instrument(custom)
    assert backend.last_selection.bank == 1
    assert backend.last_selection.program == 42


def test_play_test_sequence_uses_current_channel(synth: Synthesizer, backend, piano):
    synth.select_instrument(piano)
    synth.play_test_sequence((60, 62))
    assert (PLAY_CHANNEL, 60, 100) in backend.notes_on
    assert (PLAY_CHANNEL, 62) in backend.notes_off
