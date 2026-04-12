/**
 * menu.js — GENESIS Menu Controller
 * Toggle dropdown, route to page overlays.
 * Does NOT modify any existing DOM elements or scripts.
 */
(function () {
  "use strict";

  var menuOpen = false;

  function toggleMenu() {
    var dd = document.getElementById("genesis-menu-dropdown");
    if (!dd) return;
    menuOpen = !menuOpen;
    if (menuOpen) {
      dd.style.display = "block";
      // Force reflow before adding class for transition
      void dd.offsetHeight;
      dd.classList.add("visible");
    } else {
      dd.classList.remove("visible");
      setTimeout(function () {
        if (!menuOpen) dd.style.display = "none";
      }, 280);
    }
  }

  function closeMenu() {
    var dd = document.getElementById("genesis-menu-dropdown");
    if (!dd) return;
    menuOpen = false;
    dd.classList.remove("visible");
    setTimeout(function () { dd.style.display = "none"; }, 280);
  }

  window.addEventListener("load", function () {
    var btn = document.getElementById("genesis-menu-btn");
    if (btn) {
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        toggleMenu();
      });
    }

    // Close menu on outside click
    document.addEventListener("click", function (e) {
      if (!menuOpen) return;
      var dd = document.getElementById("genesis-menu-dropdown");
      var bt = document.getElementById("genesis-menu-btn");
      if (dd && !dd.contains(e.target) && bt && !bt.contains(e.target)) {
        closeMenu();
      }
    });

    // Bind menu items to page opener
    var items = document.querySelectorAll(".g-menu-item[data-page]");
    for (var i = 0; i < items.length; i++) {
      items[i].addEventListener("click", function () {
        var pageId = this.getAttribute("data-page");
        closeMenu();
        if (window.GenesisPages && window.GenesisPages.openPage) {
          window.GenesisPages.openPage(pageId);
        }
      });
    }
  });
})();
