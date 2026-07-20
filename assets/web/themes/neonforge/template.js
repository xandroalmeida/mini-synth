"use strict";

window.MS_THEME_TEMPLATES = window.MS_THEME_TEMPLATES || {};
window.MS_THEME_TEMPLATES.neonforge = function(){
  return `
  <section id="page-main" class="cyber-page">
    <div class="forge-shell">
      <header class="forge-header">
        <div class="maker-sigil"><i></i><span>NF</span></div>
        <div class="forge-title"><strong>NEON FORGE</strong><small>KID/01 · STREET SYNTH UNIT</small></div>
        <div class="live-bus"><span class="pulse-line"></span><small>LIVE SIGNAL BUS</small></div>
        <div class="probe"><span class="led" id="led-midi"></span><b>MIDI</b><small>INPUT</small></div>
        <div class="probe"><span class="led" id="led-audio"></span><b>AUDIO</b><small>ENGINE</small></div>
        <button class="hex-key cfg" id="btn-config"><span>⌬</span> MAINT</button>
      </header>

      <div class="forge-workbench">
        <aside class="patch-spine" aria-hidden="true">
          <span class="rail-code">PATCH//A7</span>
          <div class="cable cyan"><i></i><i></i></div>
          <div class="socket-bank"><i></i><i></i><i></i><i></i></div>
          <div class="cable magenta"><i></i><i></i></div>
          <div class="coolant-meter"><span></span></div>
          <small>OPTICAL<br>ROUTING</small>
        </aside>

        <main class="voice-core">
          <section class="holo-console">
            <div class="screen-rivet r1"></div><div class="screen-rivet r2"></div>
            <div class="screen-meta"><span>VOICE CORE / ACTIVE PATCH</span><b>SYNC 48K</b></div>
            <div class="holo-glass"><canvas id="instrument-indicator" class="forge-vfd"></canvas></div>
            <div class="signal-teeth" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
          </section>

          <section class="bank-bus">
            <span class="bus-label"><b>BANK BUS</b><small>ROUTE</small></span>
            <div class="bank-tabs" id="bank-tabs"></div>
          </section>

          <section class="cartridge-bay">
            <div class="bay-heading"><span>SONIC CARTRIDGES</span><small>PRESS TO ARM VOICE</small><i>● HOT SWAP</i></div>
            <div class="grid-stack" id="grid-stack"></div>
          </section>
        </main>

        <aside class="power-spine">
          <div class="danger-tag">HV<br><b>09</b></div>
          <div class="flux-window"><span class="flux-core"></span><i></i><i></i><i></i></div>
          <div class="power-readout"><small>CORE TEMP</small><b>38°</b><span>NOMINAL</span></div>
          <div class="microvents" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div>
          <small class="spine-code">PWR CELL<br>MK.IV</small>
        </aside>
      </div>

      <section class="command-deck">
        ${forgeControl("volume", "GAIN", "MASTER", "01")}
        ${forgeControl("reverb", "SPACE", "REVERB", "02")}
        ${forgeOctave()}
        <div class="kill-module">
          <div class="guard-rails"><i></i><i></i></div>
          <span><b>KILL AUDIO</b><small>EMERGENCY DUMP</small></span>
          <button class="kill-switch" id="btn-panic"><i></i> CUT</button>
        </div>
      </section>
      <footer class="forge-footer"><span>NEON DISTRICT LABS // UNIT 01</span><span class="footer-dashes">///</span><span>SAFE FOR SMALL OPERATORS</span></footer>
    </div>
  </section>

  <section id="page-settings" class="cyber-page hidden">
    <div class="forge-shell maintenance-shell">
      <header class="forge-header">
        <div class="maker-sigil"><i></i><span>NF</span></div>
        <div class="forge-title"><strong>MAINTENANCE HATCH</strong><small>KID/01 · SYSTEM ACCESS</small></div>
        <div class="access-state"><i></i> LOCAL ACCESS GRANTED</div>
        <button class="hex-key" id="btn-back">◁ RETURN</button>
      </header>
      <div class="maintenance-bay">
        <aside class="service-rail"><span>SYS</span><b>04</b><i></i><i></i><i></i><small>AUTHORIZED<br>TECH ONLY</small></aside>
        <div class="service-board">
          ${forgeSetting("01", "SOUNDFONT", "VOICE MEMORY", '<div class="settings-value" id="set-soundfont">—</div>', '<button class="hex-key action" id="btn-choose-sf">MOUNT FILE</button>')}
          ${forgeSetting("02", "MIDI INPUT", "CONTROL LINK", '<select class="settings-select" id="set-midi"></select>', '<button class="hex-key action" id="btn-rescan">SCAN PORTS</button>')}
          ${forgeSetting("03", "AUDIO OUTPUT", "ENGINE DRIVER", '<div class="settings-value" id="set-driver">—</div>', '<button class="hex-key action test" id="btn-test">▶ PULSE TEST</button>')}
          ${forgeSetting("04", "CHASSIS SKIN", "VISUAL MODULE", '<select class="settings-select" id="set-theme"></select>', '<div class="skin-chip"><i></i><span><b>LIVE SWAP</b><small>NO REBOOT</small></span></div>')}
        </div>
      </div>
      <footer class="forge-footer"><span>HATCH OPEN // ELECTROSTATIC PRECAUTIONS</span><span>REV. 7C</span></footer>
    </div>
  </section>

  <section id="page-error" class="cyber-page hidden">
    <div class="forge-shell fault-shell">
      <div class="fault-shutter">
        <div class="fault-glyph"><i></i><span>!</span></div>
        <small>SYSTEM INTERLOCK</small><strong>SIGNAL PATH BROKEN</strong>
        <div class="error-message" id="error-message"></div>
        <button class="hex-key fault-retry" id="btn-retry">RE-LINK SYSTEM</button>
        <span class="fault-code">ERR // KID-01 // SAFE MODE</span>
      </div>
    </div>
  </section>`;
};

function forgeControl(action, label, sublabel, number){
  return `<div class="arc-module"><span class="module-no">${number}</span><div class="arc-title"><b>${label}</b><small>${sublabel}</small></div><div class="arc-control"><button class="step-pad pm" data-act="${action}" data-dir="-1">−</button><div class="readout-shell"><canvas id="indicator-${action}" class="forge-mini"></canvas></div><button class="step-pad pm" data-act="${action}" data-dir="1">+</button></div></div>`;
}

function forgeOctave(){
  return `<div class="arc-module octave-module"><span class="module-no">03</span><div class="arc-title"><b>OCTAVE</b><small>TRANSPOSE</small></div><div class="arc-control"><button class="step-pad pm" data-act="octave" data-dir="-1">−</button><div class="readout-shell"><canvas id="indicator-octave" class="forge-mini"></canvas></div><button class="step-pad reset pm" data-act="octave" data-dir="0">◆</button><button class="step-pad pm" data-act="octave" data-dir="1">+</button></div></div>`;
}

function forgeSetting(number, title, subtitle, field, action){
  return `<section class="service-module"><div class="service-id"><span>${number}</span><i></i></div><div class="service-copy"><b>${title}</b><small>${subtitle}</small></div>${field}${action}</section>`;
}
