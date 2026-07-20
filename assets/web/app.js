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
const THEME_PATHS = {
  ms90: "themes/ms90/style.css",
  tube60: "themes/tube60/style.css",
};

function cssVar(name, fallback){
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
}

function normalize(t){
  return (t || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toUpperCase();
}

function rollMechanicalIndicator(indicator, text, direction, animate){
  const existing = indicator.querySelector(".drum-label");
  const previous = indicator.dataset.value || (existing ? existing.textContent : "");
  indicator.dataset.value = text;
  indicator.setAttribute("aria-label", text);
  if(previous === text && existing) return;

  if(indicator._rollTimer) clearTimeout(indicator._rollTimer);
  const next = document.createElement("span");
  next.className = "drum-label next";
  next.textContent = text;
  if(!animate || !previous || window.matchMedia("(prefers-reduced-motion: reduce)").matches){
    next.className = "drum-label current";
    indicator.replaceChildren(next);
    return;
  }

  const old = document.createElement("span");
  old.className = "drum-label current";
  old.textContent = previous;
  indicator.classList.remove("rolling-forward", "rolling-backward");
  indicator.replaceChildren(old, next);
  void indicator.offsetWidth;
  indicator.classList.add(direction < 0 ? "rolling-backward" : "rolling-forward");
  indicator._rollTimer = setTimeout(() => {
    next.className = "drum-label current";
    indicator.replaceChildren(next);
    indicator.classList.remove("rolling-forward", "rolling-backward");
    indicator._rollTimer = null;
  }, 360);
}

function romanNumeral(index){
  return ["I","II","III","IV","V","VI","VII","VIII","IX","X"][index] || String(index + 1);
}

function updateMechanicalSelector(index, count){
  const scale = document.querySelector(".mechanical-scale");
  const pointer = document.querySelector(".scale-pointer");
  const frame = document.querySelector(".tuning-window");
  if(!scale || !pointer || !frame || index < 0 || count < 1) return;
  if(scale.children.length !== count){
    scale.replaceChildren(...Array.from({length:count}, (_, i) => {
      const mark = document.createElement("span");
      mark.textContent = romanNumeral(i);
      return mark;
    }));
  }
  const mark = scale.children[Math.min(index, count - 1)];
  const markBox = mark.getBoundingClientRect();
  const frameBox = frame.getBoundingClientRect();
  pointer.style.left = (markBox.left + markBox.width / 2 - frameBox.left) + "px";
  pointer.setAttribute("aria-label", "Posição " + (index + 1) + " de " + count);
}

/* Renderiza VFD digital, tambor mecânico ou medidor analógico conforme o tema. */
function renderIndicator(indicator, rawText, maxDot, options){
  if(!indicator) return;
  const text = normalize(rawText);
  const opts = options || {};
  if(indicator.dataset.indicator === "mechanical"){
    rollMechanicalIndicator(indicator, text, opts.direction || 1, opts.animate !== false);
    return;
  }
  if(indicator.dataset.indicator === "analog"){
    const min = Number(indicator.dataset.min);
    const max = Number(indicator.dataset.max);
    const parsed = Number(rawText);
    const value = Number.isFinite(parsed) ? parsed : min;
    const clamped = Math.min(max, Math.max(min, value));
    const ratio = max === min ? 0 : (clamped - min) / (max - min);
    indicator.style.setProperty("--needle-angle", (-58 + ratio * 116) + "deg");
    indicator.setAttribute("aria-valuemin", String(min));
    indicator.setAttribute("aria-valuemax", String(max));
    indicator.setAttribute("aria-valuenow", String(clamped));
    return;
  }
  const canvas = indicator;
  const dpr = window.devicePixelRatio || 1;
  const cssW = canvas.clientWidth, cssH = canvas.clientHeight;
  if(cssW === 0 || cssH === 0) return;
  canvas.width = Math.round(cssW*dpr); canvas.height = Math.round(cssH*dpr);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr,0,0,dpr,0,0);
  const w = cssW, h = cssH;

  const displayText = cssVar("--display-text", "#8dffe0");
  const displayGlow = cssVar("--display-glow", "#3fe0b8");
  const displayOff = cssVar("--display-off", "#3d8c76");
  const displayOffHighlight = cssVar("--display-off-highlight", "#b5ffe9");
  const bg = ctx.createLinearGradient(0,0,0,h);
  bg.addColorStop(0,cssVar("--display-bg-top", "#0c1c17"));
  bg.addColorStop(1,cssVar("--display-bg-bottom", "#020d09"));
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
  ctx.fillStyle = displayOff;
  for(let row=0; row<panelRows; row++){
    for(let col=0; col<panelCols; col++){
      const dx = panelX + col*dot + dot/2;
      const dy = panelY + row*dot + dot/2;
      ctx.globalAlpha = 0.17;
      ctx.beginPath(); ctx.arc(dx,dy,r*0.72,0,7); ctx.fill();
      ctx.globalAlpha = 0.09;
      ctx.fillStyle = displayOffHighlight;
      ctx.beginPath(); ctx.arc(dx-r*0.18,dy-r*0.18,r*0.23,0,7); ctx.fill();
      ctx.fillStyle = displayOff;
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
          ctx.fillStyle = displayGlow; ctx.globalAlpha = 110/255;
          ctx.beginPath(); ctx.arc(dx,dy,r*1.8,0,7); ctx.fill();
          ctx.globalAlpha = 1; ctx.fillStyle = displayText;
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
  _state: {
    current: "", currentId: "", currentBank: "",
    vol: "0", rev: "0", oct: "0",
    banks: [], columns: 4, themes: [], theme: "ms90",
    statuses: { midi: ["", ""], audio: ["", ""] },
    settings: { soundfont: "—", driver: "—" },
    midi: { names: [], current: "" },
    page: "main", error: { message: "", retryable: true },
  },

  init(data){
    this._state.banks = data.banks || [];
    this._state.columns = data.columns || 4;
    this._state.themes = data.themes || [];
    this.setTheme(data.theme || "ms90", true);
  },

  _buildBanks(){
    const tabs = document.getElementById("bank-tabs");
    const stack = document.getElementById("grid-stack");
    if(!tabs || !stack) return;
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
      grid.style.gridTemplateColumns = "repeat(" + this._state.columns + ", 1fr)";
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
  },

  _renderTheme(themeId){
    const factory = window.MS_THEME_TEMPLATES && window.MS_THEME_TEMPLATES[themeId];
    if(typeof factory !== "function") return;
    document.getElementById("app-shell").innerHTML = factory();
    wireStatic();
    this._buildBanks();
    this._restoreState();
  },

  _restoreState(){
    this._populateThemes();
    this._populateMidi();
    Object.keys(this._state.settings).forEach(name => {
      const el = document.getElementById("set-" + name);
      if(el) el.textContent = this._state.settings[name];
    });
    if(this._state.currentBank) this.setCurrentBank(this._state.currentBank);
    if(this._state.currentId) this.setCurrentInstrument(this._state.currentId, this._state.current);
    this.setControl("volume", this._state.vol);
    this.setControl("reverb", this._state.rev);
    this.setControl("octave", this._state.oct);
    this.setStatus("midi", ...this._state.statuses.midi);
    this.setStatus("audio", ...this._state.statuses.audio);
    const errorMessage = document.getElementById("error-message");
    const retry = document.getElementById("btn-retry");
    if(errorMessage) errorMessage.textContent = this._state.error.message;
    if(retry) retry.classList.toggle("hidden", !this._state.error.retryable);
    this.showPage(this._state.page);
    this.redraw();
  },

  setCurrentInstrument(id, displayText){
    const previousPosition = this._instrumentPosition(this._state.currentId);
    this._state.currentId = id;
    this._state.current = displayText;
    document.querySelectorAll(".inst").forEach(b =>
      b.classList.toggle("selected", b.dataset.inst === id));
    const position = this._instrumentPosition(id);
    const direction = previousPosition.index < 0 || position.index >= previousPosition.index ? 1 : -1;
    renderIndicator(document.getElementById("instrument-indicator"), displayText, 9, {direction});
    updateMechanicalSelector(position.index, position.count);
  },

  _instrumentPosition(id){
    for(const bank of this._state.banks){
      const index = bank.instruments.findIndex(instrument => instrument.id === id);
      if(index >= 0) return {index, count:bank.instruments.length};
    }
    return {index:-1, count:0};
  },

  setCurrentBank(id){
    this._state.currentBank = id;
    document.querySelectorAll(".tab").forEach(t =>
      t.classList.toggle("selected", t.dataset.bank === id));
    document.querySelectorAll(".grid").forEach(g =>
      g.classList.toggle("active", g.dataset.bank === id));
  },

  setControl(name, text){
    if(name === "volume") this._state.vol = text;
    else if(name === "reverb") this._state.rev = text;
    else if(name === "octave") this._state.oct = text;
    renderIndicator(document.getElementById("indicator-" + name), text, 6);
  },

  setStatus(kind, state, message){
    this._state.statuses[kind] = [state || "", message || ""];
    const led = document.getElementById("led-" + kind);
    if(!led) return;
    led.classList.remove("connected", "searching", "error");
    if(state) led.classList.add(state);
    led.title = message || "";
  },

  showPage(name){
    this._state.page = name;
    ["main","settings","error"].forEach(p =>
      document.getElementById("page-" + p).classList.toggle("hidden", p !== name));
    if(name === "main") this.redraw();
  },

  showError(message, retryable){
    this._state.error = { message: message || "", retryable: Boolean(retryable) };
    document.getElementById("error-message").textContent = message || "";
    document.getElementById("btn-retry").classList.toggle("hidden", !retryable);
    this.showPage("error");
  },

  setSetting(name, value){
    this._state.settings[name] = value;
    const el = document.getElementById("set-" + name);
    if(el) el.textContent = value;
  },

  setMidiDevices(names, current){
    this._state.midi = { names: names || [], current: current || "" };
    this._populateMidi();
  },

  _populateMidi(){
    const sel = document.getElementById("set-midi");
    if(!sel) return;
    const names = this._state.midi.names;
    const current = this._state.midi.current;
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

  setThemes(themes, current){
    this._state.themes = themes || [];
    this.setTheme(current);
  },

  _populateThemes(){
    const sel = document.getElementById("set-theme");
    if(!sel) return;
    sel.innerHTML = "";
    this._state.themes.forEach(theme => {
      const option = document.createElement("option");
      option.value = theme.id;
      option.textContent = theme.label;
      sel.appendChild(option);
    });
    sel.value = this._state.theme;
  },

  setTheme(id, force){
    const themeId = Object.prototype.hasOwnProperty.call(THEME_PATHS, id) ? id : "ms90";
    const changed = this._state.theme !== themeId;
    this._state.theme = themeId;
    document.documentElement.dataset.theme = themeId;
    const link = document.getElementById("theme-stylesheet");
    const nextHref = THEME_PATHS[themeId];
    if(link.getAttribute("href") !== nextHref){
      link.onload = () => this.redraw();
      link.setAttribute("href", nextHref);
    }
    if(changed || force || !document.getElementById("page-main")){
      this._renderTheme(themeId);
    } else {
      this._populateThemes();
      this.redraw();
    }
  },

  /* Redesenha todos os visores (após resize / troca de página). */
  redraw(){
    renderIndicator(document.getElementById("instrument-indicator"), this._state.current || "MINI SYNTH", 9, {animate:false});
    const position = this._instrumentPosition(this._state.currentId);
    updateMechanicalSelector(position.index, position.count);
    renderIndicator(document.getElementById("indicator-volume"), this._state.vol, 6);
    renderIndicator(document.getElementById("indicator-reverb"), this._state.rev, 6);
    renderIndicator(document.getElementById("indicator-octave"), this._state.oct, 6);
  },
};
window.MS = MS;

/* ======================================================================
   Ligações de eventos estáticos (não dependem da config).
   ====================================================================== */
function wireStatic(){
  const bind = (id, event, handler) => {
    const el = document.getElementById(id);
    if(el) el[event] = handler;
  };
  bind("btn-config", "onclick", () => call("open_config"));
  bind("btn-back", "onclick", () => call("back"));
  bind("btn-retry", "onclick", () => call("retry"));
  bind("btn-choose-sf", "onclick", () => call("choose_soundfont"));
  bind("btn-rescan", "onclick", () => call("rescan"));
  bind("btn-test", "onclick", () => call("test_sound"));
  bind("btn-panic", "onclick", () => call("panic"));
  bind("set-midi", "onchange", e => call("select_midi", e.target.value));
  bind("set-theme", "onchange", e => call("select_theme", e.target.value));

  document.querySelectorAll(".pm").forEach(btn => {
    btn.onclick = () => call(btn.dataset.act, parseInt(btn.dataset.dir, 10));
  });
}

window.addEventListener("resize", () => MS.redraw());
MS.setTheme("ms90", true);
