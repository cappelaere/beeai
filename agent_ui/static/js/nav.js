(function () {
  var STORAGE_KEY = "realtyiq-nav-collapsed";
  var nav = document.getElementById("sidebar-nav");
  var toggle = document.getElementById("nav-toggle");

  function isCollapsed() {
    return localStorage.getItem(STORAGE_KEY) === "1";
  }

  function setCollapsed(collapsed) {
    if (nav) nav.classList.toggle("collapsed", collapsed);
    localStorage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
  }

  if (nav && toggle) {
    setCollapsed(isCollapsed());
    toggle.addEventListener("click", function () {
      setCollapsed(!isCollapsed());
    });
  }
})();
