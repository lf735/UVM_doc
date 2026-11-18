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

      const pageTitle = (document.title.split('|')[0] || 'uvm_archive').trim().toLowerCase().replace(/[^a-z0-9_]/g, '_');
      function triggerDownload(blob) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${pageTitle}.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }

      if (typeof global.JSZip === 'function') {
        const zip = new global.JSZip();
        filesList.forEach(function (f) {
          zip.file(f.name, f.content);
        });
        zip.generateAsync({ type: 'blob' }).then(triggerDownload);
        return;
      }

      triggerDownload(createNativeZipBlob(filesList));
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
    const stepResetBtn = document.getElementById('stepper-reset');
    const stepSpeedSelect = document.getElementById('stepper-speed');
    const stickyBar = document.getElementById('stepper-sticky-bar');
    const stickyPrevMajorBtn = document.getElementById('sticky-stepper-prev-major');
    const stickyPrevBtn = document.getElementById('sticky-stepper-prev');
    const stickyNextBtn = document.getElementById('sticky-stepper-next');
    const stickyNextMajorBtn = document.getElementById('sticky-stepper-next-major');
    const stickyPlayBtn = document.getElementById('sticky-stepper-play');
    const stickyResetBtn = document.getElementById('sticky-stepper-reset');
    const stickySpeedSelect = document.getElementById('sticky-stepper-speed');
    const stickyProgress = document.getElementById('sticky-stepper-progress');
    const stickyTitle = document.getElementById('sticky-stepper-title');
    const stickyState = document.getElementById('sticky-stepper-state');
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
    let currentTraceIdx = 0;
    let playInterval = null;
    let isSteppingMode = false;
    let playbackSpeed = 1;
    let stepToLogLineIdx = [];
    let executionTrace = [];
    let majorStepToTraceIdx = [];

    function isExecutableLogLine(text) {
      const t = text.trim();
      if (!t) return false;
      if (t.startsWith('---') || t.startsWith('***')) return false;
      if (t.startsWith('Questa/VCS') || t.startsWith('Example:')) return false;
      if (t.startsWith('UVM_INFO :') || t.startsWith('UVM_WARNING :') || t.startsWith('UVM_ERROR :') || t.startsWith('UVM_FATAL :')) return false;
      if (t.startsWith('[')) return false;
      if (/^(Name\s+Type|uvm_test_top|env\s+|agent\s+)/.test(t)) return false;
      return /^(UVM_INFO|UVM_WARNING|UVM_ERROR|UVM_FATAL|\d+\s*:)/.test(t);
    }

    function parseLogFileLine(text) {
      const m = text.match(/\b([\w./-]+\.(?:svh?|v|c|h))\((\d+)\)/i);
      if (!m) return null;
      return { file: m[1], line: parseInt(m[2], 10) };
    }

    function parseLogTime(text) {
      const m = text.match(/@\s*(\d+\s*\w+)|^(\d+)\s*:/);
      if (!m) return '';
      return m[1] ? m[1] : `${m[2]} ns`;
    }

    function findMatchingLogLineIdx(step, allLines) {
      if (!step || !step.log_snippet || !allLines.length) return -1;
      const snippet = step.log_snippet.trim();
      if (!snippet) return -1;

      for (let i = 0; i < allLines.length; i++) {
        const lineText = allLines[i].textContent.trim();
        if (lineText.includes(snippet) || (snippet.length > 12 && snippet.includes(lineText))) {
          return i;
        }
      }

      const tokens = snippet.split(/[\s:\[\]@\(\)]+/).filter(function (t) { return t.length > 4; });
      for (let i = 0; i < allLines.length; i++) {
        const lineText = allLines[i].textContent;
        const matchCount = tokens.filter(function (t) { return lineText.includes(t); }).length;
        if (matchCount >= 2 || (tokens.length === 1 && matchCount === 1)) {
          return i;
        }
      }
      return -1;
    }

    function isExecutableCodeText(rawText) {
      const t = rawText.replace(/\/\/.*$/, '').trim();
      if (!t) return false;
      if (t.startsWith('/*') || t.startsWith('*') || t.startsWith('*/')) return false;
      if (/^(begin|end|endclass|endfunction|endtask|endmodule|endpackage|endinterface|endprogram|else\s+begin|else|\{|\}|;)$/i.test(t)) return false;
      if (/^(class|virtual\s+class|import|typedef|package|module|interface|program|function|virtual\s+function|task|virtual\s+task|endcase)\b/i.test(t)) return false;
      return true;
    }

    function stripSvComment(rawText) {
      return rawText.replace(/\/\/.*$/, '').trim();
    }

    function findBlockEnd(lineMap, maxLine, startLn) {
      let depth = 0;
      let sawBegin = false;
      for (let ln = startLn; ln <= maxLine; ln++) {
        const t = stripSvComment(lineMap.get(ln) || '');
        if (!t) continue;
        const begins = (t.match(/\b(begin|fork)\b/g) || []).length;
        const ends = (t.match(/\b(end|join|join_any|join_none)\b/g) || []).length;
        if (begins > 0) sawBegin = true;
        depth += begins - ends;
        if (sawBegin && depth <= 0) return ln;
        if (!sawBegin && ln > startLn && t.endsWith(';')) return ln;
      }
      return startLn;
    }

    function findEnclosingMethodStart(lineMap, targetLn) {
      for (let ln = targetLn; ln >= Math.max(1, targetLn - 40); ln--) {
        const t = stripSvComment(lineMap.get(ln) || '');
        if (/^(?:virtual\s+)?(?:function|task|initial)\b/i.test(t)) return ln;
        if (ln < targetLn && /^(endfunction|endtask|endmodule|endclass)\b/i.test(t)) return ln + 1;
      }
      return Math.max(1, targetLn - 15);
    }

    function findEnclosingLoop(lineMap, maxLine, lnA, lnB) {
      const minLn = Math.max(1, Math.min(lnA, lnB) - 35);
      for (let ln = Math.min(lnA, lnB); ln >= minLn; ln--) {
        const t = stripSvComment(lineMap.get(ln) || '');
        if (/^(for|repeat|foreach|while)\s*\(/i.test(t)) {
          const endLn = findBlockEnd(lineMap, maxLine, ln);
          if (lnA > ln && lnA <= endLn && lnB > ln && lnB <= endLn) {
            return { start: ln, end: endLn };
          }
        }
        if (/^(endfunction|endtask|endmodule)\b/i.test(t)) break;
      }
      return null;
    }

    function collectControlFlowSteps(lineMap, maxLine, fromLn, toLn, ctx, outSteps) {
      let ln = fromLn;
      let parenDepth = 0;
      let inMultiLineLog = false;

      while (ln <= toLn) {
        const rawTxt = lineMap.get(ln);
        if (rawTxt === undefined) {
          ln++;
          continue;
        }
        const cleaned = stripSvComment(rawTxt);
        if (!cleaned) {
          ln++;
          continue;
        }

        if (/^(endfunction|endtask|endmodule|endclass)\b/i.test(cleaned)) {
          break;
        }

        // Skip continuation lines of a multi-line statement (e.g. $sformatf args on next line)
        if (parenDepth > 0 || inMultiLineLog) {
          parenDepth += (cleaned.match(/\(/g) || []).length - (cleaned.match(/\)/g) || []).length;
          if (parenDepth <= 0 && cleaned.endsWith(';')) {
            parenDepth = 0;
            inMultiLineLog = false;
          }
          ln++;
          continue;
        }

        // If we hit an `else` while stepping forward after an `if` branch, skip the untaken `else` block
        if (/^(?:end\s+)?else\b/i.test(cleaned)) {
          const elseEnd = findBlockEnd(lineMap, maxLine, ln);
          if (elseEnd < toLn) {
            ln = elseEnd + 1;
            continue;
          }
          // If target is inside else, just skip the `else` keyword line itself
          ln++;
          continue;
        }

        // If we hit `if (...)`, check if `toLn` is past the `if` body and inside `else`
        if (/^if\s*\(/i.test(cleaned)) {
          const ifEnd = findBlockEnd(lineMap, maxLine, ln);
          const nextAfterIf = stripSvComment(lineMap.get(ifEnd + 1) || '');
          const hasElse = /^(?:end\s+)?else\b/i.test(cleaned) || /^else\b/i.test(nextAfterIf);
          // Emit the `if (...)` condition check line
          outSteps.push({
            termIdx: ctx.termIdx,
            majorIdx: ctx.majorIdx,
            file: ctx.file,
            line: ln,
            timeStr: ctx.timeStr,
            text: `L${ln}: ${cleaned}`,
            isCodeOnly: true
          });
          if (hasElse && toLn > ifEnd) {
            const elseStart = /^else\b/i.test(nextAfterIf) ? ifEnd + 1 : ifEnd;
            const elseEnd = findBlockEnd(lineMap, maxLine, elseStart);
            if (toLn <= elseEnd) {
              // Target is in the `else` branch -> jump over `if` body into `else`
              ln = elseStart + 1;
              continue;
            }
          }
          ln++;
          continue;
        }

        // Skip unlogged `uvm_info`/`uvm_error`/`$display` statements that didn't emit a log line
        if (/^(`uvm_(?:info|warning|error|fatal)|uvm_report_(?:info|warning|error|fatal)|\$(?:display|write))\b/i.test(cleaned)) {
          const pOpen = (cleaned.match(/\(/g) || []).length;
          const pClose = (cleaned.match(/\)/g) || []).length;
          if (pOpen > pClose || !cleaned.endsWith(';')) {
            parenDepth = Math.max(0, pOpen - pClose);
            inMultiLineLog = true;
          }
          ln++;
          continue;
        }

        if (isExecutableCodeText(rawTxt)) {
          outSteps.push({
            termIdx: ctx.termIdx,
            majorIdx: ctx.majorIdx,
            file: ctx.file,
            line: ln,
            timeStr: ctx.timeStr,
            text: `L${ln}: ${cleaned}`,
            isCodeOnly: true
          });
          const pOpen = (cleaned.match(/\(/g) || []).length;
          const pClose = (cleaned.match(/\)/g) || []).length;
          if (pOpen > pClose) {
            parenDepth = pOpen - pClose;
          }
        }
        ln++;
      }
    }

    function findStudioFileIndex(filename) {
      if (!filename || !filesList.length) return -1;
      let idx = filesList.findIndex(function (f) { return f.name === filename; });
      if (idx !== -1) return idx;
      idx = filesList.findIndex(function (f) { return f.name.endsWith('/' + filename) || f.name.endsWith('\\' + filename); });
      if (idx !== -1) return idx;
      return filesList.findIndex(function (f) { return f.name.includes(filename); });
    }

    function getFileLinesMap(filename) {
      const fileIndex = findStudioFileIndex(filename);
      if (fileIndex === -1) return null;
      const map = new Map();
      const rawContent = filesList[fileIndex] && filesList[fileIndex].content;
      if (typeof rawContent === 'string' && rawContent.length > 0) {
        const lines = rawContent.split(/\r?\n/);
        for (let i = 0; i < lines.length; i++) {
          map.set(i + 1, lines[i]);
        }
        return map;
      }
      const pane = document.getElementById(`file-pane-${fileIndex}`);
      if (!pane) return null;
      const rows = pane.querySelectorAll('tr[id^="L"], tr[data-line]');
      rows.forEach(function (tr) {
        const idAttr = tr.getAttribute('id') || '';
        const ln = tr.hasAttribute('data-line')
          ? parseInt(tr.getAttribute('data-line'), 10)
          : (idAttr.startsWith('L') ? parseInt(idAttr.slice(1), 10) : NaN);
        if (!isNaN(ln)) {
          const codeCell = tr.querySelector('td.code, td.C, td:last-child');
          map.set(ln, codeCell ? codeCell.textContent : tr.textContent);
        }
      });
      return map;
    }

    function buildLogStepMapping() {
      stepToLogLineIdx = stepperSteps.map(function () { return -1; });
      executionTrace = [];
      majorStepToTraceIdx = stepperSteps.map(function () { return 0; });
      if (!terminalBody) return;
      const allLines = terminalBody.querySelectorAll('.term-line');
      if (!allLines.length) return;

      const logLineToMajorStep = new Map();
      stepperSteps.forEach(function (step, sIdx) {
        const lineIdx = findMatchingLogLineIdx(step, allLines);
        stepToLogLineIdx[sIdx] = lineIdx;
        if (lineIdx !== -1 && !logLineToMajorStep.has(lineIdx)) {
          logLineToMajorStep.set(lineIdx, sIdx);
        }
      });

      const rawLogPoints = [];
      for (let i = 0; i < allLines.length; i++) {
        const lineEl = allLines[i];
        const text = lineEl.textContent.trim();
        const matchedStep = logLineToMajorStep.has(i) ? logLineToMajorStep.get(i) : -1;
        if (isExecutableLogLine(text) || matchedStep !== -1) {
          const fl = parseLogFileLine(text);
          rawLogPoints.push({
            termIdx: i,
            lineEl: lineEl,
            matchedStep: matchedStep,
            file: fl ? fl.file : '',
            line: fl ? fl.line : 0,
            timeStr: parseLogTime(text),
            text: text
          });
        }
      }

      // Weave major steps without console logs (phase/objection) in exact chronological order
      const logPoints = [];
      let rpIdx = 0;
      let lastTermIdx = rawLogPoints.length ? rawLogPoints[0].termIdx : -1;
      for (let sIdx = 0; sIdx < stepperSteps.length; sIdx++) {
        const step = stepperSteps[sIdx];
        const targetLogIdx = stepToLogLineIdx[sIdx];
        if (targetLogIdx !== -1) {
          while (rpIdx < rawLogPoints.length && rawLogPoints[rpIdx].termIdx <= targetLogIdx) {
            const rp = rawLogPoints[rpIdx++];
            const isStart = rp.termIdx === targetLogIdx;
            const prevStep = stepperSteps[Math.max(0, sIdx - 1)] || {};
            logPoints.push({
              termIdx: rp.termIdx,
              lineEl: rp.lineEl,
              isMajorStart: isStart,
              majorIdx: isStart ? sIdx : Math.max(0, sIdx - 1),
              file: rp.file || (isStart ? step.highlight_file : prevStep.highlight_file) || '',
              line: rp.line || (isStart ? step.highlight_line : prevStep.highlight_line) || 0,
              timeStr: rp.timeStr,
              text: rp.text,
              isCodeOnly: false
            });
            lastTermIdx = rp.termIdx;
          }
        } else {
          logPoints.push({
            termIdx: lastTermIdx,
            lineEl: null,
            isMajorStart: true,
            majorIdx: sIdx,
            file: step.highlight_file || '',
            line: step.highlight_line || 0,
            timeStr: step.state || '',
            text: step.title || '',
            isCodeOnly: true
          });
        }
      }
      while (rpIdx < rawLogPoints.length) {
        const rp = rawLogPoints[rpIdx++];
        const lastIdx = Math.max(0, stepperSteps.length - 1);
        const lastStep = stepperSteps[lastIdx] || {};
        logPoints.push({
          termIdx: rp.termIdx,
          lineEl: rp.lineEl,
          isMajorStart: false,
          majorIdx: lastIdx,
          file: rp.file || lastStep.highlight_file || '',
          line: rp.line || lastStep.highlight_line || 0,
          timeStr: rp.timeStr,
          text: rp.text,
          isCodeOnly: false
        });
      }

      const fileCache = new Map();
      function getLines(fname) {
        if (!fname) return null;
        if (!fileCache.has(fname)) {
          fileCache.set(fname, getFileLinesMap(fname));
        }
        return fileCache.get(fname);
      }

      const recordedMajor = new Set();
      for (let p = 0; p < logPoints.length; p++) {
        const cur = logPoints[p];
        const prev = p > 0 ? logPoints[p - 1] : null;
        const lineMap = getLines(cur.file);
        const maxLine = lineMap ? lineMap.size : 0;

        if (lineMap && cur.file && cur.line > 0) {
          const curMethodStart = findEnclosingMethodStart(lineMap, cur.line);
          const prevMethodStart = (prev && prev.file === cur.file) ? findEnclosingMethodStart(lineMap, prev.line) : -1;
          const sameMethod = prev && prev.file === cur.file && curMethodStart === prevMethodStart;

          if (sameMethod && cur.line > prev.line + 1 && (cur.line - prev.line) <= 60) {
            // Forward step inside the same method, respecting if/else & multi-line statements
            collectControlFlowSteps(lineMap, maxLine, prev.line + 1, cur.line - 1, prev, executionTrace);
          } else if (sameMethod && cur.line <= prev.line) {
            // Loop back-edge: finish loop body -> loop header -> re-enter down to cur.line - 1
            const loop = findEnclosingLoop(lineMap, maxLine, prev.line, cur.line);
            if (loop) {
              collectControlFlowSteps(lineMap, maxLine, prev.line + 1, loop.end - 1, prev, executionTrace);
              const headerTxt = stripSvComment(lineMap.get(loop.start) || '');
              if (headerTxt) {
                executionTrace.push({
                  termIdx: prev.termIdx,
                  majorIdx: prev.majorIdx,
                  file: cur.file,
                  line: loop.start,
                  timeStr: prev.timeStr,
                  text: `L${loop.start}: ${headerTxt}`,
                  isCodeOnly: true
                });
              }
              collectControlFlowSteps(lineMap, maxLine, loop.start + 1, cur.line - 1, prev, executionTrace);
            }
          } else if (!sameMethod && cur.line > curMethodStart) {
            // Entering a new method/file: step forward from method header down to cur.line - 1
            const ctx = {
              termIdx: prev ? prev.termIdx : cur.termIdx,
              majorIdx: cur.majorIdx,
              file: cur.file,
              timeStr: prev ? prev.timeStr : cur.timeStr
            };
            collectControlFlowSteps(lineMap, maxLine, curMethodStart + 1, cur.line - 1, ctx, executionTrace);
          }
        }

        const traceIdx = executionTrace.length;
        if (cur.isMajorStart && !recordedMajor.has(cur.majorIdx)) {
          majorStepToTraceIdx[cur.majorIdx] = traceIdx;
          recordedMajor.add(cur.majorIdx);
        }

        executionTrace.push({
          termIdx: cur.termIdx,
          majorIdx: cur.majorIdx,
          file: cur.file,
          line: cur.line,
          timeStr: cur.timeStr,
          text: cur.text,
          isCodeOnly: !!cur.isCodeOnly
        });

        if (cur.lineEl) {
          cur.lineEl.setAttribute('data-trace-idx', String(traceIdx));
          cur.lineEl.setAttribute('data-step-idx', String(cur.majorIdx));
          cur.lineEl.classList.add('term-line-clickable');
          cur.lineEl.title = `Line ${traceIdx + 1} (Step ${cur.majorIdx + 1}) — Click to jump here`;
        }
      }

      terminalBody.addEventListener('click', function (e) {
        const lineEl = e.target.closest('.term-line[data-trace-idx]');
        if (!lineEl) return;
        const tIdx = parseInt(lineEl.getAttribute('data-trace-idx'), 10);
        if (!isNaN(tIdx)) {
          stopAutoPlay();
          isSteppingMode = true;
          renderTraceStep(tIdx);
        }
      });
    }

    function buildCodeStepMarkers() {
      if (!studioCodeContainer || !filesList.length) return;
      const rowMap = new Map();
      stepperSteps.forEach(function (step, sIdx) {
        if (!step.highlight_file || !step.highlight_line) return;
        const fileIndex = findStudioFileIndex(step.highlight_file);
        if (fileIndex === -1) return;
        const pane = document.getElementById(`file-pane-${fileIndex}`);
        if (!pane) return;
        const targetRow = pane.querySelector(`tr[data-line="${step.highlight_line}"], tr#L${step.highlight_line}`);
        if (!targetRow) return;
        if (!rowMap.has(targetRow)) {
          rowMap.set(targetRow, []);
        }
        rowMap.get(targetRow).push(sIdx);
      });

      rowMap.forEach(function (stepIndices, row) {
        const lnCell = row.querySelector('td.L, td:first-child');
        if (!lnCell || lnCell.querySelector('.code-step-marker')) return;
        const firstIdx = stepIndices[0];
        const marker = document.createElement('button');
        marker.type = 'button';
        marker.className = 'code-step-marker';
        marker.setAttribute('data-step-idx', String(firstIdx));
        marker.setAttribute('data-step-indices', stepIndices.join(','));
        marker.textContent = String(firstIdx + 1);
        marker.title = stepIndices.map(function (si) { return `Step ${si + 1}: ${stepperSteps[si].title}`; }).join(' | ');
        marker.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          stopAutoPlay();
          isSteppingMode = true;
          renderStep(firstIdx);
        });
        lnCell.appendChild(marker);
      });
    }

    buildLogStepMapping();
    buildCodeStepMarkers();

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

    function clearConsoleSteppingClasses() {
      if (!terminalBody) return;
      terminalBody.querySelectorAll('.term-line').forEach(function (el) {
        el.classList.remove('term-line-highlight', 'term-line-past', 'term-line-future');
      });
    }

    function scrollToHighlightedLog(explicitTermIdx, shouldScroll) {
      const step = stepperSteps[currentStepIdx];
      if (!terminalBody || !step) return;

      const allLines = terminalBody.querySelectorAll('.term-line');
      if (!allLines.length) return;

      clearConsoleSteppingClasses();

      let targetIdx = (typeof explicitTermIdx === 'number' && explicitTermIdx >= 0)
        ? explicitTermIdx
        : stepToLogLineIdx[currentStepIdx];
      if (targetIdx === undefined || targetIdx === -1) {
        targetIdx = findMatchingLogLineIdx(step, allLines);
      }
      const targetEl = targetIdx >= 0 && targetIdx < allLines.length ? allLines[targetIdx] : null;

      if (isSteppingMode && targetIdx >= 0) {
        for (let i = 0; i < allLines.length; i++) {
          if (i <= targetIdx) {
            allLines[i].classList.add('term-line-past');
          } else {
            allLines[i].classList.add('term-line-future');
          }
        }
      }

      if (targetEl) {
        if (targetEl.style.display === 'none') {
          const allBtn = document.querySelector('.term-filter[data-level="all"]');
          if (allBtn) allBtn.click();
        }

        targetEl.classList.add('term-line-highlight');
        if (shouldScroll) {
          const targetTop = targetEl.offsetTop - terminalBody.offsetTop;
          terminalBody.scrollTo({
            top: Math.max(0, targetTop - (terminalBody.clientHeight / 2) + 20),
            behavior: 'smooth'
          });
        }
      }
    }

    function highlightCodeAt(file, line) {
      if (file && studioController && studioController.switchFileTab) {
        const fileIndex = findStudioFileIndex(file);
        if (fileIndex !== -1 && fileIndex !== studioController.getCurrentFileIdx()) {
          studioController.switchFileTab(fileIndex);
        }
      }

      if (line) {
        const activeIdx = studioController ? studioController.getCurrentFileIdx() : 0;
        const activePane = document.getElementById(`file-pane-${activeIdx}`);
        const targetRow = activePane ? activePane.querySelector(`tr[data-line="${line}"], tr#L${line}`) : null;
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
    }

    function renderStep(idx, traceOverride) {
      if (idx < 0) idx = 0;
      if (idx >= stepperSteps.length) idx = stepperSteps.length - 1;
      currentStepIdx = idx;

      if (!traceOverride && executionTrace.length > 0 && majorStepToTraceIdx[idx] !== undefined) {
        currentTraceIdx = majorStepToTraceIdx[idx];
      }
      const activeTrace = traceOverride || executionTrace[currentTraceIdx] || null;

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
        if (stepperTimeline) {
          const nodeLeft = activeNode.offsetLeft;
          const nodeRight = nodeLeft + activeNode.offsetWidth;
          const viewLeft = stepperTimeline.scrollLeft;
          const viewRight = viewLeft + stepperTimeline.clientWidth;
          if (nodeLeft < viewLeft || nodeRight > viewRight) {
            stepperTimeline.scrollLeft = Math.max(0, nodeLeft - (stepperTimeline.clientWidth / 2) + (activeNode.offsetWidth / 2));
          }
        }
      }

      if (stepperProgressLabel) {
        stepperProgressLabel.textContent = `${idx + 1} / ${stepperSteps.length}`;
      }
      if (stickyProgress) {
        if (executionTrace.length > 0) {
          stickyProgress.textContent = `Step ${idx + 1}/${stepperSteps.length} · Line ${currentTraceIdx + 1}/${executionTrace.length}`;
        } else {
          stickyProgress.textContent = `${idx + 1} / ${stepperSteps.length}`;
        }
        const hoverText = (activeTrace && isSteppingMode) ? `${step.title} — ${activeTrace.text}` : step.title;
        stickyProgress.setAttribute('title', hoverText);
        stickyProgress.setAttribute('data-tooltip', hoverText);
      }
      if (stickyState) {
        const rawTime = (activeTrace && activeTrace.timeStr) ? activeTrace.timeStr : (step.state || '');
        const mTime = String(rawTime).match(/(\d+\s*(?:fs|ps|ns|us|ms|s))\b/i);
        stickyState.textContent = mTime ? mTime[1] : '0 ns';
        stickyState.style.display = 'inline-flex';
      }
      if (stickyBar) {
        stickyBar.classList.toggle('is-stepping', isSteppingMode);
      }

      if (stepActiveTitle) stepActiveTitle.textContent = step.title;
      if (stepActiveComp) stepActiveComp.textContent = `Target: ${step.component}`;
      if (stepActiveDesc) stepActiveDesc.textContent = step.desc;
      if (stepActiveLog) {
        const logHintBox = stepActiveLog.closest('.step-log-hint');
        if (step.log_snippet) {
          stepActiveLog.textContent = step.log_snippet;
          if (logHintBox) logHintBox.style.display = '';
        } else if (activeTrace && activeTrace.text) {
          stepActiveLog.textContent = activeTrace.text;
          if (logHintBox) logHintBox.style.display = '';
        } else {
          stepActiveLog.textContent = '(No console log emitted at this step)';
          if (logHintBox) logHintBox.style.display = '';
        }
      }

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
      if (stickyPrevMajorBtn) stickyPrevMajorBtn.disabled = idx === 0;
      if (stickyNextMajorBtn) stickyNextMajorBtn.disabled = idx === stepperSteps.length - 1;
      if (stickyPrevBtn) stickyPrevBtn.disabled = executionTrace.length ? currentTraceIdx === 0 : idx === 0;
      if (stickyNextBtn) stickyNextBtn.disabled = executionTrace.length ? currentTraceIdx >= executionTrace.length - 1 : idx === stepperSteps.length - 1;

      document.querySelectorAll('.code-step-marker').forEach(function (m) {
        const rawList = m.getAttribute('data-step-indices') || m.getAttribute('data-step-idx') || '';
        const list = rawList.split(',').map(function (s) { return parseInt(s, 10); });
        m.classList.toggle('active', list.indexOf(idx) !== -1);
      });

      // Topology card highlight
      document.querySelectorAll('.topo-card').forEach(function (card) {
        const text = card.textContent.toLowerCase();
        const compTarget = step.component.toLowerCase();
        const match = compTarget.split(/[,&]/).some(function (c) { return text.includes(c.trim()); });
        card.classList.toggle('highlighted', match);
      });

      // Synchronize with Code Studio (use fine-grained trace file/line if available)
      const targetFile = (activeTrace && activeTrace.file) ? activeTrace.file : step.highlight_file;
      const targetLine = (activeTrace && activeTrace.line) ? activeTrace.line : step.highlight_line;
      highlightCodeAt(targetFile, targetLine);

      // Synchronize with simulation log trace
      scrollToHighlightedLog(activeTrace ? activeTrace.termIdx : undefined);

      // Synchronize with visual concept animation
      updateScenarioAnimation(animType, idx, step);
    }

    function renderTraceStep(tIdx) {
      if (!executionTrace.length) {
        renderStep(tIdx);
        return;
      }
      if (tIdx < 0) tIdx = 0;
      if (tIdx >= executionTrace.length) tIdx = executionTrace.length - 1;
      currentTraceIdx = tIdx;
      const traceItem = executionTrace[tIdx];
      renderStep(traceItem.majorIdx, traceItem);
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

    function updatePlayButtons(isPlaying) {
      const label = isPlaying ? 'Pause ❚❚' : 'Play ▶';
      if (stepPlayBtn) stepPlayBtn.textContent = label;
      if (stickyPlayBtn) {
        stickyPlayBtn.innerHTML = isPlaying
          ? '<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>'
          : '<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 4 20 12 6 20 6 4"/></svg>';
        stickyPlayBtn.setAttribute('title', isPlaying ? 'Pause (Space)' : 'Play line-by-line (Space)');
      }
    }

    function stopAutoPlay() {
      if (playInterval) {
        clearInterval(playInterval);
        playInterval = null;
      }
      updatePlayButtons(false);
    }

    function startAutoPlay() {
      stopAutoPlay();
      isSteppingMode = true;
      const hasTrace = executionTrace.length > 0;
      if (hasTrace) {
        if (currentTraceIdx >= executionTrace.length - 1) {
          renderTraceStep(0);
        } else {
          renderTraceStep(currentTraceIdx);
        }
      } else {
        if (currentStepIdx >= stepperSteps.length - 1) {
          renderStep(0);
        } else {
          renderStep(currentStepIdx);
        }
      }
      updatePlayButtons(true);
      const baseDelay = hasTrace ? 1600 : 3800;
      const delayMs = Math.max(400, Math.round(baseDelay / playbackSpeed));
      playInterval = setInterval(function () {
        if (hasTrace) {
          if (currentTraceIdx >= executionTrace.length - 1) {
            stopAutoPlay();
          } else {
            renderTraceStep(currentTraceIdx + 1);
          }
        } else {
          if (currentStepIdx >= stepperSteps.length - 1) {
            stopAutoPlay();
          } else {
            renderStep(currentStepIdx + 1);
          }
        }
      }, delayMs);
    }

    function toggleAutoPlay() {
      if (playInterval) {
        stopAutoPlay();
      } else {
        startAutoPlay();
      }
    }

    function resetStepperMode() {
      stopAutoPlay();
      isSteppingMode = false;
      currentTraceIdx = 0;
      if (executionTrace.length > 0) {
        renderTraceStep(0);
      } else {
        renderStep(0);
      }
      clearConsoleSteppingClasses();
    }

    function setPlaybackSpeed(newSpeed) {
      const val = parseFloat(newSpeed);
      if (isNaN(val) || val <= 0) return;
      playbackSpeed = val;
      if (stepSpeedSelect) stepSpeedSelect.value = String(newSpeed);
      if (stickySpeedSelect) stickySpeedSelect.value = String(newSpeed);
      if (playInterval) {
        startAutoPlay();
      }
    }

    function goPrevMajorStep() {
      stopAutoPlay();
      isSteppingMode = true;
      renderStep(currentStepIdx - 1);
    }

    function goNextMajorStep() {
      stopAutoPlay();
      isSteppingMode = true;
      renderStep(currentStepIdx + 1);
    }

    function goPrevLine() {
      stopAutoPlay();
      isSteppingMode = true;
      if (executionTrace.length) {
        renderTraceStep(currentTraceIdx - 1);
      } else {
        renderStep(currentStepIdx - 1);
      }
    }

    function goNextLine() {
      stopAutoPlay();
      isSteppingMode = true;
      if (executionTrace.length) {
        renderTraceStep(currentTraceIdx + 1);
      } else {
        renderStep(currentStepIdx + 1);
      }
    }

    if (stepPrevBtn) stepPrevBtn.addEventListener('click', goPrevMajorStep);
    if (stickyPrevMajorBtn) stickyPrevMajorBtn.addEventListener('click', goPrevMajorStep);
    if (stepNextBtn) stepNextBtn.addEventListener('click', goNextMajorStep);
    if (stickyNextMajorBtn) stickyNextMajorBtn.addEventListener('click', goNextMajorStep);
    if (stickyPrevBtn) stickyPrevBtn.addEventListener('click', goPrevLine);
    if (stickyNextBtn) stickyNextBtn.addEventListener('click', goNextLine);
    if (stepResetBtn) stepResetBtn.addEventListener('click', resetStepperMode);
    if (stickyResetBtn) stickyResetBtn.addEventListener('click', resetStepperMode);
    if (stepSpeedSelect) {
      stepSpeedSelect.addEventListener('change', function () { setPlaybackSpeed(stepSpeedSelect.value); });
    }
    if (stickySpeedSelect) {
      stickySpeedSelect.addEventListener('change', function () { setPlaybackSpeed(stickySpeedSelect.value); });
    }

    if (btnJumpCode) {
      btnJumpCode.addEventListener('click', function () {
        isSteppingMode = true;
        scrollToHighlightedCode();
        if (studioCodeContainer) {
          studioCodeContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      });
    }

    if (btnJumpLog) {
      btnJumpLog.addEventListener('click', function () {
        isSteppingMode = true;
        const activeTrace = executionTrace[currentTraceIdx];
        scrollToHighlightedLog(activeTrace ? activeTrace.termIdx : undefined, true);
        if (terminalBody) {
          terminalBody.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      });
    }

    stepNodes.forEach(function (node, idx) {
      node.addEventListener('click', function () {
        stopAutoPlay();
        isSteppingMode = true;
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
          isSteppingMode = true;
          renderStep(nextIdx);
          if (stepNodes[nextIdx]) {
            stepNodes[nextIdx].focus();
          }
        }
      });
    }

    if (stepPlayBtn) stepPlayBtn.addEventListener('click', toggleAutoPlay);
    if (stickyPlayBtn) stickyPlayBtn.addEventListener('click', toggleAutoPlay);

    document.addEventListener('keydown', function (e) {
      if (!isSteppingMode) return;
      const tag = document.activeElement ? document.activeElement.tagName : '';
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      if (document.activeElement && document.activeElement.closest('.monaco-editor')) return;

      if (e.key === 'ArrowRight') {
        e.preventDefault();
        goNextLine();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        goPrevLine();
      } else if (e.key === ' ') {
        e.preventDefault();
        toggleAutoPlay();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        resetStepperMode();
      }
    });

    if (stickyBar) {
      try {
        if (window.parent && window.parent !== window) {
          const pSearchBar = window.parent.document.getElementById('search-nav-bar');
          if (pSearchBar && pSearchBar.style.display !== 'none') {
            stickyBar.classList.add('has-search-pilot');
          }
        }
      } catch (e) { }
      window.addEventListener('message', function (e) {
        if (e && e.data && e.data.type === 'searchNavBarVisibility') {
          stickyBar.classList.toggle('has-search-pilot', !!e.data.visible);
        }
      });
    }

    renderStep(0);
    clearConsoleSteppingClasses();
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
        const rawZip = zipPayloadEl.getAttribute('data-zip') || zipPayloadEl.textContent;
        const parsed = rawZip ? JSON.parse(rawZip) : null;
        if (Array.isArray(parsed)) {
          zipFiles = parsed;
          fileNames = parsed.map(f => f && f.name).filter(Boolean);
        }
      } catch (e) { }
    }
    if (!fileNames.length) {
      fileNames = Array.from(document.querySelectorAll('.file-code-pane[data-filename]'))
        .map(p => (p.getAttribute('data-filename') || '').trim())
        .filter(Boolean);
    }
    if (!fileNames.length) {
      fileNames = Array.from(document.querySelectorAll('.studio-tab')).map(t => {
        const nameEl = t.querySelector('.tab-name');
        return (nameEl ? nameEl.textContent : (t.getAttribute('title') || t.textContent)).trim();
      }).filter(Boolean);
    }
    if (!fileNames.length) return;

    filesBadge.dataset.popoverBound = '1';
    filesBadge.classList.add('is-interactive');
    filesBadge.setAttribute('role', 'button');
    filesBadge.setAttribute('tabindex', '0');
    filesBadge.setAttribute('aria-expanded', 'false');

    function getExampleSrcUrl(name) {
      const p = window.location.pathname.replace(/\\/g, '/');
      const mEx = p.match(/examples_view\/(.+?)\.html$/);
      if (mEx && name) {
        return `src_view/examples/${mEx[1]}/${name}.html`;
      }
      const mTut = p.match(/tutorial_view\/(.+?)\.html$/);
      if (mTut && name) {
        return `src_view/tutorial/${mTut[1]}/${name}.html`;
      }
      return '';
    }

    function postExampleFileToParent(msgType, name) {
      if (!(window.parent && window.parent !== window)) return false;
      const srcUrl = getExampleSrcUrl(name);
      if (!srcUrl) return false;
      window.parent.postMessage({ type: msgType, url: srcUrl }, '*');
      return true;
    }

    if (window.parent && window.parent !== window) {
      document.querySelectorAll('.studio-tab').forEach((tab, idx) => {
        tab.addEventListener('click', () => {
          const nameEl = tab.querySelector('.tab-name');
          const name = tab.getAttribute('data-filename') || (nameEl ? nameEl.textContent.trim() : '') || tab.getAttribute('title') || fileNames[idx];
          postExampleFileToParent('studioFileChanged', name);
        });
      });
      const studioSelect = document.getElementById('studio-file-select');
      if (studioSelect) {
        studioSelect.addEventListener('change', () => {
          const idx = parseInt(studioSelect.value, 10);
          if (!isNaN(idx) && fileNames[idx]) {
            postExampleFileToParent('studioFileChanged', fileNames[idx]);
          }
        });
      }
    }
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
          if (!postExampleFileToParent('openSourceView', name)) {
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
