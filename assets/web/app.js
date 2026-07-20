"use strict";

/* ======================================================================
   Fonte 5x7 do visor (portada de src/ui/vfd.py). '#' = ponto aceso.
   ====================================================================== */
const FONT = {
  " ": ["     ","     ","     ","     ","     ","     ","     "],
  "-": ["     ","     ","     ","#####","     ","     ","     "],
  "+": ["     ","  #  ","  #  ","#####","  #  ","  #  ","     "],
  ".": ["     ","     ","     ","     ","     "," ##  "," ##  "],
  ":": ["     "," ##  "," ##  ","     "," ##  "," ##  ","     "],
  "/": ["    #","    #","   # ","  #  "," #   ","#    ","#    "],
  "0": [" ### ","#   #","#  ##","# # #","##  #","#   #"," ### "],
  "1": ["  #  "," ##  ","  #  ","  #  ","  #  ","  #  "," ### "],
  "2": [" ### ","#   #","    #","   # ","  #  "," #   ","#####"],
  "3": ["#####","   # ","  #  ","   # ","    #","#   #"," ### "],
  "4": ["   # ","  ## "," # # ","#  # ","#####","   # ","   # "],
  "5": ["#####","#    ","#### ","    #","    #","#   #"," ### "],
  "6": [" ### ","#   #","#    ","#### ","#   #","#   #"," ### "],
  "7": ["#####","    #","   # ","  #  "," #   "," #   "," #   "],
  "8": [" ### ","#   #","#   #"," ### ","#   #","#   #"," ### "],
  "9": [" ### ","#   #","#   #"," ####","    #","#   #"," ### "],
  "A": [" ### ","#   #","#   #","#####","#   #","#   #","#   #"],
  "B": ["#### ","#   #","#   #","#### ","#   #","#   #","#### "],
  "C": [" ### ","#   #","#    ","#    ","#    ","#   #"," ### "],
  "D": ["#### ","#   #","#   #","#   #","#   #","#   #","#### "],
  "E": ["#####","#    ","#    ","#### ","#    ","#    ","#####"],
  "F": ["#####","#    ","#    ","#### ","#    ","#    ","#    "],
  "G": [" ### ","#   #","#    ","# ###","#   #","#   #"," ### "],
  "H": ["#   #","#   #","#   #","#####","#   #","#   #","#   #"],
  "I": [" ### ","  #  ","  #  ","  #  ","  #  ","  #  "," ### "],
  "J": ["  ###","   # ","   # ","   # ","#  # ","#  # "," ##  "],
  "K": ["#   #","#  # ","# #  ","##   ","# #  ","#  # ","#   #"],
  "L": ["#    ","#    ","#    ","#    ","#    ","#    ","#####"],
  "M": ["#   #","## ##","# # #","# # #","#   #","#   #","#   #"],
  "N": ["#   #","##  #","# # #","#  ##","#   #","#   #","#   #"],
  "O": [" ### ","#   #","#   #","#   #","#   #","#   #"," ### "],
  "P": ["#### ","#   #","#   #","#### ","#    ","#    ","#    "],
  "Q": [" ### ","#   #","#   #","#   #","# # #","#  # "," ## #"],
  "R": ["#### ","#   #","#   #","#### ","# #  ","#  # ","#   #"],
  "S": [" ####","#    ","#    "," ### ","    #","    #","#### "],
  "T": ["#####","  #  ","  #  ","  #  ","  #  ","  #  ","  #  "],
  "U": ["#   #","#   #","#   #","#   #","#   #","#   #"," ### "],
  "V": ["#   #","#   #","#   #","#   #","#   #"," # # ","  #  "],
  "W": ["#   #","#   #","#   #","# # #","# # #","## ##","#   #"],
  "X": ["#   #","#   #"," # # ","  #  "," # # ","#   #","#   #"],
  "Y": ["#   #","#   #"," # # ","  #  ","  #  ","  #  ","  #  "],
  "Z": ["#####","    #","   # ","  #  "," #   ","#    ","#####"],
};
const GW = 5, GH = 7, GAP = 1;
const VFD_TEXT = "#8dffe0", VFD_GLOW = "#3fe0b8";

function normalize(t){
  return (t || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toUpperCase();
}

/* Desenha uma matriz física completa e acende nela os pontos do texto. */
function drawVfd(canvas, rawText, maxDot){
  if(!canvas) return;
  const text = normalize(rawText);
  const dpr = window.devicePixelRatio || 1;
  const cssW = canvas.clientWidth, cssH = canvas.clientHeight;
  if(cssW === 0 || cssH === 0) return;
  canvas.width = Math.round(cssW*dpr); canvas.height = Math.round(cssH*dpr);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr,0,0,dpr,0,0);
  const w = cssW, h = cssH;

  const bg = ctx.createLinearGradient(0,0,0,h);
  bg.addColorStop(0,"#0c1c17"); bg.addColorStop(1,"#020d09");
  ctx.fillStyle = bg; ctx.fillRect(0,0,w,h);

  const n = Math.max(1, text.length), pad = 8;
  const totalCols = n*GW + (n-1)*GAP;
  const availW = Math.max(1, w-2*pad), availH = Math.max(1, h-2*pad);
  let dot = Math.min(availW/totalCols, availH/GH, maxDot);
  dot = Math.max(dot, 1);
  /*
   * O passo dos pontos ainda é calculado para o texto sempre caber, mas a
   * matriz apagada ocupa o visor inteiro. Isso faz o canvas parecer um módulo
   * VFD real mesmo quando exibe somente um algarismo.
   */
  const panelCols = Math.max(totalCols, Math.floor(availW/dot));
  const panelRows = Math.max(GH, Math.floor(availH/dot));
  const panelW = panelCols*dot, panelH = panelRows*dot;
  const panelX = (w-panelW)/2, panelY = (h-panelH)/2;
  const textCol = Math.floor((panelCols-totalCols)/2);
  const textRow = Math.floor((panelRows-GH)/2);
  const r = dot*0.42;

  /* Fósforo apagado: presente em toda a placa, discreto mas legível. */
  ctx.fillStyle = "#3d8c76";
  for(let row=0; row<panelRows; row++){
    for(let col=0; col<panelCols; col++){
      const dx = panelX + col*dot + dot/2;
      const dy = panelY + row*dot + dot/2;
      ctx.globalAlpha = 0.17;
      ctx.beginPath(); ctx.arc(dx,dy,r*0.72,0,7); ctx.fill();
      ctx.globalAlpha = 0.09;
      ctx.fillStyle = "#b5ffe9";
      ctx.beginPath(); ctx.arc(dx-r*0.18,dy-r*0.18,r*0.23,0,7); ctx.fill();
      ctx.fillStyle = "#3d8c76";
    }
  }
  ctx.globalAlpha = 1;

  for(let ci=0; ci<text.length; ci++){
    const glyph = FONT[text[ci]] || FONT[" "];
    const cx = panelX + (textCol + ci*(GW+GAP))*dot;
    for(let row=0; row<GH; row++){
      for(let col=0; col<GW; col++){
        const dx = cx + col*dot + dot/2;
        const dy = panelY + (textRow+row)*dot + dot/2;
        if(glyph[row][col] === "#"){
          ctx.fillStyle = VFD_GLOW; ctx.globalAlpha = 110/255;
          ctx.beginPath(); ctx.arc(dx,dy,r*1.8,0,7); ctx.fill();
          ctx.globalAlpha = 1; ctx.fillStyle = VFD_TEXT;
          ctx.beginPath(); ctx.arc(dx,dy,r,0,7); ctx.fill();
        }
      }
    }
  }
  ctx.strokeStyle = "rgba(0,0,0,0.22)"; ctx.lineWidth = 1;
  for(let y=0.5; y<h; y+=3){ ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(w,y); ctx.stroke(); }
  const refl = ctx.createLinearGradient(0,0,0,h*0.55);
  refl.addColorStop(0,"rgba(255,255,255,0.094)"); refl.addColorStop(1,"rgba(255,255,255,0)");
  ctx.fillStyle = refl; ctx.fillRect(0,0,w,h*0.55);
}

/* ======================================================================
   Ponte com o Python (pywebview.api). Chamadas seguras mesmo antes de
   o pywebview estar pronto (no-op).
   ====================================================================== */
function api(){ return (window.pywebview && window.pywebview.api) || null; }
function call(method){
  const a = api();
  if(a && typeof a[method] === "function"){
    const args = Array.prototype.slice.call(arguments, 1);
    a[method].apply(a, args);
  }
}

/* ======================================================================
   MS: interface chamada pelo Python via window.evaluate_js('MS.…').
   ====================================================================== */
const MS = {
  _state: { current: "", vol: "0", rev: "0", oct: "0", banks: [] },

  init(data){
    this._state.banks = data.banks || [];
    const columns = data.columns || 4;
    const tabs = document.getElementById("bank-tabs");
    const stack = document.getElementById("grid-stack");
    tabs.innerHTML = ""; stack.innerHTML = "";

    this._state.banks.forEach((bank, bankIndex) => {
      const tab = document.createElement("button");
      tab.className = "btn dark tab";
      tab.textContent = bank.label;
      tab.dataset.bank = bank.id;
      tab.dataset.number = String(bankIndex + 1).padStart(2, "0");
      tab.onclick = () => call("select_bank", bank.id);
      tabs.appendChild(tab);

      const grid = document.createElement("div");
      grid.className = "grid";
      grid.dataset.bank = bank.id;
      grid.style.gridTemplateColumns = "repeat(" + columns + ", 1fr)";
      bank.instruments.forEach((inst, instIndex) => {
        const b = document.createElement("button");
        b.className = "btn dark inst";
        b.dataset.inst = inst.id;
        b.dataset.number = String(instIndex + 1).padStart(2, "0");
        // 'icon' no YAML é um NOME de ícone (ex.: "piano"), não um glifo —
        // não é texto para exibir. O botão mostra só o label (como o UI antigo).
        b.textContent = inst.label;
        b.onclick = () => call("select_instrument", inst.id);
        grid.appendChild(b);
      });
      stack.appendChild(grid);
    });
    this.redraw();
  },

  setCurrentInstrument(id, displayText){
    this._state.current = displayText;
    document.querySelectorAll(".inst").forEach(b =>
      b.classList.toggle("selected", b.dataset.inst === id));
    drawVfd(document.getElementById("vfd"), displayText, 9);
  },

  setCurrentBank(id){
    document.querySelectorAll(".tab").forEach(t =>
      t.classList.toggle("selected", t.dataset.bank === id));
    document.querySelectorAll(".grid").forEach(g =>
      g.classList.toggle("active", g.dataset.bank === id));
  },

  setControl(name, text){
    if(name === "volume") this._state.vol = text;
    else if(name === "reverb") this._state.rev = text;
    else if(name === "octave") this._state.oct = text;
    drawVfd(document.getElementById("vfd-" + name), text, 6);
  },

  setStatus(kind, state, message){
    const led = document.getElementById("led-" + kind);
    if(!led) return;
    led.className = "led " + (state || "");
    led.title = message || "";
  },

  showPage(name){
    ["main","settings","error"].forEach(p =>
      document.getElementById("page-" + p).classList.toggle("hidden", p !== name));
    if(name === "main") this.redraw();
  },

  showError(message, retryable){
    document.getElementById("error-message").textContent = message || "";
    document.getElementById("btn-retry").classList.toggle("hidden", !retryable);
    this.showPage("error");
  },

  setSetting(name, value){
    const el = document.getElementById("set-" + name);
    if(el) el.textContent = value;
  },

  setMidiDevices(names, current){
    const sel = document.getElementById("set-midi");
    sel.innerHTML = "";
    if(!names || names.length === 0){
      const o = document.createElement("option");
      o.textContent = "Nenhum teclado encontrado"; o.value = "";
      sel.appendChild(o); sel.disabled = true;
      return;
    }
    sel.disabled = false;
    names.forEach(n => {
      const o = document.createElement("option");
      o.textContent = n; o.value = n;
      if(n === current) o.selected = true;
      sel.appendChild(o);
    });
  },

  /* Redesenha todos os visores (após resize / troca de página). */
  redraw(){
    drawVfd(document.getElementById("vfd"), this._state.current || "MINI SYNTH", 9);
    drawVfd(document.getElementById("vfd-volume"), this._state.vol, 6);
    drawVfd(document.getElementById("vfd-reverb"), this._state.rev, 6);
    drawVfd(document.getElementById("vfd-octave"), this._state.oct, 6);
  },
};
window.MS = MS;

/* ======================================================================
   Ligações de eventos estáticos (não dependem da config).
   ====================================================================== */
function wireStatic(){
  document.getElementById("btn-config").onclick = () => call("open_config");
  document.getElementById("btn-back").onclick    = () => call("back");
  document.getElementById("btn-retry").onclick   = () => call("retry");
  document.getElementById("btn-choose-sf").onclick = () => call("choose_soundfont");
  document.getElementById("btn-rescan").onclick  = () => call("rescan");
  document.getElementById("btn-test").onclick    = () => call("test_sound");
  document.getElementById("btn-panic").onclick   = () => call("panic");
  document.getElementById("set-midi").onchange   = (e) => call("select_midi", e.target.value);

  document.querySelectorAll(".pm").forEach(btn => {
    btn.onclick = () => call(btn.dataset.act, parseInt(btn.dataset.dir, 10));
  });
}

window.addEventListener("resize", () => MS.redraw());
wireStatic();
MS.redraw();  // primeiro paint (mostra "MINI SYNTH" até o Python enviar o estado)
