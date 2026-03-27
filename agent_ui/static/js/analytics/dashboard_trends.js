/* Internal website analytics dashboard trend charts (no CDN dependency). */
(function () {
  var dataElement = document.getElementById("analytics-trends-data");
  if (!dataElement) {
    return;
  }

  var trends = {};
  try {
    trends = JSON.parse(dataElement.textContent || "{}");
  } catch (_error) {
    trends = {};
  }
  if (!trends || typeof trends !== "object") {
    return;
  }

  function drawLineChart(canvasId, rows) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || !Array.isArray(rows) || rows.length === 0) {
      return;
    }
    var context = canvas.getContext("2d");
    if (!context) {
      return;
    }

    var values = rows.map(function (item) {
      return Number(item.page_views || 0);
    });
    var maxValue = Math.max.apply(null, values);
    var width = canvas.width;
    var height = canvas.height;
    var padding = 18;
    var graphWidth = width - padding * 2;
    var graphHeight = height - padding * 2;

    context.clearRect(0, 0, width, height);
    context.strokeStyle = "#d0d7de";
    context.lineWidth = 1;
    context.beginPath();
    context.moveTo(padding, padding);
    context.lineTo(padding, height - padding);
    context.lineTo(width - padding, height - padding);
    context.stroke();

    if (maxValue <= 0) {
      return;
    }

    context.strokeStyle = "#0f62fe";
    context.lineWidth = 2;
    context.beginPath();
    values.forEach(function (value, index) {
      var x = padding + (graphWidth * index) / Math.max(1, values.length - 1);
      var y = padding + graphHeight * (1 - value / maxValue);
      if (index === 0) {
        context.moveTo(x, y);
      } else {
        context.lineTo(x, y);
      }
    });
    context.stroke();
  }

  drawLineChart("analytics-trend-hour", trends.hour);
  drawLineChart("analytics-trend-day", trends.day);
  drawLineChart("analytics-trend-week", trends.week);
  drawLineChart("analytics-trend-month", trends.month);
})();

