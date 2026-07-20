"""Backend de síntese simulado, para testes sem áudio real."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProgramSelection:
    channel: int
    sfid: int
    bank: int
    program: int


@dataclass
class MockBackend:
    """Registra todas as chamadas em memória, sem produzir áudio.

    Implementa o protocolo :class:`~src.audio.synthesizer.SynthesizerBackend`.
    """

    running: bool = False
    gain: float = 0.0
    reverb: float = 0.0
    loaded_soundfonts: list[str] = field(default_factory=list)
    selections: list[ProgramSelection] = field(default_factory=list)
    notes_on: list[tuple[int, int, int]] = field(default_factory=list)
    notes_off: list[tuple[int, int]] = field(default_factory=list)
    control_changes: list[tuple[int, int, int]] = field(default_factory=list)
    resets: int = 0
    active_notes: set[tuple[int, int]] = field(default_factory=set)

    _next_sfid: int = 1

    # ---- ciclo de vida ----
    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def is_running(self) -> bool:
        return self.running

    # ---- soundfont / programa ----
    def load_soundfont(self, path: str) -> int:
        self.loaded_soundfonts.append(path)
        sfid = self._next_sfid
        self._next_sfid += 1
        return sfid

    def program_select(self, channel: int, sfid: int, bank: int, program: int) -> None:
        self.selections.append(ProgramSelection(channel, sfid, bank, program))

    @property
    def last_selection(self) -> ProgramSelection | None:
        return self.selections[-1] if self.selections else None

    # ---- mixagem ----
    def set_gain(self, gain: float) -> None:
        self.gain = gain

    def set_reverb(self, level: float) -> None:
        self.reverb = level

    # ---- notas ----
    def note_on(self, channel: int, note: int, velocity: int) -> None:
        self.notes_on.append((channel, note, velocity))
        self.active_notes.add((channel, note))

    def note_off(self, channel: int, note: int) -> None:
        self.notes_off.append((channel, note))
        self.active_notes.discard((channel, note))

    def control_change(self, channel: int, control: int, value: int) -> None:
        self.control_changes.append((channel, control, value))
        # All Sound Off (120) / All Notes Off (123) esvaziam o canal.
        if control in (120, 123):
            for key in {n for n in self.active_notes if n[0] == channel}:
                self.active_notes.discard(key)

    def system_reset(self) -> None:
        self.resets += 1
        self.active_notes.clear()
