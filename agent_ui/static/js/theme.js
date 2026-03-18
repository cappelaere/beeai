(function () {
  var STORAGE_KEY = "realtyiq-theme";
  var root = document.documentElement;

  function effectiveTheme(stored) {
    if (stored === "system") {
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    return stored === "dark" ? "dark" : "light";
  }

  function applyClass(theme) {
    root.classList.remove("theme-light", "theme-dark");
    root.classList.add("theme-" + theme);
  }

  function applyTheme() {
    var stored = localStorage.getItem(STORAGE_KEY) || "light";
    applyClass(effectiveTheme(stored));
  }

  // Apply on load (head script already set initial class; this keeps "system" in sync)
  applyTheme();

  // When theme is "system", react to preference changes
  window.matchMedia("(prefers-color-scheme: dark)").addListener(function () {
    if ((localStorage.getItem(STORAGE_KEY) || "light") === "system") {
      applyTheme();
    }
  });

  window.RealtyIQTheme = {
    get: function () {
      return localStorage.getItem(STORAGE_KEY) || "light";
    },
    set: function (value) {
      if (value !== "light" && value !== "dark" && value !== "system") return;
      localStorage.setItem(STORAGE_KEY, value);
      applyTheme();
    },
  };
})();
