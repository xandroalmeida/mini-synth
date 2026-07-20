"""Testes de volume e reverb."""

from __future__ import annotations

import pytest

from src.audio.synthesizer import Synthesizer


def test_set_volume_clamps(synth: Synthesizer):
    assert synth.set_volume(150) == 100
    assert synth.set_volume(-10) == 0


def test_volume_maps_to_gain(synth: Synthesizer, backend):
    # max_gain vem do AudioConfig.gain (0.8). volume 100 -> gain 0.8.
    synth.set_volume(100)
    assert backend.gain == pytest.approx(0.8)
    synth.set_volume(50)
    assert backend.gain == pytest.approx(0.4)
    synth.set_volume(0)
    assert backend.gain == pytest.approx(0.0)


def test_volume_up_down_steps(synth: Synthesizer):
    synth.set_volume(50)
    assert synth.volume_up() == 55
    assert synth.volume_down() == 50


def test_reverb_quantizes_to_allowed_levels(synth: Synthesizer):
    assert synth.set_reverb(40) == 50
    assert synth.set_reverb(10) == 0
    assert synth.set_reverb(70) == 75


def test_reverb_up_down(synth: Synthesizer):
    synth.set_reverb(0)
    assert synth.reverb_up() == 25
    assert synth.reverb_up() == 50
    assert synth.reverb_down() == 25


def test_reverb_sets_backend_level(synth: Synthesizer, backend):
    synth.set_reverb(100)
    assert backend.reverb == pytest.approx(1.0)
    synth.set_reverb(0)
    assert backend.reverb == pytest.approx(0.0)
