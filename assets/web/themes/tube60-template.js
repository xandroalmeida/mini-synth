"use strict";

window.MS_THEME_TEMPLATES = window.MS_THEME_TEMPLATES || {};
window.MS_THEME_TEMPLATES.tube60 = function(){
  return `
  <section id="page-main" class="tube-page">
    <div class="tube-cabinet">
      <header class="tube-masthead">
        <div class="tube-crest"><span class="crest-monogram">M</span><span><strong>Mini Synth</strong><small>CONSOLE VALVULADO · 1964</small></span></div>
        <div class="tube-status">
          <div><span class="jewel led" id="led-midi"></span><small>MIDI</small></div>
          <div><span class="jewel led" id="led-audio"></span><small>ÁUDIO</small></div>
        </div>
        <button class="ivory-key cfg" id="btn-config">AJUSTES</button>
      </header>
      <div class="tube-stage">
        <aside class="speaker speaker-left"><div class="speaker-cone"><i></i></div><div class="speaker-badge">HIGH FIDELITY</div></aside>
        <main class="tube-console">
          <div class="tuning-window">
            <div class="mechanical-scale" aria-hidden="true"><span>I</span><span>II</span><span>III</span><span>IV</span><span>V</span><span>VI</span><span>VII</span><span>VIII</span></div>
            <span class="scale-pointer" aria-hidden="true"></span>
            <div class="drum-frame">
              <div id="instrument-indicator" class="voice-drum" data-indicator="mechanical" role="status" aria-live="polite"><span class="drum-label current">MINI SYNTH</span></div>
            </div>
            <div class="dial-caption"><span>SELETOR MECÂNICO DE VOZ</span><span>REGISTRO</span></div>
          </div>
          <div class="tube-bank-panel"><span class="engraved-label">FAIXA</span><div class="bank-tabs" id="bank-tabs"></div></div>
          <div class="tube-voice-panel">
            <div class="voice-heading"><span>REGISTROS</span><small>PRESSIONE UMA TECLA</small></div>
            <div class="grid-stack" id="grid-stack"></div>
          </div>
        </main>
        <aside class="valve-bay">
          <div class="valve-window"><span class="valve v1"></span><span class="valve v2"></span><span class="valve v3"></span></div>
          <strong>3 VALVES</strong><small>WARM TONE AMPLIFIER</small>
          <div class="vent-slots"><i></i><i></i><i></i><i></i><i></i></div>
        </aside>
      </div>
      <div class="tube-control-deck">
        ${tubeControl("volume","VOLUME","INTENSIDADE")}
        ${tubeControl("reverb","AMBIENTE","REVERBERAÇÃO")}
        ${tubeOctave()}
        <div class="tube-stop-control"><span class="engraved-label">SEGURANÇA</span><button class="stop-key" id="btn-panic">CORTAR SOM</button></div>
      </div>
      <footer class="tube-footer"><span>MODÈLE 64</span><span>VACUUM TUBE STEREOPHONIC</span><span>FABRIQUÉ POUR PETITS MUSICIENS</span></footer>
    </div>
  </section>
  <section id="page-settings" class="tube-page hidden">
    <div class="tube-cabinet service-cabinet">
      <header class="tube-masthead"><div class="tube-crest"><span class="crest-monogram">M</span><span><strong>Painel de Serviço</strong><small>MINI SYNTH · MODÈLE 64</small></span></div><button class="ivory-key" id="btn-back">◀ VOLTAR AO RÁDIO</button></header>
      <div class="service-cloth">
        <div class="service-plaque"><strong>AJUSTES DO APARELHO</strong><small>CALIBRAÇÃO E CONEXÕES</small></div>
        <div class="service-grid">
          ${serviceRow("01","SOUNDFONT","BANCO DE TIMBRES",'<div class="settings-value" id="set-soundfont">—</div>','<button class="ivory-key act" id="btn-choose-sf">ESCOLHER ARQUIVO</button>')}
          ${serviceRow("02","ENTRADA MIDI","TECLADO CONTROLADOR",'<select class="settings-select" id="set-midi"></select>','<button class="ivory-key act" id="btn-rescan">PROCURAR TECLADO</button>')}
          ${serviceRow("03","SAÍDA DE ÁUDIO","AMPLIFICADOR",'<div class="settings-value" id="set-driver">—</div>','<button class="ivory-key act" id="btn-test">▶ TESTAR VÁLVULAS</button>')}
          ${serviceRow("04","MÓVEL / TEMA","APARÊNCIA COMPLETA",'<select class="settings-select" id="set-theme"></select>','<div class="tube-theme-sample"><span class="mini-valve"></span><strong>ACABAMENTO</strong></div>')}
        </div>
      </div>
      <footer class="tube-footer"><span>CAUTION · HIGH TEMPERATURE</span><span>QUALIDADE HI-FI</span><span>SERVICE PANEL</span></footer>
    </div>
  </section>
  <section id="page-error" class="tube-page hidden"><div class="tube-cabinet error-cabinet"><div class="fault-window"><span class="fault-jewel">!</span><strong>FALHA NO APARELHO</strong><div class="error-message" id="error-message"></div><button class="ivory-key" id="btn-retry">TENTAR NOVAMENTE</button><small>DESLIGUE O APARELHO SE O PROBLEMA CONTINUAR</small></div></div></section>
  `;
};

function tubeControl(action, label, sublabel){
  return `<div class="tube-knob-control"><span class="engraved-label">${label}</span><small>${sublabel}</small><div class="knob-line"><button class="knob-step pm" data-act="${action}" data-dir="-1">−</button><div class="analog-meter" id="indicator-${action}" data-indicator="analog" data-min="0" data-max="100" role="meter"></div><button class="knob-step pm" data-act="${action}" data-dir="1">+</button></div></div>`;
}

function tubeOctave(){
  return `<div class="tube-knob-control octave-control"><span class="engraved-label">OITAVA</span><small>REGISTRO</small><div class="knob-line"><button class="knob-step pm" data-act="octave" data-dir="-1">−</button><div class="analog-meter" id="indicator-octave" data-indicator="analog" data-min="-2" data-max="2" role="meter"></div><button class="knob-step reset pm" data-act="octave" data-dir="0">●</button><button class="knob-step pm" data-act="octave" data-dir="1">+</button></div></div>`;
}

function serviceRow(number, title, subtitle, field, action){
  return `<div class="service-row"><div class="service-label"><b>${number}</b><span><strong>${title}</strong><small>${subtitle}</small></span></div>${field}${action}</div>`;
}
