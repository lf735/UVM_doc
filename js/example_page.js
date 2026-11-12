/**
 * UVM 1.2 Interactive Example Studio Controller
 * Powered by Universal Page Controller (js/page_common.js).
 *
 * Capabilities:
 * - Multi-File Code Studio (studioCodeContainer.scrollTo, studio-file-select, studio-tab-scroll-left) in js/page_common.js
 * - Zero-Dependency Native Client-Side ZIP Generator (crc32, createNativeZipBlob, initZipDownload) in this file
 * - Simulation Console & Log Filters (initSimulationConsole) in this file
 * - Interactive Visual Flow Stepper in js/page_common.js
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

  function initExampleFeatures() {
    initZipDownload();
    initSimulationConsole();
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
    initSimulationConsole: initSimulationConsole
  };
})(window);
