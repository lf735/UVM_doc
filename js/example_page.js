/**
 * UVM 1.2 Interactive Example Studio Controller
 * Powers the multi-file Code Studio, native client-side ZIP generator,
 * simulation console, Visual Flow Stepper, and bidirectional parent communication.
 * Zero external runtime dependencies - 100% offline file:// compatible.
 */

(function initExampleStudio() {
  // Elements
  const studioTabBar = document.getElementById('studio-tab-bar');
  const studioTabs = document.querySelectorAll('.studio-tab');
  const codePanes = document.querySelectorAll('.file-code-pane');
  const studioFileInfo = document.getElementById('studio-file-info');
  const btnCopyCode = document.getElementById('btn-copy-code');
  const btnCopyCodeText = document.getElementById('btn-copy-code-text');
  const btnDownloadRaw = document.getElementById('btn-download-raw');
  const btnDownloadZip = document.getElementById('btn-download-zip');
  const btnSplitSource = document.getElementById('btn-split-source');

  // Simulation Console Elements
  const simTabs = document.querySelectorAll('.sim-tab');
  const simCmdText = document.getElementById('sim-cmd-text');
  const btnCopyCmd = document.getElementById('btn-copy-cmd');
  const termFilters = document.querySelectorAll('.term-filter');
  const terminalBody = document.getElementById('terminal-body');

  // Stepper Elements
  const stepperSection = document.getElementById('visual-flow-stepper');
  const stepperTimeline = document.getElementById('stepper-timeline');
  const stepNodes = document.querySelectorAll('.step-node');
  const stepPrevBtn = document.getElementById('stepper-prev');
  const stepNextBtn = document.getElementById('stepper-next');
  const stepPlayBtn = document.getElementById('stepper-play');
  const stepActiveTitle = document.getElementById('step-active-title');
  const stepActiveComp = document.getElementById('step-active-comp');
  const stepActiveDesc = document.getElementById('step-active-desc');
  const stepActiveLog = document.getElementById('step-active-log');

  // Raw Zip payload & Stepper payload
  const zipPayloadEl = document.getElementById('zip-payload');
  const stepperPayloadEl = document.getElementById('stepper-payload');

  let filesList = [];
  try {
    if (zipPayloadEl && zipPayloadEl.getAttribute('data-zip')) {
      filesList = JSON.parse(zipPayloadEl.getAttribute('data-zip'));
    }
  } catch (e) {
    console.warn('Could not parse zip payload', e);
  }

  let stepperSteps = [];
  try {
    if (stepperPayloadEl && stepperPayloadEl.getAttribute('data-stepper')) {
      stepperSteps = JSON.parse(stepperPayloadEl.getAttribute('data-stepper'));
    }
  } catch (e) {
    console.warn('Could not parse stepper payload', e);
  }

  let currentFileIdx = 0;
  let currentStepIdx = 0;
  let playInterval = null;
  const rawLogContent = terminalBody ? terminalBody.textContent : '';

  // =========================================================================
  // 1. Multi-File Code Studio Tabs
  // =========================================================================

  function switchFileTab(idx) {
    if (idx < 0 || idx >= studioTabs.length) return;
    currentFileIdx = idx;

    studioTabs.forEach((tab, i) => {
      tab.classList.toggle('active', i === idx);
    });

    codePanes.forEach((pane, i) => {
      pane.classList.toggle('active', i === idx);
    });

    if (filesList[idx] && studioFileInfo) {
      const lineCount = (filesList[idx].content.match(/\n/g) || []).length + 1;
      const sizeKb = (new TextEncoder().encode(filesList[idx].content).length / 1024).toFixed(1);
      studioFileInfo.textContent = `${filesList[idx].name} (${lineCount} lines, ${sizeKb} KB)`;
    }
  }

  studioTabs.forEach((tab, idx) => {
    tab.addEventListener('click', () => switchFileTab(idx));
  });

  // Copy Active File Code
  if (btnCopyCode) {
    btnCopyCode.addEventListener('click', () => {
      const curFile = filesList[currentFileIdx];
      if (!curFile) return;

      navigator.clipboard.writeText(curFile.content).then(() => {
        if (btnCopyCodeText) btnCopyCodeText.textContent = 'Copied!';
        btnCopyCode.classList.add('btn-copied');
        setTimeout(() => {
          if (btnCopyCodeText) btnCopyCodeText.textContent = 'Copy Code';
          btnCopyCode.classList.remove('btn-copied');
        }, 2000);
      }).catch(err => {
        console.error('Copy failed:', err);
      });
    });
  }

  // Download Active Raw File
  if (btnDownloadRaw) {
    btnDownloadRaw.addEventListener('click', () => {
      const curFile = filesList[currentFileIdx];
      if (!curFile) return;

      const blob = new Blob([curFile.content], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = curFile.name.split('/').pop();
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  // =========================================================================
  // 2. Native Pure Client-Side ZIP Generator (Zero Runtime Dependencies)
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

      fileEntries.push({
        offset,
        nameBytes,
        dataBytes,
        crc,
        length: dataBytes.length
      });

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

  if (btnDownloadZip) {
    btnDownloadZip.addEventListener('click', () => {
      if (!filesList || filesList.length === 0) return;
      const zipBlob = createNativeZipBlob(filesList);
      const url = URL.createObjectURL(zipBlob);
      const a = document.createElement('a');
      const pageTitle = (document.title.split('|')[0] || 'uvm_example').trim().toLowerCase().replace(/[^a-z0-9_]/g, '_');
      a.href = url;
      a.download = `${pageTitle}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  // =========================================================================
  // 3. Simulator Commands & Console Log Filtering
  // =========================================================================

  const SIM_COMMANDS = {
    questa: 'make -f Makefile.questa run',
    vcs: 'make -f Makefile.vcs run',
    xcelium: 'make -f Makefile.ius run'
  };

  simTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      simTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const sim = tab.getAttribute('data-sim');
      if (simCmdText && SIM_COMMANDS[sim]) {
        simCmdText.textContent = SIM_COMMANDS[sim];
      }
    });
  });

  if (btnCopyCmd && simCmdText) {
    btnCopyCmd.addEventListener('click', () => {
      navigator.clipboard.writeText(simCmdText.textContent).then(() => {
        btnCopyCmd.textContent = 'Copied!';
        setTimeout(() => { btnCopyCmd.textContent = 'Copy'; }, 2000);
      });
    });
  }

  termFilters.forEach(btn => {
    btn.addEventListener('click', () => {
      termFilters.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const level = btn.getAttribute('data-level');
      if (!terminalBody) return;

      if (level === 'all') {
        terminalBody.textContent = rawLogContent;
      } else if (level === 'info') {
        const filtered = rawLogContent.split('\n').filter(l => l.includes('UVM_INFO') || l.includes('---') || l.includes('Report counts') || l.includes('PASSED'));
        terminalBody.textContent = filtered.join('\n');
      } else if (level === 'warning') {
        const filtered = rawLogContent.split('\n').filter(l => l.includes('UVM_WARNING') || l.includes('---'));
        terminalBody.textContent = filtered.join('\n');
      } else if (level === 'error') {
        const filtered = rawLogContent.split('\n').filter(l => l.includes('UVM_ERROR') || l.includes('UVM_FATAL') || l.includes('---'));
        terminalBody.textContent = filtered.join('\n');
      }
    });
  });

  // =========================================================================
  // 4. Interactive Visual Flow Stepper
  // =========================================================================

  function renderStep(idx) {
    if (!stepperSteps || stepperSteps.length === 0) return;
    if (idx < 0) idx = 0;
    if (idx >= stepperSteps.length) idx = stepperSteps.length - 1;
    currentStepIdx = idx;

    const step = stepperSteps[idx];

    // Update timeline nodes
    stepNodes.forEach((node, i) => {
      node.classList.toggle('active', i === idx);
      node.classList.toggle('completed', i < idx);
    });

    // Update step card
    if (stepActiveTitle) stepActiveTitle.textContent = step.title;
    if (stepActiveComp) stepActiveComp.textContent = `Target: ${step.component}`;
    if (stepActiveDesc) stepActiveDesc.textContent = step.desc;
    if (stepActiveLog) stepActiveLog.textContent = step.log_snippet;

    // Controls state
    if (stepPrevBtn) stepPrevBtn.disabled = idx === 0;
    if (stepNextBtn) stepNextBtn.disabled = idx === stepperSteps.length - 1;

    // Highlight matching component in topology
    document.querySelectorAll('.topo-card').forEach(card => {
      const text = card.textContent.toLowerCase();
      const compTarget = step.component.toLowerCase();
      const match = compTarget.split(/[,&]/).some(c => text.includes(c.trim()));
      card.classList.toggle('highlighted', match);
    });

    // Highlight matching file and line in code studio
    if (step.highlight_file) {
      const fileIndex = filesList.findIndex(f => f.name.includes(step.highlight_file));
      if (fileIndex !== -1 && fileIndex !== currentFileIdx) {
        switchFileTab(fileIndex);
      }
      if (step.highlight_line) {
        const targetRow = document.querySelector(`#file-pane-${currentFileIdx} #L${step.highlight_line}`);
        if (targetRow) {
          document.querySelectorAll('.file-code-pane tr.stepper-highlight').forEach(tr => tr.classList.remove('stepper-highlight'));
          targetRow.classList.add('stepper-highlight');
          targetRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    }
  }

  if (stepPrevBtn) {
    stepPrevBtn.addEventListener('click', () => {
      stopAutoPlay();
      renderStep(currentStepIdx - 1);
    });
  }

  if (stepNextBtn) {
    stepNextBtn.addEventListener('click', () => {
      stopAutoPlay();
      renderStep(currentStepIdx + 1);
    });
  }

  stepNodes.forEach((node, idx) => {
    node.addEventListener('click', () => {
      stopAutoPlay();
      renderStep(idx);
    });
  });

  function stopAutoPlay() {
    if (playInterval) {
      clearInterval(playInterval);
      playInterval = null;
      if (stepPlayBtn) stepPlayBtn.textContent = 'Play ▶';
    }
  }

  if (stepPlayBtn) {
    stepPlayBtn.addEventListener('click', () => {
      if (playInterval) {
        stopAutoPlay();
      } else {
        stepPlayBtn.textContent = 'Pause ❚❚';
        playInterval = setInterval(() => {
          if (currentStepIdx >= stepperSteps.length - 1) {
            renderStep(0);
          } else {
            renderStep(currentStepIdx + 1);
          }
        }, 2500);
      }
    });
  }

  // =========================================================================
  // 5. Symbol Linking & Bidirectional Parent Communication
  // =========================================================================

  // Click on UVM class badges or code references
  document.addEventListener('click', (e) => {
    const symEl = e.target.closest('.clickable-uvm-sym');
    if (symEl) {
      e.preventDefault();
      const sym = symEl.getAttribute('data-sym') || symEl.textContent.trim();
      if (sym && window.parent && window.parent !== window) {
        window.parent.postMessage({
          type: 'openDocView',
          symbol: sym,
          url: `docs_view/base/${sym}-svh.html`
        }, '*');
      }
    }
  });

  // Split View button
  if (btnSplitSource) {
    btnSplitSource.addEventListener('click', () => {
      if (window.parent && window.parent !== window) {
        window.parent.postMessage({
          type: 'openSourceView',
          url: 'src_view/comps/uvm_component.svh.html#L44'
        }, '*');
      }
    });
  }

  // Theme synchronization from parent
  window.addEventListener('message', (e) => {
    if (!e.data || typeof e.data !== 'object') return;
    if (e.data.theme) {
      document.documentElement.setAttribute('data-theme', e.data.theme);
    }
  });

  // Notify parent of current page navigation
  if (window.parent && window.parent !== window) {
    window.parent.postMessage({
      type: 'exampleNavigated',
      url: window.location.pathname,
      title: document.title
    }, '*');
  }

  // Initialize stepper if present
  if (stepperSteps && stepperSteps.length > 0) {
    renderStep(0);
  }
})();

