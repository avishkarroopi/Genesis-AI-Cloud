/**
 * screen_router.js — GENESIS Screen Navigation Router
 * Manages flow: Splash → Enter → Login → Subscription → Dashboard
 * Referral screen is opened from hamburger menu only.
 * Does NOT modify splash.js, face.js, genesis_ws.js, menu.js, or any existing file.
 */
(function () {
  "use strict";

  // ── Intercept splash dismiss to show Enter Screen ──
  var _origSplashDismissed = false;

  // Override splash dismiss: after splash fades, show Enter Screen instead of dashboard
  // We observe the splash element for display:none
  function watchSplashDismiss() {
    var splash = document.getElementById("genesis-splash");
    if (!splash) {
      // No splash, jump to enter
      startFlow();
      return;
    }

    var observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (m) {
        if (m.attributeName === "style" && splash.style.display === "none" && !_origSplashDismissed) {
          _origSplashDismissed = true;
          observer.disconnect();
          startFlow();
        }
      });
    });
    observer.observe(splash, { attributes: true, attributeFilter: ["style"] });

    // Fallback if splash is already hidden
    if (splash.style.display === "none") {
      _origSplashDismissed = true;
      startFlow();
    }
  }

  function startFlow() {
    // Check if user is already logged in
    var loggedIn = localStorage.getItem("genesis_logged_in") === "true";
    if (loggedIn) {
      // Check first login for subscription
      var subscribed = localStorage.getItem("genesis_subscribed") === "true";
      if (!subscribed) {
        showSubscription();
      }
      // else: dashboard loads normally (already showing)
      return;
    }
    // Show Enter Screen
    if (window.GenesisEnterScreen && window.GenesisEnterScreen.show) {
      window.GenesisEnterScreen.show();
    }
  }

  // ── Enter → Login ──
  window.addEventListener("genesis_enter_complete", function () {
    var loggedIn = localStorage.getItem("genesis_logged_in") === "true";
    if (loggedIn) {
      var subscribed = localStorage.getItem("genesis_subscribed") === "true";
      if (!subscribed) {
        showSubscription();
      }
      // else: already on dashboard
    } else {
      if (window.GenesisLoginScreen && window.GenesisLoginScreen.show) {
        window.GenesisLoginScreen.show();
      }
    }
  });

  // ── Login → Subscription (first time) or Dashboard ──
  window.addEventListener("genesis_login_complete", function () {
    var subscribed = localStorage.getItem("genesis_subscribed") === "true";
    if (!subscribed) {
      showSubscription();
    }
    // else: dashboard already visible
  });

  // ── Subscription → Dashboard ──
  window.addEventListener("genesis_subscription_complete", function () {
    // Reveal dashboard cleanly
    var overlay = document.getElementById("genesis-page-overlay");
    if (overlay) overlay.style.display = "none";
    var startBtn = document.getElementById("startVoice");
    if (startBtn) startBtn.style.display = "block";
    var camBtn = document.getElementById("cameraToggle");
    if (camBtn) camBtn.style.display = "block";
  });

  function showSubscription() {
    if (window.GenesisSubscriptionScreen && window.GenesisSubscriptionScreen.show) {
      window.GenesisSubscriptionScreen.show();
    }
  }

  // ── Referral: hook into hamburger menu ──
  window.addEventListener("load", function () {
    // Add referral menu item if not present
    var dropdown = document.getElementById("genesis-menu-dropdown");
    if (dropdown && !dropdown.querySelector('[data-page="referral"]')) {
      // Find the last divider before About
      var aboutItem = dropdown.querySelector('[data-page="about"]');
      if (aboutItem) {
        var divider = document.createElement("div");
        divider.className = "g-menu-divider";
        var refItem = document.createElement("div");
        refItem.className = "g-menu-item";
        refItem.setAttribute("data-page", "referral");
        refItem.innerHTML = '<span class="g-menu-icon">🎁</span>Referral Program';
        dropdown.insertBefore(divider, aboutItem);
        dropdown.insertBefore(refItem, aboutItem);
      }
    }

    // Listen for referral menu click
    document.addEventListener("click", function (e) {
      var target = e.target.closest && e.target.closest('.g-menu-item[data-page="referral"]');
      if (target) {
        e.stopPropagation();
        if (window.GenesisReferralScreen && window.GenesisReferralScreen.show) {
          window.GenesisReferralScreen.show();
        }
      }
    });
  });

  // ── Start watching ──
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", watchSplashDismiss);
  } else {
    watchSplashDismiss();
  }
})();
