/**
 * Autocomplete for prompt suggestions
 */
(function () {
  "use strict";

  var promptInput = null;
  var autocompleteList = null;
  var currentSuggestions = [];
  var selectedIndex = -1;
  var debounceTimer = null;

  function init() {
    promptInput = document.getElementById("prompt-input");
    if (!promptInput) {
      console.log("Autocomplete: prompt-input element not found");
      return;
    }
    
    console.log("Autocomplete: initialized on prompt-input");

    // Create autocomplete dropdown
    createAutocompleteDropdown();

    // Attach event listeners
    promptInput.addEventListener("input", onInput);
    promptInput.addEventListener("keydown", onKeyDown);
    promptInput.addEventListener("focus", onFocus);
    
    // Close dropdown when clicking outside
    document.addEventListener("click", function (e) {
      if (e.target !== promptInput && !autocompleteList.contains(e.target)) {
        hideAutocomplete();
      }
    });
  }

  function createAutocompleteDropdown() {
    autocompleteList = document.createElement("div");
    autocompleteList.className = "autocomplete-dropdown";
    autocompleteList.style.display = "none";
    
    // Insert after prompt input
    var inputWrapper = promptInput.closest(".input-wrapper") || promptInput.parentElement;
    inputWrapper.style.position = "relative";
    inputWrapper.appendChild(autocompleteList);
  }

  function onInput(e) {
    var query = e.target.value.trim();
    
    // Clear previous timer
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    
    // Don't show suggestions for very short queries
    if (query.length < 2) {
      hideAutocomplete();
      return;
    }
    
    // Debounce API call
    debounceTimer = setTimeout(function () {
      fetchSuggestions(query);
    }, 200);
  }

  function onFocus(e) {
    var query = e.target.value.trim();
    if (query.length >= 2) {
      fetchSuggestions(query);
    }
  }

  function onKeyDown(e) {
    if (autocompleteList.style.display === "none") return;
    
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        moveSelection(1);
        break;
      case "ArrowUp":
        e.preventDefault();
        moveSelection(-1);
        break;
      case "Enter":
        if (selectedIndex >= 0 && selectedIndex < currentSuggestions.length) {
          e.preventDefault();
          selectSuggestion(currentSuggestions[selectedIndex]);
        }
        break;
      case "Escape":
        e.preventDefault();
        hideAutocomplete();
        break;
    }
  }

  function moveSelection(delta) {
    var items = autocompleteList.querySelectorAll(".autocomplete-item");
    if (items.length === 0) return;
    
    // Remove previous selection
    if (selectedIndex >= 0 && selectedIndex < items.length) {
      items[selectedIndex].classList.remove("selected");
    }
    
    // Update index
    selectedIndex += delta;
    if (selectedIndex < 0) selectedIndex = items.length - 1;
    if (selectedIndex >= items.length) selectedIndex = 0;
    
    // Add new selection
    items[selectedIndex].classList.add("selected");
    items[selectedIndex].scrollIntoView({ block: "nearest" });
  }

  function fetchSuggestions(query) {
    var apiUrl = "/api/prompt-suggestions/?q=" + encodeURIComponent(query) + "&limit=8";
    
    console.log("Autocomplete: fetching suggestions for:", query);
    
    fetch(apiUrl)
      .then(function (response) { return response.json(); })
      .then(function (data) {
        currentSuggestions = data.suggestions || [];
        console.log("Autocomplete: received", currentSuggestions.length, "suggestions");
        renderSuggestions(currentSuggestions);
      })
      .catch(function (err) {
        console.error("Autocomplete: failed to fetch suggestions:", err);
      });
  }

  function renderSuggestions(suggestions) {
    if (!autocompleteList) {
      console.error("Autocomplete: dropdown element not found");
      return;
    }
    
    autocompleteList.innerHTML = "";
    selectedIndex = -1;
    
    if (suggestions.length === 0) {
      console.log("Autocomplete: no suggestions to show");
      hideAutocomplete();
      return;
    }
    
    console.log("Autocomplete: rendering", suggestions.length, "suggestions");
    
    suggestions.forEach(function (suggestion, index) {
      var item = document.createElement("div");
      item.className = "autocomplete-item";
      item.textContent = suggestion.prompt;
      
      // Add usage indicator for popular prompts
      if (suggestion.usage_count > 0) {
        var badge = document.createElement("span");
        badge.className = "usage-badge";
        badge.textContent = suggestion.usage_count;
        badge.title = "Used " + suggestion.usage_count + " time" + (suggestion.usage_count > 1 ? "s" : "");
        item.appendChild(badge);
      }
      
      // Click handler
      item.addEventListener("click", function () {
        selectSuggestion(suggestion);
      });
      
      // Hover handler
      item.addEventListener("mouseenter", function () {
        // Remove previous selection
        var items = autocompleteList.querySelectorAll(".autocomplete-item");
        items.forEach(function (el) { el.classList.remove("selected"); });
        
        // Select this item
        item.classList.add("selected");
        selectedIndex = index;
      });
      
      autocompleteList.appendChild(item);
    });
    
    showAutocomplete();
  }

  function selectSuggestion(suggestion) {
    promptInput.value = suggestion.prompt;
    hideAutocomplete();
    promptInput.focus();
    
    // Trigger input event for prompt history to update
    var event = new Event("input", { bubbles: true });
    promptInput.dispatchEvent(event);
  }

  function showAutocomplete() {
    autocompleteList.style.display = "block";
  }

  function hideAutocomplete() {
    autocompleteList.style.display = "none";
    selectedIndex = -1;
  }

  // Initialize on DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
