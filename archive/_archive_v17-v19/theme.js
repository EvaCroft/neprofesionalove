/* ==========================================================================
   Neprofesionálové — Design template systém (theme.js)
   v17 — realtime slider engine + přepínání layoutů + presety (localStorage)

   Použití na libovolné stránce:
     <link rel="stylesheet" href="theme.css">
     <script src="theme.js"></script>
     ... a v <body> zavolat NeprofTheme.init() po DOMContentLoaded
   ========================================================================== */

(function (window) {
  "use strict";

  const STORAGE_KEY = "neprof_theme_v1";

  // Dostupné layouty (v17: 3 architektura, v18: +2 dle vizuálů, v19: +3)
  const LAYOUTS = [
    { id: "layout-sidebar-left", label: "Sidebar vlevo" },
    { id: "layout-sidebar-right", label: "Sidebar vpravo" },
    { id: "layout-topnav", label: "Horní lišta" },
    { id: "layout-feed-cards", label: "Feed karet (tmavý, spodní nav)" },
    { id: "layout-grid-gallery", label: "Galerie / grid (ikonový panel + top bar)" },
    { id: "layout-split-view", label: "Split-view (seznam + detail)" },
    { id: "layout-kanban", label: "Kanban board" },
    { id: "layout-magazine", label: "Magazín (hero + mřížka)" },
  ];

  // Slidery a jejich rozsahy/výchozí hodnoty — mapované přímo na CSS custom properties
  const SLIDERS = [
    { key: "--color-primary-h", label: "Odstín barvy", min: 0, max: 360, step: 1, unit: "", default: 210 },
    { key: "--color-primary-s", label: "Sytost barvy", min: 0, max: 100, step: 1, unit: "%", default: 70 },
    { key: "--color-primary-l", label: "Jas barvy", min: 20, max: 80, step: 1, unit: "%", default: 50 },
    { key: "--font-scale", label: "Velikost písma", min: 0.85, max: 1.3, step: 0.01, unit: "", default: 1 },
    { key: "--spacing-scale", label: "Mezery", min: 0.7, max: 1.5, step: 0.01, unit: "", default: 1 },
    { key: "--radius-scale", label: "Zaoblení rohů", min: 0, max: 2, step: 0.05, unit: "", default: 1 },
  ];

  const DEFAULT_PRESET = {
    name: "Výchozí",
    layout: "layout-sidebar-left",
    vars: SLIDERS.reduce((acc, s) => {
      acc[s.key] = s.default;
      return acc;
    }, {}),
  };

  function cssValueFor(sliderDef, rawValue) {
    return `${rawValue}${sliderDef.unit}`;
  }

  function applyVars(vars) {
    const root = document.documentElement;
    SLIDERS.forEach((s) => {
      const v = vars[s.key];
      if (v === undefined) return;
      root.style.setProperty(s.key, cssValueFor(s, v));
    });
  }

  function applyLayout(layoutId) {
    LAYOUTS.forEach((l) => document.body.classList.remove(l.id));
    document.body.classList.add(layoutId);
  }

  function loadPreset() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return structuredCloneSafe(DEFAULT_PRESET);
      const parsed = JSON.parse(raw);
      if (!parsed || !parsed.vars || !parsed.layout) return structuredCloneSafe(DEFAULT_PRESET);
      return parsed;
    } catch (e) {
      console.warn("NeprofTheme: nepodařilo se načíst uložený preset, používám výchozí.", e);
      return structuredCloneSafe(DEFAULT_PRESET);
    }
  }

  function savePreset(preset) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(preset));
      return true;
    } catch (e) {
      console.warn("NeprofTheme: uložení presetu selhalo (localStorage nedostupný?).", e);
      return false;
    }
  }

  function resetToDefault() {
    const preset = structuredCloneSafe(DEFAULT_PRESET);
    currentState = preset;
    savePreset(preset);
    applyVars(preset.vars);
    applyLayout(preset.layout);
    return preset;
  }

  function structuredCloneSafe(obj) {
    return JSON.parse(JSON.stringify(obj));
  }

  let currentState = null;

  function init() {
    currentState = loadPreset();
    applyVars(currentState.vars);
    applyLayout(currentState.layout);
    return currentState;
  }

  function setLayout(layoutId) {
    if (!LAYOUTS.some((l) => l.id === layoutId)) return;
    currentState.layout = layoutId;
    applyLayout(layoutId);
    savePreset(currentState);
  }

  function setVar(key, value) {
    if (!SLIDERS.some((s) => s.key === key)) return;
    currentState.vars[key] = value;
    applyVars(currentState.vars);
    savePreset(currentState);
  }

  function getState() {
    return structuredCloneSafe(currentState);
  }

  window.NeprofTheme = {
    LAYOUTS,
    SLIDERS,
    DEFAULT_PRESET,
    init,
    setLayout,
    setVar,
    resetToDefault,
    getState,
  };
})(window);
