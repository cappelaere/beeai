/* RealtyIQ website analytics client helper.
 * Sends optional client location fallback (city/state/country) to backend session storage.
 */
(function () {
  if (typeof window === "undefined" || typeof fetch === "undefined") {
    return;
  }

  function readCookie(name) {
    var match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return match ? decodeURIComponent(match[2]) : "";
  }

  function clean(value) {
    return String(value || "").trim().slice(0, 120);
  }

  function buildLocationPayload() {
    var data = window.REALTYIQ_CLIENT_LOCATION || {};
    var payload = {
      city: clean(data.city),
      state: clean(data.state),
      country: clean(data.country),
    };
    if (!payload.city && !payload.state && !payload.country) {
      return null;
    }
    return payload;
  }

  function sendLocation() {
    if (sessionStorage.getItem("analytics-location-sent") === "1") {
      return;
    }
    var payload = buildLocationPayload();
    if (!payload) {
      return;
    }
    fetch("/api/analytics/location/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": readCookie("csrftoken"),
      },
      credentials: "same-origin",
      body: JSON.stringify(payload),
    })
      .then(function () {
        sessionStorage.setItem("analytics-location-sent", "1");
      })
      .catch(function () {
        // Silent fail: analytics fallback should never block UI.
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", sendLocation);
  } else {
    sendLocation();
  }
})();

