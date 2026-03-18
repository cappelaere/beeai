(function() {
  const panel = document.getElementById('favorite-cards-panel');
  const resizer = document.getElementById('panel-resizer');
  
  if (!panel || !resizer) return;

  let isResizing = false;
  let startY = 0;
  let startHeight = 0;

  function startResize(e) {
    isResizing = true;
    startY = e.clientY;
    startHeight = panel.offsetHeight;
    
    resizer.classList.add('resizing');
    document.body.style.cursor = 'row-resize';
    document.body.style.userSelect = 'none';
    
    e.preventDefault();
  }

  function resize(e) {
    if (!isResizing) return;
    
    const delta = e.clientY - startY;
    const newHeight = startHeight + delta;
    
    // Apply min/max constraints
    const minHeight = 128; // 8rem
    const maxHeight = 480; // 30rem
    
    if (newHeight >= minHeight && newHeight <= maxHeight) {
      panel.style.height = newHeight + 'px';
      panel.style.maxHeight = newHeight + 'px';
    }
  }

  function stopResize() {
    if (!isResizing) return;
    
    isResizing = false;
    resizer.classList.remove('resizing');
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }

  resizer.addEventListener('mousedown', startResize);
  document.addEventListener('mousemove', resize);
  document.addEventListener('mouseup', stopResize);
})();
