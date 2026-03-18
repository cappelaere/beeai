(function() {
  const promptInput = document.getElementById('prompt-input');
  
  if (!promptInput) return;

  const HISTORY_KEY = 'realtyiq-prompt-history';
  const MAX_HISTORY = 50;
  
  let history = [];
  let historyIndex = -1;
  let currentDraft = '';

  // Load history from localStorage
  function loadHistory() {
    try {
      const stored = localStorage.getItem(HISTORY_KEY);
      if (stored) {
        history = JSON.parse(stored);
      }
    } catch (err) {
      console.error('Failed to load prompt history:', err);
      history = [];
    }
  }

  // Save history to localStorage
  function saveHistory() {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch (err) {
      console.error('Failed to save prompt history:', err);
    }
  }

  // Add a prompt to history
  function addToHistory(prompt) {
    if (!prompt || !prompt.trim()) return;
    
    // Remove duplicate if exists
    const index = history.indexOf(prompt);
    if (index !== -1) {
      history.splice(index, 1);
    }
    
    // Add to beginning
    history.unshift(prompt);
    
    // Limit size
    if (history.length > MAX_HISTORY) {
      history = history.slice(0, MAX_HISTORY);
    }
    
    saveHistory();
    historyIndex = -1;
    currentDraft = '';
  }

  // Navigate history
  function navigateHistory(direction) {
    if (history.length === 0) return;
    
    // Save current input as draft when starting to navigate
    if (historyIndex === -1 && direction === 'up') {
      currentDraft = promptInput.value;
    }
    
    if (direction === 'up') {
      if (historyIndex < history.length - 1) {
        historyIndex++;
        promptInput.value = history[historyIndex];
      }
    } else if (direction === 'down') {
      if (historyIndex > 0) {
        historyIndex--;
        promptInput.value = history[historyIndex];
      } else if (historyIndex === 0) {
        historyIndex = -1;
        promptInput.value = currentDraft;
      }
    }
  }

  // Handle arrow keys
  promptInput.addEventListener('keydown', function(e) {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      navigateHistory('up');
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      navigateHistory('down');
    } else if (e.key === 'Escape') {
      // Reset to draft on escape
      historyIndex = -1;
      promptInput.value = currentDraft;
    } else {
      // Any other key resets history navigation
      if (historyIndex !== -1 && e.key !== 'Enter') {
        historyIndex = -1;
        currentDraft = '';
      }
    }
  });

  // Listen for form submission to capture prompt
  const chatForm = document.getElementById('chat-form');
  if (chatForm) {
    chatForm.addEventListener('submit', function() {
      const prompt = promptInput.value.trim();
      if (prompt) {
        addToHistory(prompt);
      }
    });
  }

  // Initialize
  loadHistory();

  // Expose API for programmatic additions (e.g., from card clicks)
  window.RealtyIQPromptHistory = {
    add: addToHistory,
    clear: function() {
      history = [];
      historyIndex = -1;
      currentDraft = '';
      saveHistory();
    },
    getHistory: function() {
      return history.slice();
    }
  };
})();
