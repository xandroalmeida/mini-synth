# AGENTS.md — tema Tube 60

Instruções locais para qualquer alteração dentro deste diretório. Elas
complementam o `AGENTS.md` da raiz; em caso de dúvida visual ou histórica sobre
o Tube 60, este arquivo é a fonte de verdade.

## Conceito físico

O Tube 60 é um **móvel musical valvulado dos anos 60**, inspirado em consoles
domésticos, radiolas e órgãos elétricos da época. Não é o MS-90 recolorido e
não é uma interface digital coberta de madeira. Sua arquitetura própria combina
gabinete, tecido de alto-falante, painel central, baia de válvulas, teclas de
marfim/resina, joias luminosas, latão e placas de serviço.

Skeuomorphism e coerência histórica são requisitos. Cada detalhe deve sugerir
como seria construído, iluminado e operado fisicamente entre 1958 e 1968.

## Elementos permitidos e obrigatórios

- Nome da voz em **tambor eletromecânico de celuloide claro**, com tinta escura,
  volume cilíndrico, moldura, escala impressa e cursor vermelho móvel.
- Ao trocar de instrumento, a etiqueta anterior sai verticalmente e a próxima
  entra no sentido da navegação. O cursor acompanha a posição real dentro do
  banco e a escala adapta a quantidade de marcas. Preserve
  `prefers-reduced-motion`.
- Volume, ambiente e oitava em medidores analógicos com escala e ponteiro.
- Madeira com veio, tecido, marfim envelhecido, latão, vidro, válvulas e luz
  incandescente quente com origem física clara.
- Botões com curso mecânico e seleção semelhante a lâmpada interna, nunca um
  preenchimento plano.
- CONFIG como painel de serviço próprio do móvel, não como rack digital.

- Materiais fotográficos locais gerados por IA são permitidos para representar
  superfícies físicas reais, desde que não contenham controles interativos
  pintados. Os assets canônicos ficam em `assets/`: `walnut-veneer.png` para o
  móvel, `speaker-cloth.png` para a tela acústica e `valve-bay.png` para o
  compartimento valvulado. CSS/HTML continuam responsáveis por molduras,
  estados, texto e interação.
## Anacronismos proibidos

- **Nenhum `<canvas>` neste template.** Não usar VFD, LCD, LED numérico,
  dot-matrix, pixels apagados, texto emissivo, scanlines ou display preto.
- Não simular um display moderno apenas trocando fonte, cor ou moldura.
- Não usar faceplate industrial anos 90, botões de rack, neon ou estética de
  software/DAW.
- Não copiar a hierarquia HTML nem as classes visuais do MS-90.
- Não usar imagens externas.

Joias luminosas de estado e filamentos de válvula são permitidos porque são
luzes físicas plausíveis. Texto de instrumento luminoso não é.

## Contrato com o core

`template.js` registra `window.MS_THEME_TEMPLATES.tube60`. `style.css` contém
somente a identidade visual e as animações mecânicas deste aparelho. Estado,
eventos, cálculo do cursor e rolagem do tambor continuam em `../../app.js`.

O template precisa preservar os IDs e hooks usados pelo core: páginas
`page-main`, `page-settings`, `page-error`; `bank-tabs`, `grid-stack`,
`instrument-indicator`, `indicator-volume`, `indicator-reverb`,
`indicator-octave`; LEDs, botões, campos de ajustes e mensagem de erro. As
classes `.tab`, `.inst` e `.pm` e seus atributos `data-*` também são
comportamentais. Se um hook mudar, ajuste `app.js`, o outro tema e os testes na
mesma alteração.

O tambor usa `data-indicator="mechanical"`; os medidores usam
`data-indicator="analog"`, `data-min` e `data-max`. Não duplique estado ou
chamadas Python dentro do tema.

## Validação mínima

```bash
node --check assets/web/themes/tube60/template.js
node --check assets/web/app.js
source .venv/bin/activate && pytest
```

Renderize em 1100×720 e verifique painel principal, CONFIG e erro. Troque entre
o primeiro e o último instrumento e depois volte: o tambor deve girar nos dois
sentidos e o cursor precisa percorrer as marcas. Confirme também a troca
MS-90 → Tube 60 sem perda de estado e ausência total de `<canvas>` no template.
