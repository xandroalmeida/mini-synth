# Neon Forge — regras do tema

## Objeto físico

Este tema representa o **Neon Forge KID/01**, um sintetizador de oficina
cyberpunk montado dentro de um chassi industrial reaproveitado. A interface é
vista de frente: titânio escurecido, grafite, acrílico fumê, cabos presos nas
bordas, parafusos, marcas de uso e luz de serviço ciano/magenta.

## Elementos permitidos

- Placas assimétricas usinadas, nervuras, parafusos Torx, grelhas e etiquetas
  técnicas curtas.
- Monitores de fósforo/ciano, trilhas de circuito, cabos e luzes de diagnóstico.
- Teclas de seleção como cartuchos físicos iluminados.
- Controles como pads mecânicos, arcos de calibração e uma trava de emergência.
- Textura raster local do chassi, gerada por IA e sem controles interativos
  pintados na imagem.

## Evitar

- Reaproveitar a arquitetura de rack do MS-90, o móvel/speaker/medidores do
  Tube 60 ou apenas trocar sua paleta.
- Skyline, personagens, chuva, kanji decorativo aleatório ou clichês de pôster.
- Telas holográficas flutuantes sem suporte físico.
- Neon em toda superfície: as luzes devem ter uma fonte e iluminar o material.
- Imagens externas, texto ilegível e decoração sobre áreas clicáveis.

## Comportamento

Preserve todos os IDs consumidos por `app.js`, as classes `.tab`, `.grid`,
`.inst` e `.pm`, e os estados `.selected`, `.connected`, `.searching` e
`.error`. A tela principal não tem menus nem dropdowns; selects pertencem
somente ao compartimento CONFIG.
