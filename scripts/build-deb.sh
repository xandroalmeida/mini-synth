#!/usr/bin/env bash
# Gera o pacote .deb do Mini Synth (Ubuntu / Linux Mint e derivados).
#
# Estratégia: a interface usa pywebview no backend GTK/WebKit. O WebKitGTK e o
# PyGObject (gi) vêm de pacotes APT do sistema (Depends), então o venv é criado
# com --system-site-packages e o pip instala apenas dependências leves
# (pywebview, python-rtmidi, PyYAML, pyfluidsynth). O pacote fica pequeno,
# "Architecture: all", e o download da instalação é de poucos MB.
# Requisito: INTERNET no momento da instalação (pip).
#
# Uso:   ./scripts/build-deb.sh
# Saída: dist/mini-synth_<versão>_all.deb
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

VERSION="2.2.0"
PKG="mini-synth"
ARCH="all"
MAINTAINER="Alexandro Almeida <xandroalmeida@gmail.com>"

# Dependências Python instaladas via pip no postinst (leves; o WebKitGTK/gi vêm
# do apt via Depends, ver DEBIAN/control).
PYDEPS="pywebview>=5.0 python-rtmidi>=1.5 PyYAML>=6.0 pyfluidsynth>=1.3.3"

BUILD="${ROOT}/build/deb"
STAGE="${BUILD}/${PKG}"
APPDIR="usr/share/${PKG}"          # onde o código vive dentro do pacote
VENVDIR="/opt/${PKG}/venv"         # venv criado no alvo (postinst)
DIST="${ROOT}/dist"

BOLD="$(tput bold 2>/dev/null || true)"; RESET="$(tput sgr0 2>/dev/null || true)"
info() { echo "${BOLD}==>${RESET} $*"; }

info "Limpando build anterior..."
rm -rf "${BUILD}"
mkdir -p "${STAGE}/DEBIAN" \
         "${STAGE}/${APPDIR}" \
         "${STAGE}/usr/bin" \
         "${STAGE}/usr/share/applications" \
         "${STAGE}/usr/share/icons/hicolor/256x256/apps" \
         "${STAGE}/usr/share/doc/${PKG}"

info "Copiando aplicação (src, config, assets)..."
cp -r "${ROOT}/src"    "${STAGE}/${APPDIR}/"
cp -r "${ROOT}/config" "${STAGE}/${APPDIR}/"
cp -r "${ROOT}/assets" "${STAGE}/${APPDIR}/"
find "${STAGE}/${APPDIR}" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "${STAGE}/${APPDIR}" -name '*.pyc' -delete 2>/dev/null || true

info "Criando lançador /usr/bin/${PKG}..."
cat > "${STAGE}/usr/bin/${PKG}" <<EOF
#!/bin/sh
# Lançador do Mini Synth (instalado via .deb).
APPDIR="/${APPDIR}"
VENV="${VENVDIR}"
if [ ! -x "\${VENV}/bin/python" ]; then
    echo "Mini Synth: ambiente Python ausente. Reinstale com:" >&2
    echo "  sudo apt install --reinstall ${PKG}" >&2
    exit 1
fi
cd "\${APPDIR}" || exit 1
exec "\${VENV}/bin/python" -m src.main "\$@"
EOF
chmod 0755 "${STAGE}/usr/bin/${PKG}"

info "Escrevendo maintainer scripts (postinst/postrm)..."
cat > "${STAGE}/DEBIAN/postinst" <<EOF
#!/bin/sh
set -e
VENV="${VENVDIR}"
PYDEPS="${PYDEPS}"

case "\$1" in
  configure)
    echo "Mini Synth: preparando ambiente Python em \${VENV} (requer internet)..."
    # --system-site-packages: o venv precisa enxergar o PyGObject (gi) e o
    # WebKitGTK instalados via apt; sem isso o backend GTK do pywebview não sobe.
    if [ ! -x "\${VENV}/bin/python" ]; then
        python3 -m venv --system-site-packages "\${VENV}"
    fi
    "\${VENV}/bin/python" -m pip install --upgrade pip
    # shellcheck disable=SC2086
    "\${VENV}/bin/python" -m pip install \${PYDEPS}
    command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q || true
    command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -qtf /usr/share/icons/hicolor || true
    echo "Mini Synth: pronto. Abra pelo menu de aplicativos."
    ;;
esac
exit 0
EOF

cat > "${STAGE}/DEBIAN/postrm" <<EOF
#!/bin/sh
set -e
case "\$1" in
  remove|purge)
    rm -rf /opt/${PKG}
    command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q || true
    ;;
esac
exit 0
EOF
chmod 0755 "${STAGE}/DEBIAN/postinst" "${STAGE}/DEBIAN/postrm"

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

Comment: As dependências Python (pywebview, python-rtmidi, PyYAML, pyfluidsynth)
 são instaladas via pip no momento da instalação, num venv com
 --system-site-packages em ${VENVDIR}. O WebKitGTK/PyGObject vêm do apt
 (Depends). A SoundFont vem do pacote apt 'fluid-soundfont-gm' (Depends).
EOF
printf '%s (%s) unstable; urgency=low\n\n  * Novo tema industrial cyberpunk Neon Forge e restauração fotográfica do Tube 60.\n\n -- %s  Thu, 01 Jan 1970 00:00:00 +0000\n' \
    "${PKG}" "${VERSION}" "${MAINTAINER}" | gzip -9 -n > "${STAGE}/usr/share/doc/${PKG}/changelog.Debian.gz"

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
Depends: python3 (>= 3.10), python3-venv, python3-pip, python3-gi, gir1.2-gtk-3.0, gir1.2-webkit2-4.1, libfluidsynth3 | libfluidsynth2, fluid-soundfont-gm
Recommends: fluidsynth
Description: Instrumento MIDI simples para crianças (Mini Synth)
 Transforma um teclado controlador MIDI num instrumento musical simples,
 divertido e com temas skeuomórficos de equipamentos de som históricos. Feito para
 crianças: abrir, escolher um som e tocar.
 .
 Sons organizados em bancos (TECLAS, CORDAS, SOPROS, BATERIA...), navegação
 pelos knobs do teclado (A1 = banco, A3 = instrumento), memória por banco e
 escolha persistente entre os temas MS-90, Tube 60 e Neon Forge.
 .
 A interface usa pywebview sobre o WebKitGTK do sistema (gir1.2-webkit2-4.1).
 Bibliotecas Python leves (pywebview, python-rtmidi, PyYAML, pyfluidsynth) são
 instaladas via pip na instalação; é necessária conexão com a internet.
EOF

find "${STAGE}" -type d -exec chmod 0755 {} +
find "${STAGE}/${APPDIR}" -type f -exec chmod 0644 {} +
chmod 0644 "${STAGE}/usr/share/applications/${PKG}.desktop" \
           "${STAGE}/usr/share/icons/hicolor/256x256/apps/${PKG}.png" \
           "${STAGE}/usr/share/doc/${PKG}/copyright" \
           "${STAGE}/usr/share/doc/${PKG}/changelog.Debian.gz" \
           "${STAGE}/DEBIAN/control"
chmod 0755 "${STAGE}/usr/bin/${PKG}" "${STAGE}/DEBIAN/postinst" "${STAGE}/DEBIAN/postrm"

info "Construindo o pacote..."
mkdir -p "${DIST}"
DEB="${DIST}/${PKG}_${VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "${STAGE}" "${DEB}"

info "Pronto: ${DEB}"
echo
dpkg-deb -I "${DEB}"
