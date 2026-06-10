/**
 * tableau.js — IUAInsight
 * Logique JS partagée : graphiques Chart.js, filtres, tri de tableaux,
 * badges risque ML, exports CSV côté client, utilitaires UI.
 */

"use strict";

/* =========================================================
   1. UTILITAIRES GÉNÉRAUX
   ========================================================= */

/**
 * Retourne l'élément DOM ou null sans exception.
 */
function $id(id) {
  return document.getElementById(id);
}

/**
 * Sélecteur multiple.
 */
function $$(selector, ctx) {
  return Array.from((ctx || document).querySelectorAll(selector));
}

/**
 * Couleur CSS selon niveau de risque ML.
 */
const RISQUE_COLORS = {
  critique:     { bg: "rgba(239,68,68,0.15)",  border: "#ef4444" },
  modere:       { bg: "rgba(245,158,11,0.15)", border: "#f59e0b" },
  surveillance: { bg: "rgba(59,130,246,0.15)", border: "#3b82f6" },
  ok:           { bg: "rgba(16,185,129,0.15)", border: "#10b981" },
};

function risqueColor(niveau, type) {
  const c = RISQUE_COLORS[niveau] || RISQUE_COLORS.ok;
  return type === "bg" ? c.bg : c.border;
}

/* =========================================================
   2. CONFIGURATION CHART.JS GLOBALE
   ========================================================= */

if (typeof Chart !== "undefined") {
  Chart.defaults.font.family = "'Segoe UI', system-ui, sans-serif";
  Chart.defaults.font.size   = 12;
  Chart.defaults.color       = "#64748b";
  Chart.defaults.plugins.legend.labels.boxWidth = 12;
  Chart.defaults.plugins.tooltip.backgroundColor = "#1e2d3d";
  Chart.defaults.plugins.tooltip.padding         = 10;
  Chart.defaults.plugins.tooltip.cornerRadius    = 6;
}

/* =========================================================
   3. GRAPHIQUES — TABLEAU FILIÈRE (tableau_f.html)
   ========================================================= */

/**
 * Initialise le graphique "Réussite / Échec par niveau".
 * Données injectées via window.IUAI_DATA.niveaux depuis le template.
 */
function initNiveauChart() {
  const canvas = $id("niveauChart");
  if (!canvas) return;

  const data = window.IUAI_DATA && window.IUAI_DATA.niveaux;
  if (!data) return;

  const labels   = Object.keys(data.reussite);
  const reussite = labels.map(l => data.reussite[l]);
  const echec    = labels.map(l => data.echec[l]);

  new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Taux de réussite (%)",
          data:  reussite,
          backgroundColor: "rgba(59,130,246,0.7)",
          borderColor:     "#3b82f6",
          borderWidth: 1,
          borderRadius: 4,
        },
        {
          label: "Taux d'échec (%)",
          data:  echec,
          backgroundColor: "rgba(239,68,68,0.7)",
          borderColor:     "#ef4444",
          borderWidth: 1,
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "top" } },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: { callback: v => v + "%" },
          grid: { color: "rgba(0,0,0,0.05)" },
        },
        x: { grid: { display: false } },
      },
    },
  });
}

/**
 * Initialise le graphique d'évolution pluriannuelle par filière.
 * window.IUAI_DATA.evolution : { filiere: [val_annee1, ...], ... }
 * window.IUAI_DATA.annees    : ["2022-2023", "2023-2024", ...]
 */
function initEvolutionChart() {
  const canvas = $id("evolutionChart");
  if (!canvas) return;

  const data = window.IUAI_DATA && window.IUAI_DATA.evolution;
  if (!data) return;

  const annees = window.IUAI_DATA.annees || [];

  const PALETTE = [
    "#3b82f6","#10b981","#f59e0b","#ef4444",
    "#8b5cf6","#06b6d4","#ec4899","#84cc16",
  ];

  const datasets = Object.entries(data).map(([nom, valeurs], idx) => ({
    label: nom,
    data:  valeurs,
    borderColor:     PALETTE[idx % PALETTE.length],
    backgroundColor: PALETTE[idx % PALETTE.length] + "22",
    borderWidth: 2,
    tension: 0.35,
    pointRadius: 4,
    pointHoverRadius: 6,
    fill: false,
  }));

  new Chart(canvas, {
    type: "line",
    data: { labels: annees, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { position: "bottom" },
        tooltip: {
          callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y}%` },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: { callback: v => v + "%" },
          grid: { color: "rgba(0,0,0,0.05)" },
        },
        x: { grid: { display: false } },
      },
    },
  });
}

/* =========================================================
   4. GRAPHIQUES — TABLEAU DE BORD (tableau_de_bord.html)
   ========================================================= */

/**
 * Donut réussite / échec / abandon.
 * window.IUAI_DATA.synthese : { reussite, echec, abandon }
 */
function initSyntheseDonut() {
  const canvas = $id("syntheseDonut");
  if (!canvas) return;

  const d = window.IUAI_DATA && window.IUAI_DATA.synthese;
  if (!d) return;

  new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: ["Réussite", "Échec", "Abandon"],
      datasets: [{
        data:            [d.reussite, d.echec, d.abandon],
        backgroundColor: ["#10b981", "#ef4444", "#f59e0b"],
        borderWidth: 0,
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "68%",
      plugins: {
        legend: { position: "bottom" },
        tooltip: {
          callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed}%` },
        },
      },
    },
  });
}

/**
 * Barres filières (taux réussite).
 * window.IUAI_DATA.filieres : [{ nom, reussite, echec, abandon }, ...]
 */
function initFilieresBar() {
  const canvas = $id("filieresBar");
  if (!canvas) return;

  const filieres = window.IUAI_DATA && window.IUAI_DATA.filieres;
  if (!filieres || !filieres.length) return;

  const sorted = [...filieres].sort((a, b) => b.reussite - a.reussite);
  const labels   = sorted.map(f => f.nom);
  const reussite = sorted.map(f => f.reussite);
  const echec    = sorted.map(f => f.echec);

  new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Réussite (%)",
          data:  reussite,
          backgroundColor: sorted.map(f =>
            f.reussite >= 80 ? "rgba(16,185,129,0.75)" :
            f.reussite >= 60 ? "rgba(59,130,246,0.75)" :
            f.reussite >= 40 ? "rgba(245,158,11,0.75)" :
                               "rgba(239,68,68,0.75)"
          ),
          borderRadius: 4,
        },
        {
          label: "Échec (%)",
          data:  echec,
          backgroundColor: "rgba(239,68,68,0.3)",
          borderRadius: 4,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "top" } },
      scales: {
        x: {
          beginAtZero: true,
          max: 100,
          ticks: { callback: v => v + "%" },
          grid: { color: "rgba(0,0,0,0.05)" },
        },
        y: { grid: { display: false } },
      },
    },
  });
}

/* =========================================================
   5. GRAPHIQUES — TENDANCES (tendances.html)
   ========================================================= */

function initTendancesCharts() {
  // Évolution des inscriptions
  const inscCanvas = $id("inscriptionsChart");
  if (inscCanvas && window.IUAI_DATA && window.IUAI_DATA.inscriptions) {
    const d = window.IUAI_DATA.inscriptions;
    new Chart(inscCanvas, {
      type: "line",
      data: {
        labels: d.map(x => x.annee),
        datasets: [{
          label: "Inscriptions",
          data:  d.map(x => x.nombre),
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59,130,246,0.08)",
          borderWidth: 2,
          tension: 0.35,
          fill: true,
          pointRadius: 5,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: false, grid: { color: "rgba(0,0,0,0.05)" } },
          x: { grid: { display: false } },
        },
      },
    });
  }

  // Taux réussite / échec global
  const txCanvas = $id("tauxGlobalChart");
  if (txCanvas && window.IUAI_DATA && window.IUAI_DATA.taux_reussite_annuel) {
    const annees  = window.IUAI_DATA.annees || [];
    const reussite = window.IUAI_DATA.taux_reussite_annuel;
    const echec    = window.IUAI_DATA.taux_echec_annuel || [];
    new Chart(txCanvas, {
      type: "line",
      data: {
        labels: annees,
        datasets: [
          {
            label: "Réussite (%)",
            data: reussite,
            borderColor: "#10b981",
            backgroundColor: "rgba(16,185,129,0.08)",
            borderWidth: 2,
            tension: 0.35,
            fill: true,
          },
          {
            label: "Échec (%)",
            data: echec,
            borderColor: "#ef4444",
            backgroundColor: "rgba(239,68,68,0.08)",
            borderWidth: 2,
            tension: 0.35,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: { legend: { position: "top" } },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: { callback: v => v + "%" },
            grid: { color: "rgba(0,0,0,0.05)" },
          },
          x: { grid: { display: false } },
        },
      },
    });
  }
}

/* =========================================================
   6. GRAPHIQUES — ANALYSE DÉMOGRAPHIQUE (analyse_demo.html)
   ========================================================= */

function initDemoCharts() {
  // Répartition genre
  const genreCanvas = $id("genreChart");
  if (genreCanvas && window.IUAI_DATA && window.IUAI_DATA.demo) {
    const d = window.IUAI_DATA.demo;
    new Chart(genreCanvas, {
      type: "doughnut",
      data: {
        labels: ["Hommes", "Femmes"],
        datasets: [{
          data: [d.hommes, d.femmes],
          backgroundColor: ["#3b82f6", "#ec4899"],
          borderWidth: 0,
          hoverOffset: 6,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "65%",
        plugins: { legend: { position: "bottom" } },
      },
    });
  }

  // Tranches d'âge
  const ageCanvas = $id("ageChart");
  if (ageCanvas && window.IUAI_DATA && window.IUAI_DATA.ages) {
    const ages = window.IUAI_DATA.ages;
    new Chart(ageCanvas, {
      type: "bar",
      data: {
        labels: ages.map(a => a.intervalle),
        datasets: [{
          label: "Effectif",
          data:  ages.map(a => a.effectif),
          backgroundColor: "rgba(59,130,246,0.7)",
          borderColor: "#3b82f6",
          borderWidth: 1,
          borderRadius: 4,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: "rgba(0,0,0,0.05)" } },
          x: { grid: { display: false } },
        },
      },
    });
  }

  // Genre par filière (barres groupées)
  const filiereGenreCanvas = $id("filiereGenreChart");
  if (filiereGenreCanvas && window.IUAI_DATA && window.IUAI_DATA.filieres_genre) {
    const fg = window.IUAI_DATA.filieres_genre;
    new Chart(filiereGenreCanvas, {
      type: "bar",
      data: {
        labels: fg.map(f => f.nom),
        datasets: [
          {
            label: "Hommes (%)",
            data:  fg.map(f => f.hommes),
            backgroundColor: "rgba(59,130,246,0.7)",
            borderRadius: 3,
          },
          {
            label: "Femmes (%)",
            data:  fg.map(f => f.femmes),
            backgroundColor: "rgba(236,72,153,0.7)",
            borderRadius: 3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "top" } },
        scales: {
          x: { stacked: true, grid: { display: false } },
          y: { stacked: true, beginAtZero: true, max: 100,
               ticks: { callback: v => v + "%" },
               grid: { color: "rgba(0,0,0,0.05)" } },
        },
      },
    });
  }
}

/* =========================================================
   7. TRI DE TABLEAUX
   ========================================================= */

function initSortableTable(tableId) {
  const table = $id(tableId);
  if (!table) return;

  const headers = $$("th[data-sort]", table);
  let lastCol = null, lastDir = 1;

  headers.forEach(th => {
    th.style.cursor = "pointer";
    th.addEventListener("click", () => {
      const col = parseInt(th.dataset.sort, 10);
      const dir = (col === lastCol) ? -lastDir : 1;
      lastCol = col; lastDir = dir;

      headers.forEach(h => {
        h.classList.remove("sort-asc", "sort-desc");
        const ico = h.querySelector(".sort-icon");
        if (ico) ico.textContent = "⇅";
      });
      th.classList.add(dir === 1 ? "sort-asc" : "sort-desc");
      const ico = th.querySelector(".sort-icon");
      if (ico) ico.textContent = dir === 1 ? "↑" : "↓";

      const tbody = table.querySelector("tbody");
      if (!tbody) return;
      const rows = Array.from(tbody.querySelectorAll("tr"));
      rows.sort((a, b) => {
        const aCell = a.cells[col];
        const bCell = b.cells[col];
        if (!aCell || !bCell) return 0;
        const aVal = aCell.dataset.value !== undefined
          ? parseFloat(aCell.dataset.value)
          : aCell.textContent.trim();
        const bVal = bCell.dataset.value !== undefined
          ? parseFloat(bCell.dataset.value)
          : bCell.textContent.trim();
        if (!isNaN(aVal) && !isNaN(bVal)) return dir * (aVal - bVal);
        return dir * String(aVal).localeCompare(String(bVal), "fr");
      });
      rows.forEach(r => tbody.appendChild(r));
    });
  });
}

/* =========================================================
   8. FILTRE DE RECHERCHE EN DIRECT SUR UN TABLEAU
   ========================================================= */

function initTableSearch(inputId, tableId, colIndexes) {
  const input = $id(inputId);
  const table = $id(tableId);
  if (!input || !table) return;

  input.addEventListener("input", () => {
    const q = input.value.toLowerCase().trim();
    const tbody = table.querySelector("tbody");
    if (!tbody) return;
    $$("tr", tbody).forEach(row => {
      const text = (colIndexes || [])
        .map(i => row.cells[i] ? row.cells[i].textContent.toLowerCase() : "")
        .join(" ");
      row.style.display = (!q || text.includes(q)) ? "" : "none";
    });
    updateEmptyState(table);
  });
}

function updateEmptyState(table) {
  const tbody = table.querySelector("tbody");
  if (!tbody) return;
  const visible = $$("tr", tbody).filter(r => r.style.display !== "none");
  let empty = table.parentElement.querySelector(".table-empty-state");
  if (visible.length === 0) {
    if (!empty) {
      empty = document.createElement("div");
      empty.className = "table-empty-state text-center text-muted py-3";
      empty.textContent = "Aucun résultat trouvé.";
      table.parentElement.appendChild(empty);
    }
    empty.style.display = "";
  } else if (empty) {
    empty.style.display = "none";
  }
}

/* =========================================================
   9. EXPORT CSV CÔTÉ CLIENT
   ========================================================= */

function exportTableCSV(tableId, filename) {
  const table = $id(tableId);
  if (!table) return;
  const rows = [];
  $$("tr", table).forEach(row => {
    if (row.style.display === "none") return;
    const cells = $$("th, td", row).map(c => {
      let v = (c.dataset.value !== undefined ? c.dataset.value : c.textContent).trim();
      v = v.replace(/"/g, '""');
      return `"${v}"`;
    });
    rows.push(cells.join(","));
  });
  const csv  = "\uFEFF" + rows.join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  link.href  = URL.createObjectURL(blob);
  link.download = filename || "export.csv";
  link.click();
  URL.revokeObjectURL(link.href);
}

/* =========================================================
   10. BADGES RISQUE ML (dynamiques)
   ========================================================= */

function applyRisqueBadges() {
  $$("[data-risque]").forEach(el => {
    const niv = el.dataset.risque;
    const MAP = {
      critique:     { label: "Critique",     cls: "badge-danger"   },
      modere:       { label: "Modéré",       cls: "badge-warning"  },
      surveillance: { label: "Surveillance", cls: "badge-info"     },
      ok:           { label: "OK",           cls: "badge-success"  },
    };
    const info = MAP[niv] || MAP.ok;
    if (!el.textContent.trim()) el.textContent = info.label;
    el.classList.add(info.cls);
  });
}

/* =========================================================
   11. BARRE DE PROGRESSION ANIMÉE
   ========================================================= */

function animateProgressBars() {
  $$(".progress-bar[data-value]").forEach(bar => {
    const target = parseFloat(bar.dataset.value) || 0;
    bar.style.width = "0%";
    setTimeout(() => {
      bar.style.transition = "width 0.7s cubic-bezier(.4,0,.2,1)";
      bar.style.width = Math.min(target, 100) + "%";
    }, 80);
  });
}

/* =========================================================
   12. CONFIRMATION DE SUPPRESSION
   ========================================================= */

function initDeleteConfirm() {
  $$("[data-confirm]").forEach(el => {
    el.addEventListener("click", e => {
      const msg = el.dataset.confirm || "Confirmer la suppression ?";
      if (!confirm(msg)) e.preventDefault();
    });
  });
}

/* =========================================================
   13. AUTO-SUBMIT FILTRES (selects)
   ========================================================= */

function initAutoSubmitFilters(formId) {
  const form = $id(formId) || document.querySelector("form.filter-form");
  if (!form) return;
  $$("select", form).forEach(sel => {
    sel.addEventListener("change", () => form.submit());
  });
}

/* =========================================================
   14. TOOLTIP BOOTSTRAP — INIT GLOBALE
   ========================================================= */

function initTooltips() {
  if (typeof bootstrap === "undefined") return;
  $$('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el, { trigger: "hover" });
  });
}

/* =========================================================
   15. COMPTEUR ANIMÉ (KPI cards)
   ========================================================= */

function animateCounters() {
  $$("[data-count]").forEach(el => {
    const target = parseFloat(el.dataset.count.replace(",", ".")) || 0;
    const isFloat = el.dataset.count.includes(".");
    const duration = 900;
    const steps = 40;
    const increment = target / steps;
    let current = 0;
    const timer = setInterval(() => {
      current = Math.min(current + increment, target);
      el.textContent = isFloat
        ? current.toFixed(1)
        : Math.round(current).toLocaleString("fr-FR");
      if (current >= target) clearInterval(timer);
    }, duration / steps);
  });
}

/* =========================================================
   16. INITIALISATION PRINCIPALE (DOMContentLoaded)
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {
  // Graphiques (chaque fonction vérifie si son canvas existe)
  initNiveauChart();
  initEvolutionChart();
  initSyntheseDonut();
  initFilieresBar();
  initTendancesCharts();
  initDemoCharts();

  // Tableaux
  $$("table[id]").forEach(t => initSortableTable(t.id));
  initTableSearch("searchInput",    "mainTable",   [0, 1, 2, 3]);
  initTableSearch("searchEtudiant", "etudiantTable", [0, 1, 2]);

  // Filtres auto-submit
  initAutoSubmitFilters("filterForm");

  // UI
  applyRisqueBadges();
  animateProgressBars();
  animateCounters();
  initDeleteConfirm();
  initTooltips();

  // Boutons export CSV
  const exportBtn = $id("exportCSV");
  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      const tableId  = exportBtn.dataset.table  || "mainTable";
      const filename = exportBtn.dataset.file   || "export_iuainsight.csv";
      exportTableCSV(tableId, filename);
    });
  }
});

/* =========================================================
   17. API PUBLIQUE (appelable depuis les templates inline)
   ========================================================= */

window.IUAInsight = {
  initNiveauChart,
  initEvolutionChart,
  initSyntheseDonut,
  initFilieresBar,
  initTendancesCharts,
  initDemoCharts,
  exportTableCSV,
  animateProgressBars,
  animateCounters,
  risqueColor,
};