"use strict";

window.MS_THEME_TEMPLATES = window.MS_THEME_TEMPLATES || {};
window.MS_THEME_TEMPLATES.ms90 = function(){
  return `
  <section id="page-main" class="page ms90-page">
    <div class="header">
      <span class="screw"></span>
      <div class="brand-block">
        <span class="brand-mark">M</span>
        <div><span class="title">MINI SYNTH</span><span class="model">DIGITAL SOUND MODULE · MS-90</span></div>
      </div>
      <span class="spacer"></span>
      <div class="status-cluster">
        <div class="status"><span class="led" id="led-midi"></span><span class="cap">MIDI</span></div>
        <div class="status"><span class="led" id="led-audio"></span><span class="cap">ÁUDIO</span></div>
      </div>
      <button class="btn metal cfg" id="btn-config"><span class="button-icon">⚙</span> CONFIG</button>
      <span class="screw"></span>
    </div>
    <div class="display-card">
      <span class="screw screw-sm display-screw"></span>
      <div class="display-bezel">
        <div class="display-label"><span>PROGRAM</span><span>INSTRUMENTO ATUAL</span></div>
        <canvas id="instrument-indicator" class="vfd"></canvas>
      </div>
      <div class="display-badge"><strong>16 BIT</strong><span>DIGITAL SYNTHESIS</span></div>
      <span class="screw screw-sm display-screw"></span>
    </div>
    <div class="bank-strip"><span class="strip-label">SOUND BANK</span><div class="bank-tabs" id="bank-tabs"></div></div>
    <div class="controls-card">
      <div class="panel-legend"><span>VOICE SELECT</span><span>TOQUE PARA ESCOLHER</span></div>
      <div class="grid-stack" id="grid-stack"></div>
    </div>
    <div class="control-panel">
      <div class="control card">
        <div class="ctl-label"><span>01</span> VOLUME <small>MASTER</small></div>
        <div class="ctl-row"><button class="btn dark pm" data-act="volume" data-dir="-1">−</button><canvas class="mini-vfd" id="indicator-volume"></canvas><button class="btn dark pm" data-act="volume" data-dir="1">+</button></div>
      </div>
      <div class="control card">
        <div class="ctl-label"><span>02</span> REVERB <small>ROOM</small></div>
        <div class="ctl-row"><button class="btn dark pm" data-act="reverb" data-dir="-1">−</button><canvas class="mini-vfd" id="indicator-reverb"></canvas><button class="btn dark pm" data-act="reverb" data-dir="1">+</button></div>
      </div>
      <div class="control card">
        <div class="ctl-label"><span>03</span> OITAVA <small>SHIFT</small></div>
        <div class="ctl-row"><button class="btn dark pm" data-act="octave" data-dir="-1">−</button><canvas class="mini-vfd" id="indicator-octave"></canvas><button class="btn dark pm reset" data-act="octave" data-dir="0" title="Oitava normal">↺</button><button class="btn dark pm" data-act="octave" data-dir="1">+</button></div>
      </div>
      <div class="panic-module card">
        <div class="ctl-label"><span>!</span> EMERGÊNCIA <small>ALL NOTES OFF</small></div>
        <button class="btn panic" id="btn-panic">PARAR SOM</button>
      </div>
    </div>
    <div class="rack-footer"><span>PHONES</span><span>GENERAL MIDI</span><span>MADE FOR LITTLE MUSICIANS</span></div>
  </section>
  <section id="page-settings" class="page hidden">
    <div class="settings-header"><span class="screw"></span><div><span class="settings-title">SYSTEM SETUP</span><span class="settings-subtitle">MINI SYNTH MS-90</span></div><span class="spacer"></span><button class="btn metal" id="btn-back">◄ VOLTAR</button><span class="screw"></span></div>
    <div class="settings-display"><span>CONFIGURAÇÃO DO SISTEMA</span><small>AJUSTE AS CONEXÕES DO APARELHO</small></div>
    ${settingsPanel()}
    <div class="settings-footer"><span class="screw screw-sm"></span><span>CAUTION · DO NOT DISCONNECT WHILE PLAYING</span><span class="screw screw-sm"></span></div>
  </section>
  ${errorPanel("SYSTEM PROTECTION · MS-90")}
  `;
};

function settingsPanel(){
  return `
  <div class="card settings-card">
    <div class="settings-row"><div class="settings-field"><span>01</span><strong>SOUNDFONT</strong><small>BANCO DE TIMBRES</small></div><div class="settings-value" id="set-soundfont">—</div><button class="btn metal act" id="btn-choose-sf">ESCOLHER ARQUIVO</button></div>
    <div class="settings-row"><div class="settings-field"><span>02</span><strong>ENTRADA MIDI</strong><small>TECLADO CONTROLADOR</small></div><select class="settings-select" id="set-midi"></select><button class="btn metal act" id="btn-rescan">DETECTAR NOVAMENTE</button></div>
    <div class="settings-row"><div class="settings-field"><span>03</span><strong>SAÍDA DE ÁUDIO</strong><small>DRIVER ATUAL</small></div><div class="settings-value" id="set-driver">—</div><button class="btn metal act test" id="btn-test">▶ TESTAR SOM</button></div>
    <div class="settings-row"><div class="settings-field"><span>04</span><strong>TEMA VISUAL</strong><small>APARÊNCIA DO APARELHO</small></div><select class="settings-select" id="set-theme"></select><div class="theme-preview"><span class="theme-preview-lamp"></span><strong>APARÊNCIA</strong><small>APLICAÇÃO IMEDIATA</small></div></div>
  </div>`;
}

function errorPanel(code){
  return `<section id="page-error" class="page hidden"><div class="error-box"><span class="screw"></span><div class="warning-lamp">!</div><div class="error-title">ATENÇÃO</div><div class="error-message" id="error-message"></div><button class="btn metal error-retry" id="btn-retry">TENTAR NOVAMENTE</button><span class="error-code">${code}</span><span class="screw"></span></div></section>`;
}
