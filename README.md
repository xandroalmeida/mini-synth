# 🎹 Mini Synth

Transforma um **teclado controlador MIDI** em um instrumento musical simples,
divertido e com a cara de um **equipamento de som clássico**. Há temas
skeuomórficos intercambiáveis: um módulo digital dos anos 90 e um receiver
valvulado dos anos 60.

Feito para **crianças**: abrir, clicar em um instrumento e tocar. Sem DAW, sem
timeline, sem gravação, sem menus, sem dropdowns na tela principal.

## ✨ O que ele faz

- Detecta **automaticamente** o teclado MIDI USB conectado.
- Carrega uma **SoundFont** `.sf2`/`.sf3`.
- Dezenas de sons organizados em **bancos** (categorias): TECLAS, CORDAS,
  SOPROS, MÁGICOS, SYNTH, **BATERIA** e DIVERTIDO. Abas no topo trocam o banco;
  **um clique** troca o instrumento — sem lotar a tela.
- **Bateria completa**: cada tecla vira um som de percussão (bumbo, caixa,
  pratos…), com vários kits (Padrão, Sala, Potente, Eletrônica, 808, Jazz).
- Áudio de **baixa latência** via **FluidSynth** direto (sem Qsynth).
- Saída por **PipeWire/PulseAudio**.
- Controles físicos de **Volume**, **Reverb** e **Oitava**.
- Botão grande **PARAR SOM** (panic) para resolver notas travadas.
- **Knobs do teclado**: A1 troca o **banco**, A2 troca o **instrumento** (via
  Program Change ou CC).
- Tela **CONFIG** simples para trocar SoundFont, redetectar MIDI, testar o som
  e escolher o tema visual.
- Funciona **mesmo sem teclado** conectado (mostra aviso e permite testar o som).
- Abre **maximizado** para aproveitar a tela toda.

## 🧱 Tecnologias

Python 3.12 · pywebview (GTK/WebKit) · FluidSynth (libfluidsynth) · ALSA
Sequencer (rtmidi) · PipeWire/PulseAudio · YAML · pytest.

O acesso ao FluidSynth é feito por uma **camada desacoplada** com três backends
intercambiáveis:

1. `fluidsynth_backend` — libfluidsynth (pyfluidsynth), **preferencial**;
2. `subprocess_backend` — processo externo `fluidsynth` (fallback);
3. `mock_backend` — para os testes automatizados.

A interface é uma página web (`assets/web/`) renderizada pelo **pywebview** no
WebKitGTK do sistema. `index.html` é apenas o host e `app.js` mantém o estado
e o contrato comportamental `MS.*`. Cada tema possui **template HTML e
stylesheet próprios** em `assets/web/themes/`, portanto pode alterar toda a
arquitetura física do aparelho, não apenas cores. Toda a aparência é HTML/CSS +
`<canvas>`, **sem imagens externas**. O tema pode ser trocado em tempo real
sem reiniciar áudio ou MIDI.

## 📦 Instalação via pacote .deb (recomendado para usuários)

Baixe o `mini-synth_<versão>_all.deb` e instale (**precisa de internet** na
instalação):

```bash
sudo apt install ./mini-synth_2.1.0_all.deb
```

Por que internet? O pacote leva apenas o código e, na instalação, cria um
ambiente Python isolado em `/opt/mini-synth/venv` (com `--system-site-packages`)
e baixa via **pip** apenas bibliotecas leves: `pywebview`, `python-rtmidi`,
`PyYAML` e `pyfluidsynth`. O resto vem do apt (`python3-gi`, `gir1.2-webkit2-4.1`
e `gir1.2-gtk-3.0` para a interface; `libfluidsynth3` e `fluid-soundfont-gm`
para o som), então o download da instalação é de poucos MB.

Depois é só abrir **Mini Synth** pelo menu de aplicativos. Para remover (também
apaga o venv): `sudo apt remove mini-synth`. O pacote é `Architecture: all`.

### Gerar o .deb a partir do código

```bash
./scripts/build-deb.sh           # gera dist/mini-synth_<versão>_all.deb
```

## 🚀 Instalação a partir do código (desenvolvimento)

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
**banco/programa MIDI vivem somente aqui**, nunca no código. Instrumentos ficam
agrupados em **bancos** (categorias); cada banco vira uma aba na tela principal:

```yaml
banks:
  - id: teclas
    label: "TECLAS"           # texto da aba
    instruments:
      - id: grand_piano
        label: "PIANO"        # texto do botão
        display_name: "Grand Piano"
        bank: 0
        program: 0
  - id: bateria
    label: "BATERIA"
    instruments:
      - id: drums_standard
        label: "PADRÃO"
        bank: 128             # GM: bank 128 = kit de percussão
        program: 0
        percussion: true      # toca no canal 9, cada tecla é um som de bateria
```

> Compatibilidade: uma lista plana `instruments:` (formato antigo) ainda
> funciona — vira um único banco. `percussion: true` marca kits de bateria.

Também define a `soundfont`, o `driver` de áudio, `gain`, `sample_rate`,
`buffer_size`, o auto-connect do MIDI e o número de `columns` da grade.

### Knobs do teclado (giratórios)

Muitos teclados baratos **mudam o que os knobs enviam** conforme o banco/modo
selecionado — o mesmo knob pode mandar **Program Change** num modo e
**Control Change (CC)** em outro. O Mini Synth trata os dois casos.

Descubra o que o seu teclado envia com os scripts de debug:

```bash
python scripts/midi-debug.py      # cada comando: bytes crus + descrição humana
python scripts/midi-monitor.py    # gire um knob de cada vez; resume os CCs
```

**Mapeamento confirmado deste teclado** (8 knobs; A2 e B2 estão com defeito):

| Knob | Envia | Ação no app |
|------|-------|-------------|
| A1 | Program Change | troca o **banco** |
| A2 | — (defeito) | — |
| A3 | CC 91 | troca o **instrumento** |
| A4 | CC 93 | **volume** |
| B1 | CC 74 | **oitava** |
| B2 | — (defeito) | — |
| B3 | CC 73 | **reverb** |
| B4 | CC 72 | livre (`none`) |

Configuração na seção `controls` de `config/instruments.yaml`:

```yaml
controls:
  # A1 envia Program Change e troca o BANCO:
  #   valor 1 -> 1º banco ... N -> N-ésimo; acima de N fica no último.
  program_change_selects_bank: true

  # Knobs que enviam CC são mapeados individualmente:
  knobs:
    - cc: 91
      action: instrument   # A3 rola pelos instrumentos do banco atual
    - cc: 93
      action: volume       # A4
```

Ações disponíveis: `bank`, `instrument`, `volume`, `reverb`, `octave` e `none`.
CCs não mapeados (ex.: pedal de sustain, CC 64) seguem para o sintetizador.
Os CCs dependem do teclado — confirme com `midi-debug.py` e ajuste.

### Preferências do usuário — `~/.config/mini-synth/settings.yaml`

Criado automaticamente. Persiste entre execuções: **volume, reverb, oitava,
último instrumento, último banco, o último instrumento usado em CADA banco
(volta de onde parou), última SoundFont, dispositivo MIDI preferido, tela
cheia e **último tema visual selecionado**.

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

Cobrem: seleção de instrumentos, bancos (agrupamento + navegação A1/A2),
banco/programa, **percussão no canal 9**, volume, reverb, transposição de
oitava, panic, knobs (CC e Program Change), carregamento de configuração,
persistência, temas visuais e reconexão MIDI.

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
  ui/      web_bridge.py      # ponte Python↔interface web (pywebview)
           themes.py          # registro e validação dos temas disponíveis
  util/    signal.py          # Signal síncrono (.connect/.emit)
  config/  loader.py  models.py
assets/web/  index.html  style.css  app.js   # host, defaults e estado comum
             themes/                    # UIs completas e independentes
               ms90-template.js         # arquitetura do rack digital
               ms90.css                 # materiais do rack anos 90
               tube60-template.js       # arquitetura do móvel valvulado
               tube60.css               # materiais do aparelho anos 60
config/  instruments.yaml
scripts/ install-ubuntu.sh  build-deb.sh  make-icon.py  midi-monitor.py  midi-debug.py
tests/   test_*.py
```

## 📜 Licença

MIT.
