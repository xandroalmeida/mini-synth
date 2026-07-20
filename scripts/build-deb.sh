#!/usr/bin/env bash
# Gera o pacote .deb do Mini Synth (Ubuntu / Linux Mint e derivados).
#
# Estratégia: dependemos do apt para as bibliotecas pesadas (PySide6, rtmidi,
# PyYAML, libfluidsynth3, SoundFont) e EMBUTIMOS apenas o pyfluidsynth — um
# único módulo Python puro (MIT) que não tem pacote apt. Com isso o pacote é
# leve e "Architecture: all" (independente de arquitetura).
#
# Uso:   ./scripts/build-deb.sh
# Saída: dist/mini-synth_<versão>_all.deb
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

VERSION="1.1.0"
PKG="mini-synth"
ARCH="all"
MAINTAINER="Alexandro Almeida <xandroalmeida@gmail.com>"

BUILD="${ROOT}/build/deb"
STAGE="${BUILD}/${PKG}"
APPDIR="usr/share/${PKG}"          # onde o código vive dentro do pacote
DIST="${ROOT}/dist"

BOLD="$(tput bold 2>/dev/null || true)"; RESET="$(tput sgr0 2>/dev/null || true)"
info() { echo "${BOLD}==>${RESET} $*"; }

# --- localizar o pyfluidsynth (fluidsynth.py) para embutir --------------------
find_pyfluidsynth() {
    if [ -f "${ROOT}/.venv/lib/python3.12/site-packages/fluidsynth.py" ]; then
        echo "${ROOT}/.venv/lib/python3.12/site-packages/fluidsynth.py"; return
    fi
    # fallback: pergunta ao Python (venv ativo ou sistema)
    python3 - <<'PY' 2>/dev/null || true
import importlib.util as u
s = u.find_spec("fluidsynth")
print(s.origin if s and s.origin and s.origin.endswith(".py") else "")
PY
}

info "Limpando build anterior..."
rm -rf "${BUILD}"
mkdir -p "${STAGE}/DEBIAN"
mkdir -p "${STAGE}/${APPDIR}" \
         "${STAGE}/usr/bin" \
         "${STAGE}/usr/share/applications" \
         "${STAGE}/usr/share/icons/hicolor/256x256/apps" \
         "${STAGE}/usr/share/doc/${PKG}" \
         "${STAGE}/${APPDIR}/vendor"

info "Copiando aplicação (src, config, assets)..."
cp -r "${ROOT}/src"    "${STAGE}/${APPDIR}/"
cp -r "${ROOT}/config" "${STAGE}/${APPDIR}/"
cp -r "${ROOT}/assets" "${STAGE}/${APPDIR}/"
# remove caches de bytecode
find "${STAGE}/${APPDIR}" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "${STAGE}/${APPDIR}" -name '*.pyc' -delete 2>/dev/null || true

info "Embutindo pyfluidsynth (vendor)..."
PYFS="$(find_pyfluidsynth)"
if [ -z "${PYFS}" ] || [ ! -f "${PYFS}" ]; then
    echo "ERRO: não encontrei o fluidsynth.py (pyfluidsynth). Rode 'pip install pyfluidsynth' no .venv." >&2
    exit 1
fi
cp "${PYFS}" "${STAGE}/${APPDIR}/vendor/fluidsynth.py"

info "Criando lançador /usr/bin/${PKG}..."
cat > "${STAGE}/usr/bin/${PKG}" <<EOF
#!/bin/sh
# Lançador do Mini Synth (instalado via .deb).
APPDIR="/${APPDIR}"
# Roda de dentro do APPDIR para que 'python3 -m src.main' pegue o pacote
# instalado (e não algum 'src' do diretório atual). vendor/ traz o pyfluidsynth.
cd "\${APPDIR}" || exit 1
export PYTHONPATH="\${APPDIR}/vendor\${PYTHONPATH:+:\${PYTHONPATH}}"
exec python3 -m src.main "\$@"
EOF
chmod 0755 "${STAGE}/usr/bin/${PKG}"

info "Instalando atalho de menu e ícone..."
cat > "${STAGE}/usr/share/applications/${PKG}.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Mini Synth
GenericName=Instrumento Musical
Comment=Transforme seu teclado MIDI em um instrumento simples e divertido
Exec=${PKG}
Icon=${PKG}
Terminal=false
Categories=Audio;Music;AudioVideo;
Keywords=midi;piano;synth;fluidsynth;teclado;música;criança;
StartupNotify=true
EOF
cp "${ROOT}/assets/icon.png" "${STAGE}/usr/share/icons/hicolor/256x256/apps/${PKG}.png"

info "Copyright e changelog..."
cat > "${STAGE}/usr/share/doc/${PKG}/copyright" <<EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: Mini Synth

Files: *
Copyright: 2026 Alexandro Almeida
License: MIT

Files: ${APPDIR}/vendor/fluidsynth.py
Copyright: pyfluidsynth authors
License: MIT
Comment: pyfluidsynth (https://github.com/nwhitehead/pyfluidsynth) embutido por
 não haver pacote apt. A SoundFont NÃO é distribuída aqui (vem de
 'fluid-soundfont-gm' via Depends).
EOF
printf '%s (%s) unstable; urgency=low\n\n  * Bancos, bateria, navegação por knobs e memória por banco.\n\n -- %s  Thu, 01 Jan 1970 00:00:00 +0000\n' \
    "${PKG}" "${VERSION}" "${MAINTAINER}" | gzip -9 -n > "${STAGE}/usr/share/doc/${PKG}/changelog.Debian.gz"

# --- Installed-Size (KB) ------------------------------------------------------
ISIZE="$(du -s -k "${STAGE}/usr" | awk '{print $1}')"

info "Escrevendo DEBIAN/control..."
cat > "${STAGE}/DEBIAN/control" <<EOF
Package: ${PKG}
Version: ${VERSION}
Section: sound
Priority: optional
Architecture: ${ARCH}
Maintainer: ${MAINTAINER}
Installed-Size: ${ISIZE}
Depends: python3 (>= 3.10), python3-pyside6.qtcore, python3-pyside6.qtgui, python3-pyside6.qtwidgets, python3-rtmidi, python3-yaml, libfluidsynth3 | libfluidsynth2, fluid-soundfont-gm
Recommends: fluidsynth
Description: Instrumento MIDI simples para crianças (Mini Synth)
 Transforma um teclado controlador MIDI num instrumento musical simples,
 divertido e com aparência de equipamento de som dos anos 90. Feito para
 crianças: abrir, escolher um som e tocar.
 .
 Sons organizados em bancos (TECLAS, CORDAS, SOPROS, BATERIA...), navegação
 pelos knobs do teclado (A1 = banco, A3 = instrumento) e memória por banco.
EOF

# permissões corretas dos diretórios/arquivos
find "${STAGE}" -type d -exec chmod 0755 {} +
find "${STAGE}/${APPDIR}" -type f -exec chmod 0644 {} +
chmod 0644 "${STAGE}/usr/share/applications/${PKG}.desktop" \
           "${STAGE}/usr/share/icons/hicolor/256x256/apps/${PKG}.png" \
           "${STAGE}/usr/share/doc/${PKG}/copyright" \
           "${STAGE}/usr/share/doc/${PKG}/changelog.Debian.gz" \
           "${STAGE}/DEBIAN/control"
chmod 0755 "${STAGE}/usr/bin/${PKG}"

info "Construindo o pacote..."
mkdir -p "${DIST}"
DEB="${DIST}/${PKG}_${VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "${STAGE}" "${DEB}"

info "Pronto: ${DEB}"
echo
dpkg-deb -I "${DEB}"
