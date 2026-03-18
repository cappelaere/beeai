(function() {
  const nav = document.getElementById('sidebar-nav');
  const resizer = document.getElementById('nav-resizer');
  
  if (!nav || !resizer) return;

  let isResizing = false;
  let startX = 0;
  let startWidth = 0;

  function startResize(e) {
    isResizing = true;
    startX = e.clientX;
    startWidth = nav.offsetWidth;
    
    resizer.classList.add('resizing');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    
    e.preventDefault();
  }

  function resize(e) {
    if (!isResizing) return;
    
    const delta = e.clientX - startX;
    const newWidth = startWidth + delta;
    
    // Apply min/max constraints
    const minWidth = 160; // 10rem
    const maxWidth = 400; // 25rem
    
    if (newWidth >= minWidth && newWidth <= maxWidth) {
      nav.style.width = newWidth + 'px';
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
