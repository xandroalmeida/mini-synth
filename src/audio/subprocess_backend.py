"""Backend que controla o binário ``fluidsynth`` via subprocesso.

Fallback para o caso da libfluidsynth/pyfluidsynth apresentar problemas. Fala
com o processo pelo shell de comandos do FluidSynth (stdin), o que mantém a
integração desacoplada da API C.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import threading

from ..config.models import AudioConfig
from .synthesizer import SynthError

logger = logging.getLogger(__name__)


class SubprocessBackend:
    """Implementa ``SynthesizerBackend`` conversando com o CLI do FluidSynth."""

    def __init__(self, audio: AudioConfig) -> None:
        self._audio = audio
        self._proc: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()
        self._sfid = 1  # o CLL do fluidsynth numera as fonts a partir de 1

    def start(self) -> None:
        binary = shutil.which("fluidsynth")
        if binary is None:
            raise SynthError("O programa 'fluidsynth' não está instalado.")
        cmd = [
            binary,
            "-a", self._audio.driver,
            "-o", f"audio.period-size={self._audio.buffer_size}",
            "-r", str(self._audio.sample_rate),
            "-g", str(self._audio.gain),
            "-s",           # inicia o shell de comandos (lê de stdin)
            "-i",           # não entra em modo interativo de terminal
        ]
        try:
            self._proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except OSError as exc:  # pragma: no cover
            raise SynthError("Não foi possível iniciar o FluidSynth.") from exc
        logger.info("FluidSynth (subprocesso) iniciado: %s", " ".join(cmd))

    def stop(self) -> None:
        if self._proc is None:
            return
        try:
            self._send("quit")
            self._proc.wait(timeout=2)
        except Exception:  # pragma: no cover
            self._proc.kill()
        finally:
            self._proc = None

    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def _send(self, command: str) -> None:
        if self._proc is None or self._proc.stdin is None:
            return
        with self._lock:
            try:
                self._proc.stdin.write(command + "\n")
                self._proc.stdin.flush()
            except (BrokenPipeError, OSError):  # pragma: no cover
                logger.warning("Conexão com o FluidSynth perdida.")

    def load_soundfont(self, path: str) -> int:
        self._send(f'load "{path}"')
        sfid = self._sfid
        self._sfid += 1
        return sfid

    def program_select(self, channel: int, sfid: int, bank: int, program: int) -> None:
        self._send(f"select {channel} {sfid} {bank} {program}")

    def set_gain(self, gain: float) -> None:
        self._send(f"gain {gain:.4f}")

    def set_reverb(self, level: float) -> None:
        self._send(f"reverb {'on' if level > 0 else 'off'}")
        self._send(f"rev_setlevel {level:.3f}")

    def note_on(self, channel: int, note: int, velocity: int) -> None:
        self._send(f"noteon {channel} {note} {velocity}")

    def note_off(self, channel: int, note: int) -> None:
        self._send(f"noteoff {channel} {note}")

    def control_change(self, channel: int, control: int, value: int) -> None:
        self._send(f"cc {channel} {control} {value}")

    def system_reset(self) -> None:
        self._send("reset")
