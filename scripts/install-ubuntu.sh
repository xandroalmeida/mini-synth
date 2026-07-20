#!/usr/bin/env bash
# Instala/verifica as dependências do Mini Synth em Ubuntu / Linux Mint e derivados.
#
# NÃO altera configurações globais de áudio: apenas instala pacotes e cria o
# ambiente virtual Python do projeto.
set -euo pipefail

cd "$(dirname "$0")/.."

BOLD="$(tput bold 2>/dev/null || true)"
RESET="$(tput sgr0 2>/dev/null || true)"

info()  { echo "${BOLD}==>${RESET} $*"; }
warn()  { echo "${BOLD}[!]${RESET} $*" >&2; }

APT_PACKAGES=(
    fluidsynth              # sintetizador (binário e serviço)
    libfluidsynth3          # biblioteca usada pelo pyfluidsynth
    fluid-soundfont-gm      # SoundFont General MIDI padrão
    alsa-utils              # aconnect, aplay, amidi
    libasound2-dev          # necessário para python-rtmidi (ALSA)
    python3                 # interpretador
    python3-venv            # ambientes virtuais
    python3-pip             # instalador de pacotes Python
    python3-gi              # PyGObject (backend GTK do pywebview)
    gir1.2-gtk-3.0          # bindings GTK 3
    gir1.2-webkit2-4.1      # WebKitGTK (renderiza a interface)
    pipewire-pulse          # saída de áudio (compatibilidade PulseAudio)
)

install_system_packages() {
    if ! command -v apt-get >/dev/null 2>&1; then
        warn "apt-get não encontrado. Instale manualmente: ${APT_PACKAGES[*]}"
        return
    fi
    info "Atualizando lista de pacotes (sudo)..."
    sudo apt-get update -qq

    info "Instalando dependências de sistema..."
    sudo apt-get install -y "${APT_PACKAGES[@]}"
}

check_tools() {
    info "Verificando ferramentas..."
    for tool in fluidsynth aconnect aplay python3; do
        if command -v "$tool" >/dev/null 2>&1; then
            echo "    ✓ $tool"
        else
            warn "    ✗ $tool NÃO encontrado"
        fi
    done
}

setup_venv() {
    info "Criando ambiente virtual Python em .venv (--system-site-packages)..."
    # O venv precisa enxergar o PyGObject (gi)/WebKitGTK do apt para o backend
    # GTK do pywebview funcionar. Se um .venv antigo (sem esse acesso) existir,
    # recria.
    if [ -d ".venv" ] && ! .venv/bin/python -c "import gi" >/dev/null 2>&1; then
        warn ".venv sem acesso ao 'gi' do sistema; recriando com --system-site-packages..."
        rm -rf .venv
    fi
    if [ ! -d ".venv" ]; then
        python3 -m venv --system-site-packages .venv
    fi
    # shellcheck disable=SC1091
    source .venv/bin/activate
    info "Instalando dependências Python..."
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
}

check_soundfont() {
    info "Procurando SoundFonts instaladas..."
    local found=0
    for dir in /usr/share/sounds/sf2 /usr/share/sounds/sf3 /usr/share/soundfonts "$HOME/SoundFonts"; do
        if ls "$dir"/*.sf2 "$dir"/*.sf3 >/dev/null 2>&1; then
            ls "$dir"/*.sf2 "$dir"/*.sf3 2>/dev/null | sed 's/^/    ✓ /'
            found=1
        fi
    done
    if [ "$found" -eq 0 ]; then
        warn "Nenhuma SoundFont encontrada. Instale 'fluid-soundfont-gm'."
    fi
}

main() {
    install_system_packages
    check_tools
    setup_venv
    check_soundfont
    echo
    info "Pronto! Para iniciar:  ${BOLD}./run.sh${RESET}"
}

main "$@"
