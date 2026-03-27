/* Internal website analytics dashboard trend chart. */
(function () {
  var dataElement = document.getElementById("analytics-trend-data");
  var canvas = document.getElementById("analytics-trend-chart");
  if (!dataElement || !canvas || typeof Chart === "undefined") {
    return;
  }

  var rows = [];
  try {
    rows = JSON.parse(dataElement.textContent || "[]");
  } catch (_error) {
    rows = [];
  }
  if (!Array.isArray(rows) || rows.length === 0) {
    return;
  }

  var labels = rows.map(function (item) {
    var dt = new Date(item.bucket);
    if (isNaN(dt.getTime())) {
      return item.bucket || "";
    }
    return dt.toLocaleString();
  });
  var pageViews = rows.map(function (item) {
    return Number(item.page_views || 0);
  });
  var uniqueVisitors = rows.map(function (item) {
    return Number(item.unique_visitors || 0);
  });
  var uniqueUsers = rows.map(function (item) {
    return Number(item.unique_users || 0);
  });

  // eslint-disable-next-line no-new
  new Chart(canvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Page views",
          data: pageViews,
          borderColor: "#0f62fe",
          backgroundColor: "rgba(15, 98, 254, 0.15)",
          tension: 0.25,
          fill: true,
        },
        {
          label: "Unique visitors",
          data: uniqueVisitors,
          borderColor: "#24a148",
          backgroundColor: "rgba(36, 161, 72, 0.12)",
          tension: 0.25,
          fill: false,
        },
        {
          label: "Unique users",
          data: uniqueUsers,
          borderColor: "#8a2be2",
          backgroundColor: "rgba(138, 43, 226, 0.12)",
          tension: 0.25,
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            precision: 0,
          },
        },
      },
    },
  });
})();

