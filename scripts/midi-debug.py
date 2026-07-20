#!/usr/bin/env python3
"""Debug MIDI — mostra na tela TODOS os comandos recebidos do teclado/controlador.

Para cada mensagem que chega, imprime:

  * o conteúdo *raw* (bytes crus em hexadecimal e em decimal);
  * uma *descrição humana* do comando — o que ele significa — quando conhecido.

Diferente do ``midi-monitor.py`` (focado em descobrir o CC de cada knob), este
script decodifica o protocolo MIDI inteiro: Note On/Off, aftertouch, control
change (com nome do controlador), program change, pitch bend, e as mensagens de
sistema (clock, start/stop, SysEx, etc.).

Uso:
    python scripts/midi-debug.py            # abre a 1ª porta física
    python scripts/midi-debug.py --all      # também mostra clock/sysex/active-sense
    python scripts/midi-debug.py --port 1   # abre a porta pelo índice

Pressione Ctrl+C para encerrar.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Permite importar o pacote src/ ao rodar como script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.midi import alsa  # noqa: E402

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Nome amigável dos controladores (Control Change) mais comuns.
CC_NAMES = {
    0: "Bank Select (MSB)",
    1: "Mod Wheel",
    2: "Breath",
    4: "Foot Controller",
    5: "Portamento Time",
    6: "Data Entry (MSB)",
    7: "Volume",
    8: "Balance",
    10: "Pan",
    11: "Expression",
    32: "Bank Select (LSB)",
    64: "Sustain (pedal)",
    65: "Portamento",
    66: "Sostenuto",
    67: "Soft Pedal",
    71: "Resonance",
    74: "Cutoff / Brightness",
    91: "Reverb",
    93: "Chorus",
    120: "All Sound Off",
    121: "Reset All Controllers",
    123: "All Notes Off",
}

# Mensagens de sistema "real-time" e "common" (byte de status 0xF_).
SYSTEM_MESSAGES = {
    0xF1: "MIDI Time Code (quarter frame)",
    0xF2: "Song Position Pointer",
    0xF3: "Song Select",
    0xF6: "Tune Request",
    0xF8: "Timing Clock",
    0xFA: "Start",
    0xFB: "Continue",
    0xFC: "Stop",
    0xFE: "Active Sensing",
    0xFF: "System Reset",
}


def note_name(note: int) -> str:
    """Ex.: 60 -> 'C4' (padrão em que o C central é C4)."""
    return f"{NOTE_NAMES[note % 12]}{note // 12 - 1}"


def describe(data: list[int]) -> str:
    """Descrição humana de uma mensagem MIDI. '' se não reconhecida."""
    if not data:
        return "(vazio)"

    status = data[0]
    high = status & 0xF0
    channel = (status & 0x0F) + 1  # canais MIDI são 1..16 para humanos

    if high == 0x80 and len(data) >= 3:
        n = data[1]
        return f"Note OFF  {n} ({note_name(n)})  vel {data[2]}  · canal {channel}"

    if high == 0x90 and len(data) >= 3:
        n, vel = data[1], data[2]
        if vel == 0:  # Note On com velocidade 0 = Note Off (convenção comum)
            return f"Note OFF  {n} ({note_name(n)})  (vel 0)  · canal {channel}"
        return f"Note ON   {n} ({note_name(n)})  vel {vel}  · canal {channel}"

    if high == 0xA0 and len(data) >= 3:
        n = data[1]
        return f"Poly Aftertouch  {n} ({note_name(n)})  pressão {data[2]}  · canal {channel}"

    if high == 0xB0 and len(data) >= 3:
        cc, value = data[1], data[2]
        name = CC_NAMES.get(cc, "controlador/knob")
        return f"Control Change  CC {cc} = {value}  [{name}]  · canal {channel}"

    if high == 0xC0 and len(data) >= 2:
        return f"Program Change  programa {data[1]}  · canal {channel}"

    if high == 0xD0 and len(data) >= 2:
        return f"Channel Aftertouch  pressão {data[1]}  · canal {channel}"

    if high == 0xE0 and len(data) >= 3:
        # 14 bits (LSB, MSB), centralizado em 8192.
        bend = (data[2] << 7 | data[1]) - 8192
        return f"Pitch Bend  {bend:+d}  (0 = centro)  · canal {channel}"

    # Mensagens de sistema (0xF0..0xFF): não têm canal.
    if status == 0xF0:
        return f"SysEx (início)  — {len(data)} bytes"
    if status in SYSTEM_MESSAGES:
        extra = ""
        if status == 0xF2 and len(data) >= 3:
            extra = f"  pos {(data[2] << 7 | data[1])}"
        elif status == 0xF3 and len(data) >= 2:
            extra = f"  song {data[1]}"
        return f"System: {SYSTEM_MESSAGES[status]}{extra}"

    return ""  # desconhecida


def raw(data: list[int]) -> str:
    """Bytes crus em hex e decimal, ex.: '90 3C 64  |  144 60 100'."""
    hex_part = " ".join(f"{b:02X}" for b in data)
    dec_part = " ".join(str(b) for b in data)
    return f"{hex_part}  |  {dec_part}"


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--all",
        action="store_true",
        help="também exibe clock, active-sensing e SysEx (por padrão são ignorados).",
    )
    p.add_argument(
        "--port",
        type=int,
        default=None,
        metavar="N",
        help="abre a porta pelo índice em vez de escolher a 1ª física.",
    )
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    # Garante que cada linha seja liberada na hora — mesmo se a saída for
    # redirecionada para arquivo/pipe (senão o Python usa buffer de bloco e
    # nada aparece até o processo encerrar).
    try:
        sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - stdout exótico
        pass

    # Criamos o MidiIn direto (não via alsa.create_midi_in) para poder controlar
    # o filtro de tipos conforme a flag --all.
    try:
        import rtmidi
    except ImportError:
        print("python-rtmidi indisponível. Rode dentro do .venv.", file=sys.stderr)
        return 1

    midi_in = rtmidi.MidiIn(name="Mini Synth Debug")
    show_system = args.all
    # Se --all, NÃO ignoramos nada; senão, ignoramos o "ruído" de sincronismo.
    midi_in.ignore_types(
        sysex=not show_system,
        timing=not show_system,
        active_sense=not show_system,
    )

    ports = alsa.list_input_ports(midi_in)
    if args.port is not None:
        target = next((p for p in ports if p.index == args.port), None)
        if target is None:
            print(f"Porta {args.port} não existe. Portas: {[(p.index, p.name) for p in ports]}")
            return 1
    else:
        target = alsa.choose_port(ports)

    if target is None:
        print("Nenhum teclado MIDI físico encontrado.")
        print("Portas vistas:", [(p.index, p.name) for p in ports])
        return 1

    try:
        midi_in.open_port(target.index, name="debug")
    except Exception as exc:
        print(f"Não foi possível abrir a porta '{target.name}': {exc}")
        print("O Mini Synth (ou outro app) está usando o teclado? Feche e tente de novo.")
        return 1
    print(f"Ouvindo: {target.name}  (porta {target.index})")
    if not show_system:
        print("Dica: use --all para ver também clock/active-sensing/SysEx.")
    print("Toque notas, gire knobs, use o pedal... Ctrl+C para encerrar.\n")
    print(f"{'tempo':>9}  {'RAW (hex | dec)':<34}  descrição")
    print("-" * 78)

    count = 0
    start = time.monotonic()
    try:
        while True:
            msg = midi_in.get_message()
            if msg is None:
                time.sleep(0.001)
                continue
            data, _delta = msg
            if not data:
                continue
            count += 1
            elapsed = time.monotonic() - start
            desc = describe(data) or "(comando desconhecido)"
            print(f"{elapsed:8.2f}s  {raw(data):<34}  {desc}")
    except KeyboardInterrupt:
        pass
    finally:
        midi_in.close_port()
        midi_in.delete()

    print(f"\nEncerrado. {count} mensagem(ns) recebida(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
