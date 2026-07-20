# 🎹 Mini Synth

Transforma um **teclado controlador MIDI** em um instrumento musical simples,
divertido e com a cara de um **equipamento de som dos anos 90** (skeuomórfico:
alumínio escovado, visor dot-matrix, botões físicos e LEDs).

Feito para **crianças**: abrir, clicar em um instrumento e tocar. Sem DAW, sem
timeline, sem gravação, sem menus, sem dropdowns na tela principal.

## ✨ O que ele faz

- Detecta **automaticamente** o teclado MIDI USB conectado.
- Carrega uma **SoundFont** `.sf2`/`.sf3`.
- Mostra **botões grandes** e troca de instrumento com **um clique**.
- Áudio de **baixa latência** via **FluidSynth** direto (sem Qsynth).
- Saída por **PipeWire/PulseAudio**.
- Controles físicos de **Volume**, **Reverb** e **Oitava**.
- Botão grande **PARAR SOM** (panic) para resolver notas travadas.
- **Knobs do teclado** podem trocar o instrumento (via Program Change ou CC).
- Tela **CONFIG** simples para trocar SoundFont, redetectar MIDI e testar o som.
- Funciona **mesmo sem teclado** conectado (mostra aviso e permite testar o som).
- Abre **maximizado** para aproveitar a tela toda.

## 🧱 Tecnologias

Python 3.12 · PySide6 · FluidSynth (libfluidsynth) · ALSA Sequencer (rtmidi) ·
PipeWire/PulseAudio · YAML · pytest.

O acesso ao FluidSynth é feito por uma **camada desacoplada** com três backends
intercambiáveis:

1. `fluidsynth_backend` — libfluidsynth (pyfluidsynth), **preferencial**;
2. `subprocess_backend` — processo externo `fluidsynth` (fallback);
3. `mock_backend` — para os testes automatizados.

Toda a aparência é feita com Qt Style Sheets + pintura à mão (QPainter) — **sem
imagens externas**. Os botões, o visor dot-matrix e os LEDs são desenhados por
código.

## 🚀 Instalação (Ubuntu / Linux Mint e derivados)

```bash
git clone <este-repositorio> mini-synth
cd mini-synth
./scripts/install-ubuntu.sh
```

O script instala/verifica: `fluidsynth`, `libfluidsynth3`, `fluid-soundfont-gm`,
`alsa-utils`, `libasound2-dev`, `python3`, `python3-venv`, `pipewire-pulse`, e
cria o ambiente virtual em `.venv` com as dependências Python.

> O script **não** altera configurações globais de áudio.

### Instalação manual (resumo)

```bash
sudo apt install fluidsynth libfluidsynth3 fluid-soundfont-gm \
                 alsa-utils libasound2-dev python3-venv pipewire-pulse
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## ▶️ Como executar

```bash
./run.sh
```

ou

```bash
source .venv/bin/activate
python -m src.main
```

Para depurar no terminal (mostra cada evento MIDI recebido):

```bash
MINI_SYNTH_DEBUG=1 python -m src.main
```

### Atalhos

- **F11** — alterna tela cheia.
- **Esc** — sai da tela cheia.

### Ícone de menu (opcional)

Edite os caminhos em `mini-synth.desktop` e copie:

```bash
cp mini-synth.desktop ~/.local/share/applications/
```

## ⚙️ Configuração

### Instrumentos e aparência — `config/instruments.yaml`

Os botões são montados **dinamicamente** a partir desse arquivo. Os números de
**banco/programa MIDI vivem somente aqui**, nunca no código:

```yaml
instruments:
  - id: grand_piano
    label: "PIANO"          # texto do botão
    display_name: "Grand Piano"
    bank: 0
    program: 0
```

Também define a `soundfont`, o `driver` de áudio, `gain`, `sample_rate`,
`buffer_size`, o auto-connect do MIDI e o número de `columns` da grade.

### Knobs do teclado (giratórios)

Muitos teclados baratos **mudam o que os knobs enviam** conforme o banco/modo
selecionado — o mesmo knob pode mandar **Program Change** num modo e
**Control Change (CC)** em outro. O Mini Synth trata os dois casos.

Descubra o que o seu teclado envia com o monitor:

```bash
python scripts/midi-monitor.py    # gire um knob de cada vez; Ctrl+C encerra
```

Configuração na seção `controls` de `config/instruments.yaml`:

```yaml
controls:
  # Program Change (modo comum do knob A1) troca o instrumento:
  #   valor 1 -> 1º instrumento ... 12 -> 12º; acima de 12 fica no último.
  program_change_selects_instrument: true

  # Knobs que enviam CC podem ser mapeados individualmente:
  knobs:
    - cc: 1
      action: instrument   # rola pelos instrumentos
```

Ações disponíveis: `instrument`, `volume`, `reverb`, `octave` e `none`.
CCs não mapeados (ex.: pedal de sustain, CC 64) seguem para o sintetizador.

### Preferências do usuário — `~/.config/mini-synth/settings.yaml`

Criado automaticamente. Persiste entre execuções: **volume, reverb, oitava,
último instrumento, última SoundFont, dispositivo MIDI preferido e tela cheia.**

### Logs — `~/.local/state/mini-synth/mini-synth.log`

A interface nunca mostra *stack traces*; mensagens de erro são simples e há um
botão **TENTAR NOVAMENTE** para erros recuperáveis.

## 🧪 Testes

Os testes **não** exigem teclado MIDI real nem servidor de áudio real (usam o
`MockBackend` e um rtmidi falso):

```bash
source .venv/bin/activate
pytest
```

Cobrem: seleção de instrumentos, banco/programa, volume, reverb, transposição de
oitava, panic, knobs (CC e Program Change), carregamento de configuração,
persistência e reconexão MIDI.

## 🛠️ Solução de problemas

| Sintoma | O que fazer |
|---|---|
| **"FluidSynth não está instalado"** | `sudo apt install fluidsynth libfluidsynth3` |
| **"SoundFont não encontrada"** | `sudo apt install fluid-soundfont-gm` ou escolha um `.sf2` na tela **CONFIG** |
| **"Teclado MIDI não encontrado"** | Conecte o teclado USB; o app redetecta a cada 2 s. Use **Detectar novamente** na CONFIG. Verifique com `aconnect -l` |
| **"Não foi possível iniciar o áudio"** | Confirme o PipeWire/Pulse ativo. Troque o `driver` em `instruments.yaml` para `alsa` |
| **Knob não troca o instrumento** | Rode `python scripts/midi-monitor.py`, veja o que o knob envia e ajuste `controls` no YAML |
| **Som travado** | Clique em **PARAR SOM** |
| **Sem som mesmo com o teclado** | Abra **CONFIG → Testar som** para isolar áudio de MIDI |
| **Latência alta** | Reduza `buffer_size` (ex.: 128) em `instruments.yaml` |

Verificações úteis:

```bash
aconnect -l          # portas MIDI (o teclado deve aparecer)
aplay -l             # placas de áudio
fluidsynth --version # instalação do FluidSynth
```

## 📁 Estrutura do projeto

```
src/
  main.py            application.py
  audio/   synthesizer.py  fluidsynth_backend.py  subprocess_backend.py  mock_backend.py  factory.py
  midi/    device_manager.py  alsa.py
  ui/      main_window.py  buttons.py  instrument_button.py  control_panel.py
           vfd.py  status_indicator.py  decorations.py  settings_window.py  styles.py
  config/  loader.py  models.py
config/  instruments.yaml
scripts/ install-ubuntu.sh  make-icon.py  midi-monitor.py
tests/   test_*.py
```

## 📜 Licença

MIT.
