/**
 * UVM 1.2 Interactive Documentation - Image Zoom Lightbox Modal Controller
 * Exposed via window.UvmImageModal (and window.openImageZoomModal / window.closeImageZoomModal).
 * Offline file:// compatible (classic IIFE).
 */
(function (global) {
  'use strict';

  function initImageModal() {
    const imageZoomModal = document.getElementById('image-zoom-modal');
    const imageModalTitle = document.getElementById('image-modal-title');
    const imageModalImg = document.getElementById('image-modal-img');
    const imageModalViewport = document.getElementById('image-modal-viewport');
    const imageModalStage = document.getElementById('image-modal-stage');
    const imageZoomLevel = document.getElementById('image-zoom-level');
    const imageZoomInBtn = document.getElementById('image-zoom-in');
    const imageZoomOutBtn = document.getElementById('image-zoom-out');
    const imageZoomFitBtn = document.getElementById('image-zoom-fit');
    const imageZoomActualBtn = document.getElementById('image-zoom-actual');
    const imageModalCloseBtn = document.getElementById('image-modal-close');

    let currentZoom = 1.0;
    let fitZoom = 1.0;
    let panX = 0;
    let panY = 0;
    let isPanning = false;
    let panStartX = 0;
    let panStartY = 0;

    function updateImageTransform() {
      if (!imageModalStage) return;
      imageModalStage.style.transform = `translate(${panX}px, ${panY}px) scale(${currentZoom})`;
      if (imageZoomLevel) {
        imageZoomLevel.textContent = `${Math.round(currentZoom * 100)}%`;
      }
    }

    function setZoom(newZoom, centerX = null, centerY = null) {
      const clamped = Math.max(0.2, Math.min(5.0, newZoom));
      if (centerX !== null && centerY !== null && imageModalViewport) {
        const rect = imageModalViewport.getBoundingClientRect();
        const vx = centerX - rect.left - rect.width / 2;
        const vy = centerY - rect.top - rect.height / 2;
        const ratio = clamped / currentZoom;
        panX = vx - (vx - panX) * ratio;
        panY = vy - (vy - panY) * ratio;
      }
      currentZoom = clamped;
      updateImageTransform();
    }

    function fitImageToViewport() {
      if (!imageModalImg || !imageModalViewport) return;
      const naturalW = imageModalImg.naturalWidth || 600;
      const naturalH = imageModalImg.naturalHeight || 400;
      const vpW = imageModalViewport.clientWidth || 800;
      const vpH = imageModalViewport.clientHeight || 600;

      const availW = Math.max(100, vpW - 80);
      const availH = Math.max(100, vpH - 80);

      const scaleX = availW / naturalW;
      const scaleY = availH / naturalH;
      let targetScale = Math.min(scaleX, scaleY);
      if (targetScale > 1.5) targetScale = 1.5;
      if (targetScale < 0.25) targetScale = 0.25;

      fitZoom = targetScale;
      currentZoom = targetScale;
      panX = 0;
      panY = 0;
      updateImageTransform();
    }

    function resetActualZoom() {
      currentZoom = 1.0;
      panX = 0;
      panY = 0;
      updateImageTransform();
    }

    function openImageZoomModal(src, title) {
      if (!imageZoomModal || !imageModalImg) return;
      const diagramTitle = title || 'UVM Diagram';
      if (imageModalTitle) {
        imageModalTitle.textContent = diagramTitle;
      }
      const modalCaption = document.getElementById('image-modal-caption');
      if (modalCaption) {
        modalCaption.textContent = diagramTitle;
      }
      imageModalImg.src = src;
      imageModalImg.onload = () => {
        fitImageToViewport();
      };
      if (imageModalImg.complete) {
        fitImageToViewport();
      }
      imageZoomModal.style.display = 'flex';
      imageZoomModal.style.pointerEvents = 'auto';
      void imageZoomModal.offsetWidth;
      imageZoomModal.classList.add('open');
      imageZoomModal.setAttribute('aria-hidden', 'false');
    }

    function closeImageZoomModal() {
      if (!imageZoomModal) return;
      imageZoomModal.classList.remove('open');
      imageZoomModal.setAttribute('aria-hidden', 'true');
      imageZoomModal.style.pointerEvents = 'none';
      imageZoomModal.style.display = 'none';
      isPanning = false;
      if (imageModalViewport) {
        imageModalViewport.classList.remove('is-dragging');
      }
      if (document.activeElement && imageZoomModal.contains(document.activeElement)) {
        document.activeElement.blur();
      }
      if (imageModalImg) {
        imageModalImg.src = '';
      }
    }

    function handleKeydown(e) {
      if (!imageZoomModal || !imageZoomModal.classList.contains('open')) return false;
      if (e.key === 'Escape') {
        e.preventDefault();
        closeImageZoomModal();
        return true;
      }
      if (e.key === '+' || e.key === '=') {
        e.preventDefault();
        setZoom(currentZoom * 1.25);
        return true;
      }
      if (e.key === '-' || e.key === '_') {
        e.preventDefault();
        setZoom(currentZoom * 0.8);
        return true;
      }
      if (e.key === '0') {
        e.preventDefault();
        fitImageToViewport();
        return true;
      }
      if (e.key === '1') {
        e.preventDefault();
        resetActualZoom();
        return true;
      }
      return false;
    }

    if (imageZoomInBtn) {
      imageZoomInBtn.addEventListener('click', () => setZoom(currentZoom * 1.25));
    }
    if (imageZoomOutBtn) {
      imageZoomOutBtn.addEventListener('click', () => setZoom(currentZoom * 0.8));
    }
    if (imageZoomFitBtn) {
      imageZoomFitBtn.addEventListener('click', () => fitImageToViewport());
    }
    if (imageZoomActualBtn) {
      imageZoomActualBtn.addEventListener('click', resetActualZoom);
    }
    if (imageModalCloseBtn) {
      imageModalCloseBtn.addEventListener('click', closeImageZoomModal);
    }
    if (imageZoomModal) {
      imageZoomModal.addEventListener('click', (e) => {
        if (e.target === imageZoomModal) {
          closeImageZoomModal();
        }
      });
    }

    if (imageModalViewport) {
      imageModalViewport.addEventListener('wheel', (e) => {
        e.preventDefault();
        const factor = e.deltaY < 0 ? 1.15 : 0.87;
        setZoom(currentZoom * factor, e.clientX, e.clientY);
      }, { passive: false });

      imageModalViewport.addEventListener('mousedown', (e) => {
        if (e.target.closest('.image-modal-toolbar') || e.target.closest('.image-modal-header')) return;
        isPanning = true;
        panStartX = e.clientX - panX;
        panStartY = e.clientY - panY;
        imageModalViewport.classList.add('is-dragging');
      });

      window.addEventListener('mousemove', (e) => {
        if (!isPanning) return;
        panX = e.clientX - panStartX;
        panY = e.clientY - panStartY;
        updateImageTransform();
      });

      window.addEventListener('mouseup', () => {
        if (isPanning) {
          isPanning = false;
          if (imageModalViewport) {
            imageModalViewport.classList.remove('is-dragging');
          }
        }
      });

      imageModalViewport.addEventListener('dblclick', (e) => {
        if (e.target.closest('.image-modal-toolbar') || e.target.closest('.image-modal-header')) return;
        if (Math.abs(currentZoom - fitZoom) < 0.1 || currentZoom <= 1.1) {
          setZoom(2.0, e.clientX, e.clientY);
        } else {
          fitImageToViewport();
        }
      });
    }

    global.openImageZoomModal = openImageZoomModal;
    global.closeImageZoomModal = closeImageZoomModal;

    return {
      open: openImageZoomModal,
      close: closeImageZoomModal,
      handleKeydown: handleKeydown
    };
  }

  global.UvmImageModal = {
    init: initImageModal
  };

  function initSearchModals(options) {
    const opts = options || {};
    const escapeHtml = (global.UvmAppUtils && global.UvmAppUtils.escapeHtml) || (s => String(s || ''));
    const aiConsentModal = document.getElementById('ai-consent-modal');
    const aiConsentModelList = document.getElementById('ai-consent-model-list');
    const aiConsentConfirm = document.getElementById('ai-consent-confirm');
    const searchSettingsModal = document.getElementById('search-settings-modal');
    const settingsModelList = document.getElementById('settings-model-list');
    const settingsCacheStatus = document.getElementById('settings-cache-status');
    const settingsToggleHybrid = document.getElementById('settings-toggle-hybrid');
    const settingsToggleAutoSemantic = document.getElementById('settings-toggle-auto-semantic');
    const settingsModeConsolidated = document.getElementById('settings-mode-consolidated');
    const settingsModeMixed = document.getElementById('settings-mode-mixed');
    const searchSettingsDone = document.getElementById('search-settings-done');
    const searchInput = document.getElementById('modal-search-input');

    function renderStarRating(rating) {
      let stars = '';
      for (let i = 1; i <= 5; i++) {
        stars += i <= rating ? '★' : '☆';
      }
      return stars;
    }

    function renderAiModelList(container, isConsent) {
      if (!container || !global.UVMRagEngine) return;
      const models = global.UVMRagEngine.models || [];
      const currentId = global.UVMRagEngine.currentModelId;
      let html = '';

      models.forEach(m => {
        const isSelected = m.id === currentId;
        const recBadge = m.recommended ? `<span class="ai-badge-rec">Recommended</span>` : '';
        const radioName = isConsent ? 'consent-model-radio' : 'settings-model-radio';
        html += `
            <label class="ai-model-card ${isSelected ? 'selected' : ''}" data-model-id="${m.id}" tabindex="0" role="radio" aria-checked="${isSelected}">
              <input type="radio" name="${radioName}" value="${m.id}" class="ai-model-radio" ${isSelected ? 'checked' : ''}>
              <div class="ai-model-info">
                <div class="ai-model-header">
                  <span class="ai-model-name">${escapeHtml(m.name)}</span>
                  ${recBadge}
                </div>
                <div class="ai-model-desc">${escapeHtml(m.description)}</div>
                <div class="ai-model-metrics">
                  <span class="ai-metric-item"><strong>Speed:</strong> <span class="ai-stars">${renderStarRating(m.speedRating)}</span></span>
                  <span class="ai-metric-item"><strong>Accuracy:</strong> <span class="ai-stars">${renderStarRating(m.accuracyRating)}</span></span>
                  <span class="ai-metric-item"><strong>Size:</strong> ${escapeHtml(m.downloadSize)} (${escapeHtml(m.ramUsage)})</span>
                </div>
              </div>
            </label>
          `;
      });

      container.innerHTML = html;

      container.querySelectorAll('.ai-model-card').forEach(card => {
        const selectCard = () => {
          container.querySelectorAll('.ai-model-card').forEach(c => {
            c.classList.remove('selected');
            c.setAttribute('aria-checked', 'false');
          });
          card.classList.add('selected');
          card.setAttribute('aria-checked', 'true');
          const radio = card.querySelector('input[type="radio"]');
          if (radio) radio.checked = true;
          const modelId = card.getAttribute('data-model-id');
          global.UVMRagEngine.setModel(modelId);
          if (opts.onModelChange) opts.onModelChange(modelId);
        };

        card.addEventListener('click', selectCard);
        card.addEventListener('keydown', (e) => {
          if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            selectCard();
          }
        });
      });
    }

    function updateCacheStatusUI() {
      if (!settingsCacheStatus || !global.UVMRagEngine) return;
      global.UVMRagEngine.getCacheInfo().then(({ count, sizeMB }) => {
        if (settingsCacheStatus) {
          settingsCacheStatus.textContent = sizeMB > 0
            ? `Cached models storage: ~${sizeMB} MB (${count} files cached)`
            : 'No cached models';
        }
      }).catch(() => {
        if (settingsCacheStatus) settingsCacheStatus.textContent = 'Cache status unavailable';
      });
    }

    function openAiConsentModal() {
      if (!aiConsentModal) return;
      renderAiModelList(aiConsentModelList, true);
      aiConsentModal.style.display = 'flex';
      if (aiConsentConfirm) aiConsentConfirm.focus();
    }

    function closeAiConsentModal() {
      if (!aiConsentModal) return;
      aiConsentModal.style.display = 'none';
      if (searchInput) searchInput.focus();
    }

    function openSearchSettingsModal() {
      if (!searchSettingsModal) return;
      renderAiModelList(settingsModelList, false);
      if (settingsToggleHybrid && global.UVMRagEngine) {
        settingsToggleHybrid.checked = global.UVMRagEngine.isHybrid;
      }
      if (settingsToggleAutoSemantic && global.UVMRagEngine) {
        settingsToggleAutoSemantic.checked = global.UVMRagEngine.isAutoSemantic;
      }
      if (global.UVMRagEngine) {
        const mode = global.UVMRagEngine.displayMode;
        if (settingsModeConsolidated) settingsModeConsolidated.checked = (mode !== 'mixed');
        if (settingsModeMixed) settingsModeMixed.checked = (mode === 'mixed');
      }
      updateCacheStatusUI();
      searchSettingsModal.style.display = 'flex';
      if (searchSettingsDone) searchSettingsDone.focus();
    }

    function closeSearchSettingsModal() {
      if (!searchSettingsModal) return;
      searchSettingsModal.style.display = 'none';
      if (searchInput) searchInput.focus();
    }

    return {
      updateCacheStatusUI: updateCacheStatusUI,
      openAiConsentModal: openAiConsentModal,
      closeAiConsentModal: closeAiConsentModal,
      openSearchSettingsModal: openSearchSettingsModal,
      closeSearchSettingsModal: closeSearchSettingsModal
    };
  }

  global.UvmSearchModals = {
    init: initSearchModals
  };
})(window);

