# AGENTS.md — tema MS-90

Instruções locais para qualquer alteração dentro deste diretório. Elas
complementam o `AGENTS.md` da raiz; em caso de dúvida visual sobre o MS-90,
este arquivo é a fonte de verdade.

## Conceito físico

O MS-90 é um **módulo digital de rack / mini system hi-fi dos anos 90**, não
uma página web escura. A composição deve parecer um aparelho fabricado entre
1990 e 1998: faceplate metálico, módulos encaixados, parafusos, frisos,
serigrafia técnica, VFD verde-azulado, LEDs e teclas de resina translúcida.

Skeuomorphism é obrigatório. Todo controle precisa comunicar material,
profundidade, curso físico, reflexão e estado. Não aceite uma solução que seja
apenas retângulos planos, cores neon ou sombras genéricas.

## Elementos permitidos e obrigatórios

- VFD dot-matrix 5×7 em `<canvas>`, incluindo fósforo apagado em **toda a área
  física do visor**, scanlines discretas, reflexo de vidro e glow contido.
- Botões semitransparentes com luz interna/traseira. O estado selecionado deve
  parecer uma lâmpada acesa dentro da peça, não apenas uma troca de cor.
- Estado `:active` com deslocamento, compressão de sombra e sensação de clique.
- LEDs, metal escovado, plástico fumê, parafusos, juntas e molduras de rack.
- Arquitetura horizontal e modular legível em 1100×720 e no monitor 1280×800.

## Não introduzir

- Madeira, tecido de alto-falante antigo, latão ornamental, válvulas aparentes,
  escalas de rádio, tambores mecânicos ou medidores de ponteiro do Tube 60.
- Gradientes/glow sem uma fonte física plausível.
- Imagens externas, menus, dropdowns na tela principal ou linguagem de DAW.
- Reaproveitamento do markup ou das classes visuais do Tube 60.

## Contrato com o core

`template.js` registra `window.MS_THEME_TEMPLATES.ms90`. `style.css` contém
somente a identidade visual deste aparelho. Estado, eventos e dados continuam
em `../../app.js`.

O template precisa preservar os IDs e hooks usados pelo core: páginas
`page-main`, `page-settings`, `page-error`; `bank-tabs`, `grid-stack`,
`instrument-indicator`, `indicator-volume`, `indicator-reverb`,
`indicator-octave`; LEDs, botões, campos de ajustes e mensagem de erro. As
classes `.tab`, `.inst` e `.pm` e seus atributos `data-*` também são
comportamentais. Se um hook mudar, ajuste `app.js`, o outro tema e os testes na
mesma alteração.

O `<canvas>` sem `data-indicator` é deliberado: `renderIndicator` o interpreta
como VFD. Não mova fonte 5×7, estado global ou chamadas Python para este tema.

## Validação mínima

```bash
node --check assets/web/themes/ms90/template.js
node --check assets/web/app.js
source .venv/bin/activate && pytest
```

Além dos testes, renderize a UI no navegador em 1100×720. Confirme o painel
principal, CONFIG, estados selecionado/pressionado, matriz apagada em todo o
visor e a troca Tube 60 → MS-90 sem perda do instrumento ou dos controles.
