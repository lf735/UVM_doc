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
})(window);

