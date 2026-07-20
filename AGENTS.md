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
- **A interface é pywebview (backend GTK/WebKit).** O venv PRECISA ser criado
  com `python3 -m venv --system-site-packages` para enxergar o `gi` (PyGObject)
  e o WebKitGTK do apt; senão a janela não abre. Se o `.venv` não tiver esse
  acesso, rode `./scripts/install-ubuntu.sh` (ele detecta e recria) ou recrie à
  mão. pip instala só coisas leves (pywebview etc.).
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
python -m src.main            # ou ./run.sh   (janela 1100×720, ou fullscreen se configurado)
MINI_SYNTH_DEBUG=1 python -m src.main   # loga cada evento MIDI + erros de evaluate_js
pytest                        # 73 testes, sem hardware/áudio/gráfico real
python scripts/midi-debug.py     # bytes crus + descrição humana de cada comando MIDI
python scripts/midi-monitor.py   # resume os CCs de cada knob (gire um de cada vez)
```

- Testes usam `MockBackend` + um `rtmidi` falso; a UI é o `WebUiBridge` sem
  janela (guarda estado em Python). Nada de áudio/MIDI/gráfico real é necessário.
  A fixture `qapp` do `conftest.py` é um no-op (a UI é web, não precisa de
  contexto gráfico).
- `pyproject.toml` já define `pythonpath = ["."]`, então `pytest` acha `src/`.

## ⚠️ Armadilhas já pagas (não repita)

1. **Verificar a UI web: sirva os assets e abra no navegador.** A janela real é
   pywebview/WebKitGTK; o screenshot de janela via D-Bus do GNOME é **bloqueado**
   no Ubuntu 24.04. Para conferir o visual, rode `python -m http.server` em
   `assets/web/` e abra no Chrome (ou capture com WebKit `get_snapshot`, que
   exige o apt `python3-gi-cairo`). Para checar a integração real, rode
   `python -m src.main` com `MINI_SYNTH_DEBUG=1` e veja o log: **zero**
   `evaluate_js falhou` / `Can't find variable: MS` = a ponte está OK.
   ⚠️ pywebview: carregue via **`file://`** (`(WEB_DIR/'index.html').as_uri()`);
   o http server embutido dele dá **404 nos assets** (`app.js`/`style.css`).
2. **`pkill -f "src.main"` mata o próprio comando** (o wrapper do shell contém
   a string). Use o truque de regex: `pkill -f "[p]ython -m src.main"`.
3. **Botões/visor/LEDs são CSS + canvas** (`assets/web/style.css`, `app.js`).
   O VFD é a fonte 5×7 `_FONT` desenhada num `<canvas>` (`drawVfd`), com
   glow/scanlines/reflexo. Skeuomorfismo em CSS (gradiente + box-shadow +
   `:active`), **sem imagens externas**.
4. **O teclado troca o protocolo dos knobs conforme o modo/banco.** Os knobs já
   apareceram como CCs diferentes E como **Program Change** dependendo do modo.
   Por isso o app trata Program Change E CC. Não presuma um número fixo; confirme
   com o `midi-monitor.py` e/ou o log em modo DEBUG. Mapeamento confirmado deste
   teclado está na armadilha 6.
5. **Números de banco/programa MIDI só em `config/instruments.yaml`.** Nunca
   espalhe pelo código.
6. **Navegação por bancos:** A1 troca o **banco** (categoria), A3 troca o
   **instrumento** dentro do banco. Program Change do teclado (modo do A1)
   também troca o **banco** (`program_change_selects_bank`). Mapeamento é
   **direto** (`_knob_index`): cada valor de CC = um item (0→1º, 1→2º…) e trava
   no último acima da quantidade — os dois knobs usam a MESMA regra.
   **Mapeamento confirmado ao vivo deste teclado (8 knobs):**
   `A1 = Program Change → banco`, `A3 = CC 91 → instrumento`,
   `A4 = CC 93 → volume`, `B1 = CC 74 → oitava`, `B3 = CC 73 → reverb`,
   `B4 = CC 72 → none (livre)`. **A2 e B2 não emitem nada — provável defeito no
   hardware.** Use `scripts/midi-debug.py` (bytes crus + descrição) ou
   `midi-monitor.py` para reconferir; vários knobs mandam **Program Change
   (0xC0)** em vez de CC, então ambos os scripts mostram PC também.
7. **Bateria = percussão (`percussion: true`, GM bank 128).** Instrumentos de
   percussão tocam no **canal 9** (`DRUM_CHANNEL`), não no canal 0, e **sem
   transposição de oitava** (cada tecla é um som fixo de bateria). A troca de
   canal fica encapsulada em `Synthesizer.select_instrument`.

## Arquitetura (mapa rápido)

```
src/
  main.py            # logging, webview.create_window/start (pywebview GTK), ConfigError fatal
  application.py     # Application: liga config↔synth↔MIDI↔UI. Sem lógica de síntese/UI.
  audio/
    synthesizer.py       # Synthesizer (lógica musical, threading.RLock) + Protocol Backend
    factory.py           # create_backend("auto"|"fluidsynth"|"subprocess"|"mock")
    fluidsynth_backend.py subprocess_backend.py mock_backend.py
  midi/
    alsa.py              # funções PURAS de filtro de porta + wrapper rtmidi (testável)
    device_manager.py    # MidiDeviceManager: thread daemon 2s, Signal (util.signal), reconexão
  ui/
    web_bridge.py        # WebUiBridge: ponte p/ a UI web (API pública usada pelo Application).
                         #   Api (js_api p/ JS→Python) + evaluate_js('MS.…') p/ Python→JS.
  util/
    signal.py            # Signal síncrono (.connect/.emit)
  config/
    models.py            # dataclasses validadas (AppConfig, Instrument, ControlsConfig, UserSettings)
    loader.py            # YAML + persistência + busca de SoundFont
assets/web/            # A INTERFACE (HTML/CSS/JS).
  index.html           # 3 páginas: #page-main / #page-settings / #page-error
  style.css            # skeuomorfismo 90s: botões, faceplate, LEDs, parafusos (CSS puro)
  app.js               # namespace MS.* (chamado pelo Python); VFD dot-matrix 5x7 em <canvas>
```

### Fluxo MIDI (importante)

O app **intercepta** o MIDI (rtmidi), não deixa o teclado tocar direto no
FluidSynth. `device_manager` emite `Signal` (`note_on/off`, `control_change`,
`program_change`); `application` aplica **transposição de oitava** (exceto na
bateria) e roteia as notas para o **canal do instrumento atual** — canal 0 para
melódicos, canal 9 para percussão. Assim, qualquer canal do teclado toca o
instrumento escolhido. Knobs A1/A3 e Program Change trocam banco/instrumento na
UI (ver armadilhas 6 e 7).

Instrumentos vivem em **bancos** (`banks:` no `instruments.yaml`): cada banco é
uma categoria (TECLAS, SOPROS, BATERIA…). Na UI, uma fileira de abas no topo
troca o banco (o JS mostra uma `.grid` por banco; só a ativa aparece);
`AppConfig.instruments` continua achatando tudo numa lista. O formato antigo
(lista plana `instruments:`) ainda carrega — vira um banco "default".

**Threading**: o callback do rtmidi roda em thread própria e chama o
`Synthesizer` DIRETO — por isso o `Synthesizer` tem um `threading.RLock`. As
atualizações de UI vão por `window.evaluate_js('MS.…')`,
que o pywebview entrega em segurança (validado com evaluate_js de thread de
fundo). O `WebUiBridge` guarda o estado em Python, então tudo continua testável
sem janela.

## Convenções / o que NÃO quebrar

- Type hints em todo lugar; dataclasses validam a config (`models.py`).
- Tela principal: **sem menus, sem dropdowns**. Dropdown só na tela CONFIG.
- Erros na UI são **mensagens simples** + botão TENTAR NOVAMENTE; nunca
  stack trace. Detalhes vão para o log.
- Aparência: HTML/CSS + `<canvas>` (`assets/web/`), **sem imagens externas**.
- Persistência: `~/.config/mini-synth/settings.yaml`.
  Logs: `~/.local/state/mini-synth/mini-synth.log`.
- Ao mudar comportamento, atualize/estenda os testes (`tests/test_*.py`) e
  rode `pytest` antes de entregar.

## Memória entre sessões

Há notas persistidas em
`~/.claude/projects/-home-alexandro-Projetos-MusicBox/memory/`
(`musicbox-project.md`, `musicbox-environment.md`). Atualize-as quando descobrir
algo novo e durável sobre o projeto ou o ambiente.
