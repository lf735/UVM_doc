/**
 * UVM 1.2 Interactive Example Studio Controller
 * Powered by Universal Page Controller (js/page_common.js).
 *
 * Capabilities:
 * - Multi-File Code Studio (studioCodeContainer.scrollTo, studio-file-select, studio-tab-scroll-left) in js/page_common.js
 * - Zero-Dependency Native Client-Side ZIP Generator (crc32, createNativeZipBlob, initZipDownload) in this file
 * - Simulation Console & Log Filters (initSimulationConsole) in this file
 * - Interactive Visual Flow Stepper (initFlowStepper) in this file
 */
(function initExamplePage(global) {
  'use strict';

  if (!global.PageCommon) {
    console.warn('PageCommon must be loaded before example_page.js');
  }

  // =========================================================================
  // Native Client-Side Zero-Dependency ZIP Generator
  // =========================================================================

  function crc32(uint8) {
    let crc = ~0;
    for (let i = 0; i < uint8.length; i++) {
      crc ^= uint8[i];
      for (let j = 0; j < 8; j++) {
        crc = (crc >>> 1) ^ (crc & 1 ? 0xEDB88320 : 0);
      }
    }
    return ~crc >>> 0;
  }

  function createNativeZipBlob(files) {
    const encoder = new TextEncoder();
    const fileEntries = [];
    let offset = 0;
    const parts = [];

    for (const f of files) {
      const nameBytes = encoder.encode(f.name);
      const dataBytes = encoder.encode(f.content);
      const crc = crc32(dataBytes);

      // Local File Header (30 bytes + name length)
      const header = new Uint8Array(30);
      const view = new DataView(header.buffer);
      header.set([0x50, 0x4B, 0x03, 0x04], 0); // PK\x03\x04
      view.setUint16(4, 20, true);              // version 2.0
      view.setUint16(6, 0x0800, true);          // UTF-8 flag
      view.setUint16(8, 0, true);               // compression: 0 (Store)
      view.setUint16(10, 0, true);              // time
      view.setUint16(12, 0, true);              // date
      view.setUint32(14, crc, true);            // CRC-32
      view.setUint32(18, dataBytes.length, true); // compressed size
      view.setUint32(22, dataBytes.length, true); // uncompressed size
      view.setUint16(26, nameBytes.length, true); // filename length
      view.setUint16(28, 0, true);              // extra field length

      fileEntries.push({ offset, nameBytes, dataBytes, crc, length: dataBytes.length });
      parts.push(header, nameBytes, dataBytes);
      offset += header.length + nameBytes.length + dataBytes.length;
    }

    const cdOffset = offset;
    let cdSize = 0;

    // Central Directory Headers (46 bytes + name length)
    for (const entry of fileEntries) {
      const cd = new Uint8Array(46);
      const view = new DataView(cd.buffer);
      cd.set([0x50, 0x4B, 0x01, 0x02], 0);    // PK\x01\x02
      view.setUint16(4, 20, true);            // version made by
      view.setUint16(6, 20, true);            // version needed
      view.setUint16(8, 0x0800, true);        // UTF-8 flag
      view.setUint16(10, 0, true);            // compression: 0
      view.setUint16(12, 0, true);            // time
      view.setUint16(14, 0, true);            // date
      view.setUint32(16, entry.crc, true);    // CRC-32
      view.setUint32(20, entry.length, true); // comp size
      view.setUint32(24, entry.length, true); // uncomp size
      view.setUint16(28, entry.nameBytes.length, true); // filename len
      view.setUint16(30, 0, true);            // extra len
      view.setUint16(32, 0, true);            // comment len
      view.setUint16(34, 0, true);            // disk start
      view.setUint16(36, 0, true);            // int attr
      view.setUint32(38, 0, true);            // ext attr
      view.setUint32(42, entry.offset, true); // local header offset

      parts.push(cd, entry.nameBytes);
      cdSize += cd.length + entry.nameBytes.length;
    }

    // End of Central Directory (22 bytes)
    const eocd = new Uint8Array(22);
    const eocdView = new DataView(eocd.buffer);
    eocd.set([0x50, 0x4B, 0x05, 0x06], 0);    // PK\x05\x06
    eocdView.setUint16(4, 0, true);           // disk number
    eocdView.setUint16(6, 0, true);           // start disk
    eocdView.setUint16(8, files.length, true);  // entries on disk
    eocdView.setUint16(10, files.length, true); // total entries
    eocdView.setUint32(12, cdSize, true);     // size of central directory
    eocdView.setUint32(16, cdOffset, true);   // offset of central directory
    eocdView.setUint16(20, 0, true);          // comment length

    parts.push(eocd);
    return new Blob(parts, { type: 'application/zip' });
  }

  function initZipDownload() {
    const btnDownloadZip = document.getElementById('btn-download-zip');
    const zipPayloadEl = document.getElementById('zip-payload');
    if (!btnDownloadZip || !zipPayloadEl || btnDownloadZip.dataset.zipBound) return;
    btnDownloadZip.dataset.zipBound = '1';

    btnDownloadZip.addEventListener('click', function () {
      let filesList = [];
      try {
        filesList = JSON.parse(zipPayloadEl.getAttribute('data-zip') || '[]');
      } catch (e) {
        console.warn('Could not parse zip payload', e);
      }
      if (!filesList || filesList.length === 0) return;

      const zipBlob = createNativeZipBlob(filesList);
      const url = URL.createObjectURL(zipBlob);
      const a = document.createElement('a');
      const pageTitle = (document.title.split('|')[0] || 'uvm_archive').trim().toLowerCase().replace(/[^a-z0-9_]/g, '_');
      a.href = url;
      a.download = `${pageTitle}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  // =========================================================================
  // Simulation Console & Log Filters
  // =========================================================================

  function initSimulationConsole() {
    const simTabs = document.querySelectorAll('.sim-tab');
    const simCmdText = document.getElementById('sim-cmd-text');
    const btnCopyCmd = document.getElementById('btn-copy-cmd');
    const termFilters = document.querySelectorAll('.term-filter');
    const terminalBody = document.getElementById('terminal-body');

    if (!terminalBody && !simTabs.length) return;
    if (terminalBody && terminalBody.dataset.simBound) return;
    if (terminalBody) terminalBody.dataset.simBound = '1';

    const rawLogContent = terminalBody ? terminalBody.textContent : '';

    // Structure terminal body into styled line elements
    if (terminalBody && rawLogContent) {
      const rawLogLines = rawLogContent.split('\n');
      terminalBody.innerHTML = '';
      rawLogLines.forEach(function (line, idx) {
        const lineDiv = document.createElement('div');
        lineDiv.className = 'term-line';
        lineDiv.setAttribute('data-line', idx);
        if (line.includes('UVM_ERROR') || line.includes('UVM_FATAL')) {
          lineDiv.classList.add('line-error');
        } else if (line.includes('UVM_WARNING')) {
          lineDiv.classList.add('line-warning');
        } else if (line.includes('UVM_INFO')) {
          lineDiv.classList.add('line-info');
        }
        lineDiv.textContent = line || '\u00A0';
        terminalBody.appendChild(lineDiv);
      });
    }

    const SIM_COMMANDS = {
      questa: 'make -f Makefile.questa run',
      vcs: 'make -f Makefile.vcs run',
      xcelium: 'make -f Makefile.ius run'
    };

    simTabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        simTabs.forEach(function (t) { t.classList.remove('active'); });
        tab.classList.add('active');
        const sim = tab.getAttribute('data-sim');
        if (simCmdText && SIM_COMMANDS[sim]) {
          simCmdText.textContent = SIM_COMMANDS[sim];
        }
      });
    });

    if (btnCopyCmd && simCmdText && global.PageCommon && global.PageCommon.clipboard) {
      btnCopyCmd.addEventListener('click', function () {
        global.PageCommon.clipboard.copyText(simCmdText.textContent).then(function () {
          global.PageCommon.clipboard.bindCopyFeedback(btnCopyCmd, 'Copy', 'Copied!');
        });
      });
    }

    termFilters.forEach(function (btn) {
      btn.addEventListener('click', function () {
        termFilters.forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');
        const level = btn.getAttribute('data-level');
        if (!terminalBody) return;

        const allLines = terminalBody.querySelectorAll('.term-line');
        allLines.forEach(function (lineEl) {
          const text = lineEl.textContent;
          if (level === 'all') {
            lineEl.style.display = '';
          } else if (level === 'info') {
            const show = lineEl.classList.contains('line-info') || text.includes('---') || text.includes('Report counts') || text.includes('PASSED');
            lineEl.style.display = show ? '' : 'none';
          } else if (level === 'warning') {
            const show = lineEl.classList.contains('line-warning') || text.includes('---');
            lineEl.style.display = show ? '' : 'none';
          } else if (level === 'error') {
            const show = lineEl.classList.contains('line-error') || text.includes('---');
            lineEl.style.display = show ? '' : 'none';
          }
        });
      });
    });
  }

  // =========================================================================
  // Interactive Visual Flow Stepper
  // =========================================================================

  function initFlowStepper(studioController) {
    const stepperSection = document.getElementById('visual-flow-stepper');
    const stepNodes = document.querySelectorAll('.step-node');
    const stepPrevBtn = document.getElementById('stepper-prev');
    const stepNextBtn = document.getElementById('stepper-next');
    const stepPlayBtn = document.getElementById('stepper-play');
    const stepActiveTitle = document.getElementById('step-active-title');
    const stepActiveComp = document.getElementById('step-active-comp');
    const stepActiveDesc = document.getElementById('step-active-desc');
    const stepActiveLog = document.getElementById('step-active-log');
    const stepStateBadge = document.getElementById('step-state-badge');
    const btnJumpCode = document.getElementById('btn-jump-code');
    const btnJumpLog = document.getElementById('btn-jump-log');
    const stepperPayloadEl = document.getElementById('stepper-payload');
    const terminalBody = document.getElementById('terminal-body');
    const studioCodeContainer = document.getElementById('studio-code-container');
    const animSection = document.getElementById('scenario-anim-section');
    const animType = animSection ? animSection.getAttribute('data-anim') : '';
    const stepperProgressLabel = document.getElementById('stepper-progress-label');
    const stepDetailCard = document.getElementById('step-detail-card');
    const stepperTimeline = document.getElementById('stepper-timeline');

    if (!stepperSection || !stepNodes.length || stepperSection.dataset.stepperBound) return;
    stepperSection.dataset.stepperBound = '1';

    let stepperSteps = [];
    try {
      if (stepperPayloadEl && stepperPayloadEl.getAttribute('data-stepper')) {
        stepperSteps = JSON.parse(stepperPayloadEl.getAttribute('data-stepper'));
      }
    } catch (e) {
      console.warn('Could not parse stepper payload', e);
    }
    if (!stepperSteps || stepperSteps.length === 0) return;

    const zipPayloadEl = document.getElementById('zip-payload');
    let filesList = [];
    try {
      if (zipPayloadEl && zipPayloadEl.getAttribute('data-zip')) {
        filesList = JSON.parse(zipPayloadEl.getAttribute('data-zip'));
      }
    } catch (e) { }

    let currentStepIdx = 0;
    let playInterval = null;

    function scrollToHighlightedCode() {
      const activeIdx = studioController ? studioController.getCurrentFileIdx() : 0;
      const activePane = document.getElementById(`file-pane-${activeIdx}`);
      const step = stepperSteps[currentStepIdx];
      if (!step || !step.highlight_line) return;
      const targetRow = activePane ? activePane.querySelector(`tr[data-line="${step.highlight_line}"], tr#L${step.highlight_line}`) : null;
      if (targetRow && studioCodeContainer) {
        const rowTop = targetRow.offsetTop;
        studioCodeContainer.scrollTo({
          top: Math.max(0, rowTop - (studioCodeContainer.clientHeight / 2)),
          behavior: 'smooth'
        });
      }
    }

    function scrollToHighlightedLog() {
      const step = stepperSteps[currentStepIdx];
      if (!terminalBody || !step || !step.log_snippet) return;
      const snippet = step.log_snippet.trim();
      if (!snippet) return;

      // Clear previous line highlights
      terminalBody.querySelectorAll('.term-line.term-line-highlight').forEach(function (el) {
        el.classList.remove('term-line-highlight');
      });

      const allLines = terminalBody.querySelectorAll('.term-line');
      if (!allLines.length) return;

      let targetEl = null;

      // 1. Direct substring match
      for (let i = 0; i < allLines.length; i++) {
        const lineText = allLines[i].textContent.trim();
        if (lineText.includes(snippet) || (snippet.length > 12 && snippet.includes(lineText))) {
          targetEl = allLines[i];
          break;
        }
      }

      // 2. Token-based fallback matching for robust partial hits
      if (!targetEl) {
        const tokens = snippet.split(/[\s:\[\]@\(\)]+/).filter(function (t) { return t.length > 4; });
        for (let i = 0; i < allLines.length; i++) {
          const lineText = allLines[i].textContent;
          const matchCount = tokens.filter(function (t) { return lineText.includes(t); }).length;
          if (matchCount >= 2 || (tokens.length === 1 && matchCount === 1)) {
            targetEl = allLines[i];
            break;
          }
        }
      }

      if (targetEl) {
        // Ensure line is visible if a filter was active
        if (targetEl.style.display === 'none') {
          const allBtn = document.querySelector('.term-filter[data-level="all"]');
          if (allBtn) allBtn.click();
        }

        targetEl.classList.add('term-line-highlight');
        const targetTop = targetEl.offsetTop - terminalBody.offsetTop;
        terminalBody.scrollTo({
          top: Math.max(0, targetTop - (terminalBody.clientHeight / 2) + 20),
          behavior: 'smooth'
        });
      }
    }

    function renderStep(idx) {
      if (idx < 0) idx = 0;
      if (idx >= stepperSteps.length) idx = stepperSteps.length - 1;
      currentStepIdx = idx;

      const step = stepperSteps[idx];

      stepNodes.forEach(function (node, i) {
        const isCurrent = i === idx;
        node.classList.toggle('active', isCurrent);
        node.classList.toggle('completed', i < idx);
        node.setAttribute('aria-selected', isCurrent ? 'true' : 'false');
        node.setAttribute('aria-current', isCurrent ? 'step' : 'false');
        node.setAttribute('tabindex', isCurrent ? '0' : '-1');
      });

      const activeNode = stepNodes[idx];
      if (activeNode) {
        if (stepDetailCard && activeNode.id) {
          stepDetailCard.setAttribute('aria-labelledby', activeNode.id);
        }
        try {
          activeNode.scrollIntoView({ block: 'nearest', inline: 'nearest' });
        } catch (err) { }
      }

      if (stepperProgressLabel) {
        stepperProgressLabel.textContent = `${idx + 1} / ${stepperSteps.length}`;
      }

      if (stepActiveTitle) stepActiveTitle.textContent = step.title;
      if (stepActiveComp) stepActiveComp.textContent = `Target: ${step.component}`;
      if (stepActiveDesc) stepActiveDesc.textContent = step.desc;
      if (stepActiveLog) stepActiveLog.textContent = step.log_snippet;

      if (stepStateBadge) {
        if (step.state) {
          stepStateBadge.textContent = step.state;
          stepStateBadge.style.display = 'inline-flex';
        } else {
          stepStateBadge.style.display = 'none';
        }
      }

      if (stepPrevBtn) stepPrevBtn.disabled = idx === 0;
      if (stepNextBtn) stepNextBtn.disabled = idx === stepperSteps.length - 1;

      // Topology card highlight
      document.querySelectorAll('.topo-card').forEach(function (card) {
        const text = card.textContent.toLowerCase();
        const compTarget = step.component.toLowerCase();
        const match = compTarget.split(/[,&]/).some(function (c) { return text.includes(c.trim()); });
        card.classList.toggle('highlighted', match);
      });

      // Synchronize with Code Studio
      if (step.highlight_file && studioController && studioController.switchFileTab) {
        const fileIndex = filesList.findIndex(function (f) { return f.name.includes(step.highlight_file); });
        if (fileIndex !== -1 && fileIndex !== studioController.getCurrentFileIdx()) {
          studioController.switchFileTab(fileIndex);
        }
      }

      if (step.highlight_line) {
        const activeIdx = studioController ? studioController.getCurrentFileIdx() : 0;
        const activePane = document.getElementById(`file-pane-${activeIdx}`);
        const targetRow = activePane ? activePane.querySelector(`tr[data-line="${step.highlight_line}"], tr#L${step.highlight_line}`) : null;
        if (targetRow) {
          document.querySelectorAll('.file-code-pane tr.stepper-highlight').forEach(function (tr) {
            tr.classList.remove('stepper-highlight');
          });
          targetRow.classList.add('stepper-highlight');
          if (studioCodeContainer) {
            const rowTop = targetRow.offsetTop;
            studioCodeContainer.scrollTo({
              top: Math.max(0, rowTop - (studioCodeContainer.clientHeight / 2)),
              behavior: 'smooth'
            });
          }
        }
      }

      // Synchronize with simulation log trace
      scrollToHighlightedLog();

      // Synchronize with visual concept animation
      updateScenarioAnimation(animType, idx, step);
    }

    function updateScenarioAnimation(type, idx, step) {
      if (!type) return;
      if (animSection) {
        animSection.classList.remove('anim-stepping');
        void animSection.offsetWidth;
        animSection.classList.add('anim-stepping');
      }

      if (type === 'fifo') {
        const slots = document.querySelectorAll('.anim-fifo-slots .slot');
        const countLabel = document.getElementById('fifo-count-label');
        const prodBadge = document.getElementById('fifo-prod-badge');
        const consBadge = document.getElementById('fifo-cons-badge');
        const prodActor = document.getElementById('fifo-actor-prod');

        slots.forEach(function (s, i) {
          s.style.transitionDelay = (idx === 1 ? i * 65 : 0) + 'ms';
        });

        if (idx === 0) {
          slots.forEach(function (s) { s.className = 'slot'; });
          if (countLabel) countLabel.textContent = '0 / 10';
          if (prodBadge) { prodBadge.textContent = 'Ready'; prodBadge.className = 'actor-badge ready'; }
          if (consBadge) { consBadge.textContent = 'Waiting'; consBadge.className = 'actor-badge waiting'; }
          if (prodActor) prodActor.classList.remove('blocked');
        } else if (idx === 1) {
          slots.forEach(function (s) { s.className = 'slot filled'; });
          if (countLabel) countLabel.textContent = '10 / 10 [FULL]';
          if (prodBadge) { prodBadge.textContent = 'Bursting (try_put)'; prodBadge.className = 'actor-badge burst'; }
          if (consBadge) { consBadge.textContent = 'Asleep (#100)'; consBadge.className = 'actor-badge waiting'; }
          if (prodActor) prodActor.classList.remove('blocked');
        } else if (idx === 2) {
          slots.forEach(function (s) { s.className = 'slot full-blocked'; });
          if (countLabel) countLabel.textContent = '10 / 10 [BLOCKED]';
          if (prodBadge) { prodBadge.textContent = 'BLOCKED (Back-Pressure)'; prodBadge.className = 'actor-badge blocked'; }
          if (consBadge) { consBadge.textContent = 'Waking up'; consBadge.className = 'actor-badge'; }
          if (prodActor) prodActor.classList.add('blocked');
        } else if (idx === 3) {
          slots.forEach(function (s, i) {
            s.className = i === 0 ? 'slot popping' : 'slot filled';
          });
          if (countLabel) countLabel.textContent = '9 / 10 (Item Released)';
          if (prodBadge) { prodBadge.textContent = 'Unblocking'; prodBadge.className = 'actor-badge ready'; }
          if (consBadge) { consBadge.textContent = 'GET(data 0)'; consBadge.className = 'actor-badge reading'; }
          if (prodActor) prodActor.classList.remove('blocked');
        } else if (idx === 4) {
          slots.forEach(function (s) { s.className = 'slot filled'; });
          if (countLabel) countLabel.textContent = '10 / 10 [RESUMED]';
          if (prodBadge) { prodBadge.textContent = 'Resumed (Put OK)'; prodBadge.className = 'actor-badge ready'; }
          if (consBadge) { consBadge.textContent = 'Consuming'; consBadge.className = 'actor-badge'; }
          if (prodActor) prodActor.classList.remove('blocked');
        }
      } else if (type === 'objections') {
        const counterDigit = document.getElementById('obj-counter-digit');
        const drainStatus = document.getElementById('obj-drain-status');
        const bar15 = document.getElementById('gbar-15');
        const bar25 = document.getElementById('gbar-25');
        const bar35 = document.getElementById('gbar-35');
        const bar50 = document.getElementById('gbar-50');
        const barDrain = document.getElementById('gbar-drain');

        if (idx === 0) {
          if (counterDigit) counterDigit.textContent = '0';
          if (drainStatus) { drainStatus.textContent = 'Drain Time: 10 ns (Armed)'; drainStatus.className = 'anim-obj-drain-status ready'; }
          [bar15, bar25, bar35, bar50, barDrain].forEach(function (b) { if (b) b.className = 'gantt-bar'; });
        } else if (idx === 1) {
          if (counterDigit) counterDigit.textContent = '4';
          if (drainStatus) { drainStatus.textContent = '4 Threads Running Concurrently'; drainStatus.className = 'anim-obj-drain-status running'; }
          [bar15, bar25, bar35, bar50].forEach(function (b) { if (b) b.className = 'gantt-bar active'; });
          if (barDrain) barDrain.className = 'gantt-bar gantt-drain-bar';
        } else if (idx === 2) {
          if (counterDigit) counterDigit.textContent = '1';
          if (drainStatus) { drainStatus.textContent = 'Threads Dropping (35ns reached)'; drainStatus.className = 'anim-obj-drain-status running'; }
          if (bar15) bar15.className = 'gantt-bar done';
          if (bar25) bar25.className = 'gantt-bar done';
          if (bar35) bar35.className = 'gantt-bar done';
          if (bar50) bar50.className = 'gantt-bar active';
          if (barDrain) barDrain.className = 'gantt-bar gantt-drain-bar';
        } else if (idx === 3) {
          if (counterDigit) counterDigit.textContent = '0';
          if (drainStatus) { drainStatus.textContent = 'Objections = 0 -> DRAIN WATCHDOG ACTIVE (10ns)'; drainStatus.className = 'anim-obj-drain-status drain-active'; }
          [bar15, bar25, bar35, bar50].forEach(function (b) { if (b) b.className = 'gantt-bar done'; });
          if (barDrain) barDrain.className = 'gantt-bar gantt-drain-bar active';
        } else if (idx === 4) {
          if (counterDigit) counterDigit.textContent = '0';
          if (drainStatus) { drainStatus.textContent = 'Drain Expired -> Test Done @ 60ns'; drainStatus.className = 'anim-obj-drain-status completed'; }
          [bar15, bar25, bar35, bar50].forEach(function (b) { if (b) b.className = 'gantt-bar done'; });
          if (barDrain) barDrain.className = 'gantt-bar gantt-drain-bar done';
        }
      } else if (type === 'tlm2') {
        const pktFw = document.getElementById('tlm2-packet-fw');
        const pktBw = document.getElementById('tlm2-packet-bw');
        const hostNode = document.getElementById('tlm2-host-node');
        const devNode = document.getElementById('tlm2-dev-node');

        if (idx === 0) {
          if (pktFw) { pktFw.textContent = 'TOKEN (BEGIN_REQ)'; pktFw.className = 'tlm2-packet moving-fw'; }
          if (pktBw) pktBw.className = 'tlm2-packet';
          if (hostNode) hostNode.className = 'tlm2-node tlm2-host active';
          if (devNode) devNode.className = 'tlm2-node tlm2-device';
        } else if (idx === 1) {
          if (pktFw) { pktFw.textContent = 'DATA (DE AD BE EF)'; pktFw.className = 'tlm2-packet at-target'; }
          if (pktBw) pktBw.className = 'tlm2-packet';
          if (hostNode) hostNode.className = 'tlm2-node tlm2-host';
          if (devNode) devNode.className = 'tlm2-node tlm2-device active';
        } else if (idx === 2) {
          if (pktFw) pktFw.className = 'tlm2-packet';
          if (pktBw) { pktBw.textContent = 'HANDSHAKE (ACK)'; pktBw.className = 'tlm2-packet moving-bw'; }
          if (hostNode) hostNode.className = 'tlm2-node tlm2-host';
          if (devNode) devNode.className = 'tlm2-node tlm2-device active';
        } else if (idx === 3) {
          if (pktFw) pktFw.className = 'tlm2-packet';
          if (pktBw) { pktBw.textContent = 'UVM_TLM_COMPLETED'; pktBw.className = 'tlm2-packet completed'; }
          if (hostNode) hostNode.className = 'tlm2-node tlm2-host completed';
          if (devNode) devNode.className = 'tlm2-node tlm2-device completed';
        }
      } else if (type === 'ral') {
        const blocks = ['ral-block-seq', 'ral-block-adapt', 'ral-block-bus', 'ral-block-dut', 'ral-block-mirror'];
        const arrows = ['ral-arr-1', 'ral-arr-2', 'ral-arr-3', 'ral-arr-4'];
        blocks.forEach(function (b) {
          const el = document.getElementById(b);
          if (el) el.classList.remove('active', 'completed');
        });
        arrows.forEach(function (a) {
          const el = document.getElementById(a);
          if (el) el.classList.remove('active', 'done');
        });

        if (idx === 0) {
          const b = document.getElementById('ral-block-seq');
          const a1 = document.getElementById('ral-arr-1');
          if (b) b.classList.add('active');
          if (a1) a1.classList.add('active');
        } else if (idx === 1) {
          const b1 = document.getElementById('ral-block-seq');
          const b2 = document.getElementById('ral-block-adapt');
          const a1 = document.getElementById('ral-arr-1');
          const a2 = document.getElementById('ral-arr-2');
          if (b1) b1.classList.add('completed');
          if (b2) b2.classList.add('active');
          if (a1) a1.classList.add('done');
          if (a2) a2.classList.add('active');
        } else if (idx === 2) {
          ['ral-block-seq', 'ral-block-adapt'].forEach(function (id) {
            const el = document.getElementById(id);
            if (el) el.classList.add('completed');
          });
          ['ral-arr-1', 'ral-arr-2'].forEach(function (id) {
            const el = document.getElementById(id);
            if (el) el.classList.add('done');
          });
          const b3 = document.getElementById('ral-block-bus');
          const b4 = document.getElementById('ral-block-dut');
          const a3 = document.getElementById('ral-arr-3');
          if (b3) b3.classList.add('active');
          if (b4) b4.classList.add('active');
          if (a3) a3.classList.add('active');
        } else if (idx === 3) {
          blocks.forEach(function (id) {
            const el = document.getElementById(id);
            if (el) el.classList.add('completed');
          });
          arrows.forEach(function (id) {
            const el = document.getElementById(id);
            if (el) el.classList.add('done');
          });
          const bm = document.getElementById('ral-block-mirror');
          const a4 = document.getElementById('ral-arr-4');
          if (bm) bm.classList.add('active');
          if (a4) a4.classList.add('active');
        }
      } else if (type === 'phasing') {
        const dirBadge = document.getElementById('phasing-dir-badge');
        const allNodes = document.querySelectorAll('.p-node');
        allNodes.forEach(function (n, i) {
          n.className = n.className.replace(/highlight-\w+/g, '').trim();
          n.style.transitionDelay = (i * 95) + 'ms';
        });

        if (idx === 0) {
          if (dirBadge) dirBadge.textContent = '↓ Top-Down Phasing (build_phase)';
          const top = document.getElementById('pnode-top');
          const a1 = document.getElementById('pnode-a1');
          const a2 = document.getElementById('pnode-a2');
          if (top) top.classList.add('highlight-build');
          if (a1) a1.classList.add('highlight-build');
          if (a2) a2.classList.add('highlight-build');
        } else if (idx === 1) {
          if (dirBadge) dirBadge.textContent = '↑ Bottom-Up Phasing (end_of_elaboration)';
          const b1 = document.getElementById('pnode-b1');
          const d1 = document.getElementById('pnode-d1');
          const b2 = document.getElementById('pnode-b2');
          const d2 = document.getElementById('pnode-d2');
          [b1, d1, b2, d2].forEach(function (n) { if (n) n.classList.add('highlight-elaboration'); });
        } else if (idx === 2) {
          if (dirBadge) dirBadge.textContent = '⚡ Time-Consuming Phasing (run_phase @ 0ns)';
          allNodes.forEach(function (n) { n.classList.add('highlight-run'); });
        } else if (idx === 3) {
          if (dirBadge) dirBadge.textContent = '⏱ Advancing Simulation Time (t = 500ns)';
          allNodes.forEach(function (n) { n.classList.add('highlight-run'); });
        } else if (idx === 4) {
          if (dirBadge) dirBadge.textContent = '✓ Cleanup & Reporting (extract, check, report)';
          allNodes.forEach(function (n) { n.classList.add('highlight-cleanup'); });
        }
      }
    }

    function stopAutoPlay() {
      if (playInterval) {
        clearInterval(playInterval);
        playInterval = null;
        if (stepPlayBtn) stepPlayBtn.textContent = 'Play ▶';
      }
    }

    if (stepPrevBtn) {
      stepPrevBtn.addEventListener('click', function () {
        stopAutoPlay();
        renderStep(currentStepIdx - 1);
      });
    }

    if (stepNextBtn) {
      stepNextBtn.addEventListener('click', function () {
        stopAutoPlay();
        renderStep(currentStepIdx + 1);
      });
    }

    if (btnJumpCode) {
      btnJumpCode.addEventListener('click', function () {
        scrollToHighlightedCode();
        if (studioCodeContainer) {
          studioCodeContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      });
    }

    if (btnJumpLog) {
      btnJumpLog.addEventListener('click', function () {
        scrollToHighlightedLog();
        if (terminalBody) {
          terminalBody.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      });
    }

    stepNodes.forEach(function (node, idx) {
      node.addEventListener('click', function () {
        stopAutoPlay();
        renderStep(idx);
      });
    });

    if (stepperTimeline) {
      stepperTimeline.addEventListener('keydown', function (e) {
        let nextIdx = null;
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
          nextIdx = (currentStepIdx + 1) % stepperSteps.length;
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
          nextIdx = (currentStepIdx - 1 + stepperSteps.length) % stepperSteps.length;
        } else if (e.key === 'Home') {
          nextIdx = 0;
        } else if (e.key === 'End') {
          nextIdx = stepperSteps.length - 1;
        }
        if (nextIdx !== null) {
          e.preventDefault();
          stopAutoPlay();
          renderStep(nextIdx);
          if (stepNodes[nextIdx]) {
            stepNodes[nextIdx].focus();
          }
        }
      });
    }

    if (stepPlayBtn) {
      stepPlayBtn.addEventListener('click', function () {
        if (playInterval) {
          stopAutoPlay();
        } else {
          if (currentStepIdx >= stepperSteps.length - 1) {
            renderStep(0);
          }
          stepPlayBtn.textContent = 'Pause ❚❚';
          playInterval = setInterval(function () {
            if (currentStepIdx >= stepperSteps.length - 1) {
              stopAutoPlay();
            } else {
              renderStep(currentStepIdx + 1);
            }
          }, 3800);
        }
      });
    }

    renderStep(0);
  }

  function initBannerFilesPopover(studio) {
    const banner = document.querySelector('.example-source-banner');
    const filesBadge = banner ? banner.querySelector('.badge-files') : null;
    if (!banner || !filesBadge || filesBadge.dataset.popoverBound) return;

    let zipFiles = [];
    let fileNames = [];
    const zipPayloadEl = document.getElementById('zip-payload');
    if (zipPayloadEl) {
      try {
        const parsed = JSON.parse(zipPayloadEl.textContent);
        if (Array.isArray(parsed)) {
          zipFiles = parsed;
          fileNames = parsed.map(f => f && f.name).filter(Boolean);
        }
      } catch (e) { }
    }
    if (!fileNames.length) {
      fileNames = Array.from(document.querySelectorAll('.studio-tab')).map(t => t.textContent.trim()).filter(Boolean);
    }
    if (!fileNames.length) return;

    filesBadge.dataset.popoverBound = '1';
    filesBadge.classList.add('is-interactive');
    filesBadge.setAttribute('role', 'button');
    filesBadge.setAttribute('tabindex', '0');
    filesBadge.setAttribute('aria-expanded', 'false');
    filesBadge.title = 'Click to view example files';

    let popover = null;

    function closePopover() {
      if (popover && popover.parentNode) {
        popover.parentNode.removeChild(popover);
      }
      popover = null;
      filesBadge.setAttribute('aria-expanded', 'false');
    }

    function togglePopover(e) {
      e.stopPropagation();
      if (popover) {
        closePopover();
        return;
      }
      popover = document.createElement('div');
      popover.className = 'banner-files-popover';
      popover.setAttribute('role', 'menu');

      fileNames.forEach((name, idx) => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'banner-files-popover-item';
        item.setAttribute('role', 'menuitem');
        item.textContent = name;
        item.addEventListener('click', () => {
          const pane = document.getElementById(`file-pane-${idx}`) ||
            Array.from(document.querySelectorAll('.file-code-pane')).find(p => p.getAttribute('data-filename') === name);
          const zipEntry = zipFiles.find(f => f && f.name === name) || zipFiles[idx];
          if (window.parent && window.parent !== window && pane) {
            window.parent.postMessage({
              type: 'openExampleSource',
              fileName: name,
              tableHtml: pane.innerHTML,
              rawContent: zipEntry ? zipEntry.content : ''
            }, '*');
          } else {
            if (studio && typeof studio.switchFile === 'function') {
              studio.switchFile(name);
            } else if (studio && typeof studio.switchFileTab === 'function') {
              studio.switchFileTab(idx);
            }
            const studioContainer = document.querySelector('.studio-container') || document.getElementById('studio-code-container');
            if (studioContainer) {
              studioContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
          }
          closePopover();
        });
        popover.appendChild(item);
      });

      banner.appendChild(popover);
      filesBadge.setAttribute('aria-expanded', 'true');
    }

    filesBadge.addEventListener('click', togglePopover);
    filesBadge.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        togglePopover(e);
      } else if (e.key === 'Escape') {
        closePopover();
      }
    });
    document.addEventListener('click', (e) => {
      if (popover && !popover.contains(e.target) && e.target !== filesBadge) {
        closePopover();
      }
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && popover) {
        closePopover();
      }
    });
  }

  function initExampleFeatures() {
    initZipDownload();
    initSimulationConsole();
    const studio = global.PageCommon && global.PageCommon.getStudioController
      ? global.PageCommon.getStudioController()
      : null;
    initBannerFilesPopover(studio);
    if (document.getElementById('visual-flow-stepper')) {
      initFlowStepper(studio);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initExampleFeatures);
  } else {
    initExampleFeatures();
  }

  global.ExamplePage = {
    crc32: crc32,
    createNativeZipBlob: createNativeZipBlob,
    initZipDownload: initZipDownload,
    initSimulationConsole: initSimulationConsole,
    initFlowStepper: initFlowStepper
  };
})(window);
