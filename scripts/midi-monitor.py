#!/usr/bin/env python3
"""Monitor MIDI — descobre quais mensagens seu teclado/knobs enviam.

Abre a primeira porta MIDI física (mesma lógica de filtragem do app) e mostra,
em tempo real, tudo que chega. Ideal para descobrir o número de CC de cada knob.

Uso:
    python scripts/midi-monitor.py

Gire UM knob de cada vez (A1, depois A2, ...). Cada knob costuma ter um número
de CC diferente. Ao final, pressione Ctrl+C para ver o resumo.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Permite importar o pacote src/ ao rodar como script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.midi import alsa  # noqa: E402

# Nome amigável dos controles comuns.
CC_NAMES = {
    1: "Mod Wheel",
    7: "Volume",
    10: "Pan",
    11: "Expression",
    64: "Sustain (pedal)",
    91: "Reverb",
    93: "Chorus",
}

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def note_name(note: int) -> str:
    return f"{NOTE_NAMES[note % 12]}{note // 12 - 1}"


def main() -> int:
    midi_in = alsa.create_midi_in()
    if midi_in is None:
        print("python-rtmidi indisponível. Rode dentro do .venv.", file=sys.stderr)
        return 1

    ports = alsa.list_input_ports(midi_in)
    target = alsa.choose_port([p for p in ports])
    if target is None:
        print("Nenhum teclado MIDI físico encontrado.")
        print("Portas vistas:", [p.name for p in ports])
        return 1

    midi_in.open_port(target.index, name="monitor")
    print(f"Ouvindo: {target.name}")
    print("Gire os knobs (A1, A2, ...) UM DE CADA VEZ. Ctrl+C para encerrar.\n")

    # cc -> [ordem_de_aparição, contagem, min, max, último]
    seen: dict[int, list[int]] = {}
    order = 0

    try:
        while True:
            msg = midi_in.get_message()
            if msg is None:
                time.sleep(0.001)
                continue
            data, _delta = msg
            if not data:
                continue
            status = data[0] & 0xF0
            channel = (data[0] & 0x0F) + 1

            if status == 0xB0 and len(data) >= 3:  # Control Change
                cc, value = data[1], data[2]
                if cc not in seen:
                    order += 1
                    seen[cc] = [order, 0, value, value, value]
                rec = seen[cc]
                rec[1] += 1
                rec[2] = min(rec[2], value)
                rec[3] = max(rec[3], value)
                rec[4] = value
                name = CC_NAMES.get(cc, "knob/controle")
                print(f"  CC {cc:>3}  = {value:>3}   (canal {channel}, {name})")
            elif status == 0x90 and len(data) >= 3 and data[2] > 0:
                print(f"  NOTE ON   {data[1]:>3} ({note_name(data[1])})  vel {data[2]}")
            elif status in (0x80, 0x90) and len(data) >= 3:
                print(f"  NOTE OFF  {data[1]:>3} ({note_name(data[1])})")
            elif status == 0xE0 and len(data) >= 3:
                bend = (data[2] << 7 | data[1]) - 8192
                print(f"  PITCH BEND {bend:+d}")
    except KeyboardInterrupt:
        pass
    finally:
        midi_in.close_port()

    print("\n===== RESUMO DOS CONTROLES (CC) =====")
    if not seen:
        print("Nenhum CC capturado. Os knobs enviaram algo? Tente girar mais.")
    else:
        print("Ordem em que apareceram (gire A1, A2, ... nessa ordem para mapear):\n")
        for cc, (ordem, count, lo, hi, last) in sorted(seen.items(), key=lambda x: x[1][0]):
            name = CC_NAMES.get(cc, "")
            extra = f"  [{name}]" if name else ""
            print(f"  {ordem:>2}º  →  CC {cc:>3}   ({count} msgs, faixa {lo}..{hi}){extra}")
        print("\nAnote qual CC corresponde ao knob A1 — é ele que vai trocar o instrumento.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
