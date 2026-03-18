(function () {
  function getCsrfToken() {
    return window.CSRF_TOKEN || document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
  }

  document.querySelectorAll(".fav-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var id = btn.dataset.id;
      var isFav = btn.dataset.fav === "1";
      var nextFav = !isFav;
      fetch("/api/cards/" + id + "/favorite/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({ is_favorite: nextFav }),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          btn.dataset.fav = data.is_favorite ? "1" : "0";
          btn.classList.toggle("is-favorite", data.is_favorite);
          btn.title = data.is_favorite ? "Remove from favorites" : "Add to favorites";
        })
        .catch(function (err) {
          console.error("Error toggling favorite:", err);
        });
    });
  });
})();
