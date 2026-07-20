"""Testes de seleção de instrumento (bank/program) e som de teste."""

from __future__ import annotations

from src.audio.mock_backend import MockBackend
from src.audio.synthesizer import DRUM_CHANNEL, PLAY_CHANNEL, Synthesizer
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


# ---- percussão (bateria) -------------------------------------------------
def _drum_kit() -> Instrument:
    return Instrument(id="drums", label="BATERIA", display_name="Bateria",
                      bank=128, program=0, percussion=True)


def test_percussion_selects_on_drum_channel(synth: Synthesizer, backend):
    synth.select_instrument(_drum_kit())
    sel = backend.last_selection
    assert sel.channel == DRUM_CHANNEL
    assert sel.bank == 128
    assert synth.play_channel == DRUM_CHANNEL


def test_percussion_notes_route_to_drum_channel_without_transpose(synth: Synthesizer, backend):
    synth.set_octave(2)  # oitava alta não deve afetar a bateria
    synth.select_instrument(_drum_kit())
    synth.handle_note_on(38, 100)   # 38 = caixa (GM)
    assert (DRUM_CHANNEL, 38, 100) in backend.notes_on
    synth.handle_note_off(38)
    assert (DRUM_CHANNEL, 38) in backend.notes_off


def test_switching_from_drums_back_to_melodic_restores_channel(synth: Synthesizer, backend, piano):
    synth.select_instrument(_drum_kit())
    assert synth.play_channel == DRUM_CHANNEL
    synth.select_instrument(piano)
    assert synth.play_channel == PLAY_CHANNEL
    synth.handle_note_on(60, 100)
    assert (PLAY_CHANNEL, 60, 100) in backend.notes_on
