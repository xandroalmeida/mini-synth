# AGENTS.md — guia para agentes de IA

Contexto operacional para trabalhar neste repositório de forma eficaz. Leia
antes de editar. Complementa o `README.md` (voltado a humanos); aqui ficam os
detalhes não óbvios e as armadilhas já descobertas.

## O que é

**Mini Synth**: app desktop (Linux) que transforma um teclado controlador MIDI
num instrumento simples para **crianças**. Estética skeuomórfica de equipamento
de som dos anos 90. NÃO é uma DAW: sem timeline, sem gravação, sem menus, sem
dropdowns na tela principal. Simplicidade é requisito, não preguiça.

## Ambiente desta máquina (verificado)

- **Python 3.12**, use SEMPRE o venv do projeto: `source .venv/bin/activate`.
  O Python do sistema não tem `pip` nem as dependências.
- **`fluidsynth` (binário CLI) NÃO está instalado**; só a `libfluidsynth3`.
  Logo, o backend padrão é o `fluidsynth_backend` (pyfluidsynth). O
  `subprocess_backend` só funciona se `apt install fluidsynth`.
- Áudio: **PipeWire + pipewire-pulse**. FluidSynth não tem driver `pipewire`
  nativo aqui → use o driver **`pulseaudio`** (funciona sobre o PipeWire).
  Drivers disponíveis: `alsa, jack, pulseaudio, sdl2`.
- Sessão gráfica: **Wayland (GNOME), monitor 1280×800** (1x, sem HiDPI).
- SoundFont disponível: `/usr/share/sounds/sf2/FluidR3_GM.sf2`.
- Teclado: genérico **Holtek (USB 04d9:e000)**, nome ALSA `MidiKeyboard`
  (client 20). Pode existir um `FLUID Synth` residual (qsynth) — é filtrado
  pelo nome; nunca conectar nele.

## Rodar, testar, depurar

```bash
source .venv/bin/activate
python -m src.main            # ou ./run.sh   (abre MAXIMIZADO)
MINI_SYNTH_DEBUG=1 python -m src.main   # loga cada evento MIDI no terminal
pytest                        # 58 testes, sem hardware/áudio real
python scripts/midi-monitor.py   # descobre o que cada knob/tecla envia
```

- Testes rodam com `QT_QPA_PLATFORM=offscreen` (setado no `conftest.py`) e usam
  `MockBackend` + um `rtmidi` falso. Nada de áudio/MIDI real é necessário.
- `pyproject.toml` já define `pythonpath = ["."]`, então `pytest` acha `src/`.

## ⚠️ Armadilhas já pagas (não repita)

1. **Verificar a UI: use captura da JANELA REAL, no tamanho real.**
   `widget.grab()` offscreen num tamanho arbitrário **engana** — a janela real
   abre no tamanho que o WM dá. Sem `showMaximized`, ela abre no **mínimo
   (900×540)** e aperta tudo. Para conferir de verdade, rode com a plataforma
   real (sem offscreen), deixe a janela abrir/maximizar e só então
   `ctrl.window.grab().save(...)`. Depois **abra o PNG e olhe criticamente.**
2. **`pkill -f "src.main"` mata o próprio comando** (o wrapper do shell contém
   a string). Use o truque de regex: `pkill -f "[p]ython -m src.main"`.
3. **Botões físicos são pintados à mão** (`src/ui/buttons.py`, `PanelButton`),
   NÃO com `border: outset` do QSS (fica chapado e "encavala"). Cada botão
   reserva margem interna para a sombra projetada; ajuste espaçamentos de
   layout junto com essa margem para não colar as fileiras.
4. **O teclado troca o protocolo dos knobs conforme o banco.** O mesmo knob A1
   já apareceu como CC 91, CC 1 e **Program Change**. Por isso o app trata
   Program Change E CC. Não presuma um número fixo; confirme com o
   `midi-monitor.py` e/ou o log em modo DEBUG.
5. **Números de banco/programa MIDI só em `config/instruments.yaml`.** Nunca
   espalhe pelo código.

## Arquitetura (mapa rápido)

```
src/
  main.py            # logging, QApplication, stylesheet, trata ConfigError fatal
  application.py     # Application: liga config↔synth↔MIDI↔UI. Sem lógica de síntese/UI.
  audio/
    synthesizer.py       # Synthesizer (lógica musical) + Protocol SynthesizerBackend
    factory.py           # create_backend("auto"|"fluidsynth"|"subprocess"|"mock")
    fluidsynth_backend.py subprocess_backend.py mock_backend.py
  midi/
    alsa.py              # funções PURAS de filtro de porta + wrapper rtmidi (testável)
    device_manager.py    # MidiDeviceManager(QObject): QTimer 2s, sinais Qt, reconexão
  ui/
    main_window.py       # QStackedWidget: principal / CONFIG / erro. Fullscreen, Esc.
    buttons.py           # PanelButton (skeuomorfismo real, QPainter)
    vfd.py               # VfdDisplay (dot-matrix 5x7 pintado, glow, scanlines)
    instrument_button.py control_panel.py status_indicator.py decorations.py styles.py
  config/
    models.py            # dataclasses validadas (AppConfig, Instrument, ControlsConfig, UserSettings)
    loader.py            # YAML + persistência + busca de SoundFont
```

### Fluxo MIDI (importante)

O app **intercepta** o MIDI (rtmidi), não deixa o teclado tocar direto no
FluidSynth. `device_manager` emite sinais Qt (`note_on/off`, `control_change`,
`program_change`); `application` aplica **transposição de oitava** e roteia tudo
para o **canal 0** do synth (assim, qualquer canal do teclado toca o instrumento
escolhido). Program Change / CC mapeados trocam o instrumento na UI.

Sinais Qt emitidos da thread do rtmidi chegam à thread da UI por conexão
enfileirada (funciona; já testado cross-thread).

## Convenções / o que NÃO quebrar

- Type hints em todo lugar; dataclasses validam a config (`models.py`).
- Tela principal: **sem menus, sem dropdowns**. Dropdown só na tela CONFIG.
- Erros na UI são **mensagens simples** + botão TENTAR NOVAMENTE; nunca
  stack trace. Detalhes vão para o log.
- Aparência: só QSS + QPainter, **sem imagens externas**.
- Persistência: `~/.config/mini-synth/settings.yaml`.
  Logs: `~/.local/state/mini-synth/mini-synth.log`.
- Ao mudar comportamento, atualize/estenda os testes (`tests/test_*.py`) e
  rode `pytest` antes de entregar.

## Memória entre sessões

Há notas persistidas em
`~/.claude/projects/-home-alexandro-Projetos-MusicBox/memory/`
(`musicbox-project.md`, `musicbox-environment.md`). Atualize-as quando descobrir
algo novo e durável sobre o projeto ou o ambiente.
