/**
 * widget.js — GENESIS Clock Widget (Standalone)
 * Real-time clock, date, location, and weather.
 * Does NOT touch face.js, genesis_ws.js, or any canvas logic.
 */

(function () {
  "use strict";

  // ── Weather API (free, no key needed) ──
  const GEO_API = "https://ipapi.co/json/";
  const WEATHER_API = "https://wttr.in/{city}?format=j1";

  // ── Weather icon map (wttr.in weatherCode → emoji) ──
  const WEATHER_ICONS = {
    "113": "☀️",   // Sunny
    "116": "⛅",   // Partly cloudy
    "119": "☁️",   // Cloudy
    "122": "☁️",   // Overcast
    "143": "🌫️",  // Mist
    "176": "🌦️",  // Patchy rain
    "179": "🌨️",  // Patchy snow
    "182": "🌧️",  // Patchy sleet
    "185": "🌧️",  // Patchy freezing drizzle
    "200": "⛈️",   // Thunder
    "227": "❄️",   // Blowing snow
    "230": "❄️",   // Blizzard
    "248": "🌫️",  // Fog
    "260": "🌫️",  // Freezing fog
    "263": "🌦️",  // Patchy light drizzle
    "266": "🌧️",  // Light drizzle
    "281": "🌧️",  // Freezing drizzle
    "284": "🌧️",  // Heavy freezing drizzle
    "293": "🌦️",  // Patchy light rain
    "296": "🌧️",  // Light rain
    "299": "🌧️",  // Moderate rain
    "302": "🌧️",  // Heavy rain
    "305": "🌧️",  // Heavy rain intervals
    "308": "🌧️",  // Heavy rain
    "311": "🌧️",  // Light freezing rain
    "314": "🌧️",  // Heavy freezing rain
    "317": "🌨️",  // Light sleet
    "320": "🌨️",  // Heavy sleet
    "323": "🌨️",  // Patchy light snow
    "326": "🌨️",  // Light snow
    "329": "❄️",   // Moderate snow
    "332": "❄️",   // Heavy snow
    "335": "❄️",   // Patchy heavy snow
    "338": "❄️",   // Heavy snow
    "350": "🌧️",  // Ice pellets
    "353": "🌦️",  // Light rain shower
    "356": "🌧️",  // Heavy rain shower
    "359": "🌧️",  // Torrential rain
    "362": "🌨️",  // Light sleet shower
    "365": "🌨️",  // Heavy sleet shower
    "368": "🌨️",  // Light snow shower
    "371": "❄️",   // Heavy snow shower
    "374": "🌧️",  // Light ice pellet shower
    "377": "🌧️",  // Heavy ice pellet shower
    "386": "⛈️",   // Patchy thunderstorm with rain
    "389": "⛈️",   // Heavy thunderstorm
    "392": "⛈️",   // Patchy thunderstorm with snow
    "395": "⛈️",   // Heavy thunderstorm with snow
  };

  const DAYS = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
  const MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];

  // ── State ──
  let locationText = "LOCATING...";
  let tempText = "--°C";
  let weatherIcon = "⛅";
  let weatherFetched = false;

  // ── Build DOM ──
  function buildWidget() {
    const w = document.getElementById("clock-widget");
    if (!w) return;

    w.innerHTML = `
      <div class="cw-neon-ring"></div>
      <div class="cw-glass-highlight"></div>
      <div class="cw-content">
        <span class="cw-weather-icon" id="cw-weather-icon">${weatherIcon}</span>
        <span class="cw-location" id="cw-location">${locationText}</span>
        <span class="cw-temp" id="cw-temp">${tempText}</span>
        <span class="cw-time" id="cw-time">--:--</span>
        <span class="cw-date" id="cw-date">--- --- -- / -- SEC</span>
        <span class="cw-sys-status" id="cw-sys-status">SYS STAT OK</span>
      </div>
    `;
  }

  // ── Clock tick (1 second interval) ──
  function updateClock() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, "0");
    const m = String(now.getMinutes()).padStart(2, "0");
    const s = String(now.getSeconds()).padStart(2, "0");
    const day = DAYS[now.getDay()];
    const month = MONTHS[now.getMonth()];
    const date = String(now.getDate()).padStart(2, "0");

    const timeEl = document.getElementById("cw-time");
    const dateEl = document.getElementById("cw-date");
    if (timeEl) timeEl.textContent = `${h}:${m}`;
    if (dateEl) dateEl.textContent = `${day}, ${month} ${date} / ${s} SEC`;
  }

  // ── Fetch location via IP ──
  async function fetchLocation() {
    try {
      const resp = await fetch(GEO_API);
      if (!resp.ok) throw new Error("Geo API failed");
      const data = await resp.json();
      const city = data.city || "UNKNOWN";
      const country = data.country_code || "";
      locationText = `${city}, ${country}`.toUpperCase();

      const locEl = document.getElementById("cw-location");
      if (locEl) locEl.textContent = locationText;

      // Now fetch weather for this city
      fetchWeather(city);
    } catch (e) {
      console.warn("[WIDGET] Location fetch failed:", e.message);
      locationText = "LOCATION N/A";
      const locEl = document.getElementById("cw-location");
      if (locEl) locEl.textContent = locationText;
    }
  }

  // ── Fetch weather via wttr.in ──
  async function fetchWeather(city) {
    try {
      const url = WEATHER_API.replace("{city}", encodeURIComponent(city));
      const resp = await fetch(url);
      if (!resp.ok) throw new Error("Weather API failed");
      const data = await resp.json();

      const current = data.current_condition && data.current_condition[0];
      if (current) {
        const tempC = current.temp_C || "--";
        const code = current.weatherCode || "116";

        tempText = `${tempC}°C`;
        weatherIcon = WEATHER_ICONS[code] || "⛅";
        weatherFetched = true;

        const tempEl = document.getElementById("cw-temp");
        const iconEl = document.getElementById("cw-weather-icon");
        if (tempEl) tempEl.textContent = tempText;
        if (iconEl) iconEl.textContent = weatherIcon;
      }
    } catch (e) {
      console.warn("[WIDGET] Weather fetch failed:", e.message);
      tempText = "--°C";
      const tempEl = document.getElementById("cw-temp");
      if (tempEl) tempEl.textContent = tempText;
    }
  }

  // ── Init ──
  function init() {
    buildWidget();
    updateClock();

    // Update clock every second
    setInterval(updateClock, 1000);

    // Fetch location + weather on load, refresh every 10 minutes
    fetchLocation();
    setInterval(fetchLocation, 600000);
  }

  // Wait for DOM
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
