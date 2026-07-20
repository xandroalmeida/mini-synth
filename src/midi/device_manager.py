"""Detecção, conexão e monitoramento de dispositivos MIDI.

Responsabilidades (todas fora da thread da interface, exceto os sinais Qt, que
são entregues de forma segura à thread da UI):

* listar portas ALSA MIDI (via rtmidi);
* identificar portas físicas e ignorar as virtuais / do próprio FluidSynth;
* detectar conexão e desconexão;
* reconectar automaticamente (varredura a cada 2 s);
* expor o estado para a interface por meio de sinais Qt.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QTimer, Signal

from . import alsa
from .alsa import MidiPort

logger = logging.getLogger(__name__)

POLL_INTERVAL_MS = 2000

# Estados expostos para os indicadores da interface.
STATE_SEARCHING = "searching"  # amarelo
STATE_CONNECTED = "connected"  # verde
STATE_ERROR = "error"          # vermelho


class MidiDeviceManager(QObject):
    """Gerencia a porta MIDI física e encaminha eventos para o app."""

    #: (estado, mensagem legível) — para o indicador de status.
    status_changed = Signal(str, str)
    #: nota, velocidade
    note_on = Signal(int, int)
    #: nota
    note_off = Signal(int)
    #: controle, valor
    control_change = Signal(int, int)
    #: número do programa (Program Change)
    program_change = Signal(int)

    def __init__(self, preferred_device: str = "", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._preferred = preferred_device
        self._midi_in = alsa.create_midi_in()
        self._open_port: MidiPort | None = None
        self._state = STATE_SEARCHING
        self._timer = QTimer(self)
        self._timer.setInterval(POLL_INTERVAL_MS)
        self._timer.timeout.connect(self._poll)

    # ---- API pública ---------------------------------------------------
    @property
    def state(self) -> str:
        return self._state

    @property
    def connected_device(self) -> str:
        return self._open_port.name if self._open_port else ""

    def set_preferred_device(self, name: str) -> None:
        self._preferred = name or ""

    def start(self) -> None:
        """Inicia o monitoramento e tenta uma primeira conexão imediata."""
        if self._midi_in is None:
            self._set_state(STATE_ERROR, "MIDI indisponível neste sistema")
            return
        self._poll()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()
        self._close_port()
        if self._midi_in is not None:
            try:
                self._midi_in.delete()  # type: ignore[attr-defined]
            except Exception:  # pragma: no cover
                pass
            self._midi_in = None

    def list_ports(self) -> list[MidiPort]:
        if self._midi_in is None:
            return []
        return alsa.list_input_ports(self._midi_in)

    def rescan(self) -> None:
        """Força uma nova detecção imediatamente (botão 'Detectar novamente')."""
        logger.info("Redetecção de MIDI solicitada.")
        self._poll()

    # ---- lógica interna ------------------------------------------------
    def _poll(self) -> None:
        if self._midi_in is None:
            return
        ports = self.list_ports()

        # A porta aberta ainda existe?
        if self._open_port is not None:
            still_present = any(p.name == self._open_port.name for p in ports)
            if not still_present:
                logger.info("Dispositivo MIDI desconectado: %s", self._open_port.name)
                self._close_port()
                self._set_state(STATE_SEARCHING, "Procurando teclado MIDI...")
            else:
                return  # tudo certo, nada a fazer

        target = alsa.choose_port(ports, self._preferred)
        if target is None:
            self._set_state(STATE_SEARCHING, "Teclado MIDI não encontrado")
            return
        self._open(target)

    def _open(self, port: MidiPort) -> None:
        assert self._midi_in is not None
        try:
            self._midi_in.open_port(port.index, name="in")  # type: ignore[attr-defined]
            self._midi_in.set_callback(self._on_midi)        # type: ignore[attr-defined]
        except Exception as exc:  # pragma: no cover - depende do hardware
            logger.error("Falha ao abrir porta MIDI '%s': %s", port.name, exc)
            self._set_state(STATE_ERROR, "Não foi possível abrir o teclado")
            return
        self._open_port = port
        logger.info("Teclado MIDI conectado: %s", port.name)
        self._set_state(STATE_CONNECTED, port.name)

    def _close_port(self) -> None:
        if self._midi_in is not None and self._open_port is not None:
            try:
                self._midi_in.cancel_callback()   # type: ignore[attr-defined]
                self._midi_in.close_port()        # type: ignore[attr-defined]
            except Exception:  # pragma: no cover
                pass
        self._open_port = None

    def _set_state(self, state: str, message: str) -> None:
        if state != self._state or state != STATE_CONNECTED:
            self._state = state
            self.status_changed.emit(state, message)

    def _on_midi(self, event: tuple, _data: object = None) -> None:
        """Callback do rtmidi (roda em thread própria). Faz o parse e emite."""
        message, _delta = event
        if not message:
            return
        status = message[0] & 0xF0
        logger.debug("MIDI in: %s", [hex(b) for b in message])
        if status == 0x90 and len(message) >= 3:  # Note On
            note, velocity = message[1], message[2]
            if velocity == 0:
                self.note_off.emit(note)
            else:
                self.note_on.emit(note, velocity)
        elif status == 0x80 and len(message) >= 2:  # Note Off
            self.note_off.emit(message[1])
        elif status == 0xB0 and len(message) >= 3:  # Control Change
            logger.debug("MIDI CC %d = %d", message[1], message[2])
            self.control_change.emit(message[1], message[2])
        elif status == 0xC0 and len(message) >= 2:  # Program Change
            logger.debug("MIDI Program Change %d", message[1])
            self.program_change.emit(message[1])
