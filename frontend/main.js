/**
 * MailForge — Frontend
 * Hash-based client-side router + premium micro-interactions
 * All API calls preserved, zero Bootstrap dependency
 */

const API_BASE = "http://localhost:8000";

/* ══════════════════════════════════════════════════════
   ROUTER
   Hash-based routing: #generate | #settings | #help
   ══════════════════════════════════════════════════════ */

class Router {
  constructor() {
    this.current = null;
    this.navItems = document.querySelectorAll(".nav-item[data-page]");
    this.pages = {
      generate: document.getElementById("page-generate"),
      settings: document.getElementById("page-settings"),
      help:     document.getElementById("page-help"),
    };

    // Add stagger class to all forge-cards for entry animation
    document.querySelectorAll(".forge-card").forEach(el => el.classList.add("stagger-child"));

    window.addEventListener("hashchange", () => this._onHashChange());
    this.navItems.forEach(btn => {
      btn.addEventListener("click", () => {
        window.location.hash = btn.dataset.page;
      });
    });
  }

  init() {
    const page = this._getHash();
    this._show(page, false); // No animation on first load
  }

  _getHash() {
    const h = window.location.hash.replace("#", "").trim();
    return this.pages[h] ? h : "generate";
  }

  _onHashChange() {
    this._show(this._getHash(), true);
  }

  async _show(name, animate) {
    if (this.current === name) return;

    const prev = this.current ? this.pages[this.current] : null;
    const next = this.pages[name];

    // Animate exit
    if (prev && animate) {
      prev.classList.remove("page-active");
      prev.classList.add("page-exit");
      await delay(200);
      prev.classList.remove("page-exit");
      prev.style.display = "none";
    } else if (prev) {
      prev.classList.remove("page-active");
      prev.style.display = "none";
    }

    // Activate next
    next.style.display = "block";
    // Force reflow so animation triggers correctly
    next.offsetHeight; // eslint-disable-line no-unused-expressions
    next.classList.add("page-active");

    // Nav highlight
    this.navItems.forEach(btn => {
      btn.classList.toggle("active", btn.dataset.page === name);
    });

    this.current = name;
    window.scrollTo({ top: 0, behavior: animate ? "smooth" : "instant" });
  }
}

/* ══════════════════════════════════════════════════════
   SETTINGS
   ══════════════════════════════════════════════════════ */

const SETTINGS_KEY = "mailforge_settings";

let settings = loadSettings();

function loadSettings() {
  try {
    return JSON.parse(sessionStorage.getItem(SETTINGS_KEY)) || {};
  } catch { return {}; }
}

function saveSettings() {
  settings = {
    company_name:        _val("settingsCompanyName"),
    founder_name:        _val("settingsFounderName"),
    company_description: _val("settingsCompanyDesc"),
    portfolio_link_1:    _val("settingsPortfolioLink1"),
    portfolio_link_2:    _val("settingsPortfolioLink2"),
  };
  sessionStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  showToast("✓ Settings saved");
}

function restoreSettingsForm() {
  _set("settingsCompanyName",    settings.company_name);
  _set("settingsFounderName",    settings.founder_name);
  _set("settingsCompanyDesc",    settings.company_description);
  _set("settingsPortfolioLink1", settings.portfolio_link_1);
  _set("settingsPortfolioLink2", settings.portfolio_link_2);
}

/* ══════════════════════════════════════════════════════
   GENERATE FLOW
   ══════════════════════════════════════════════════════ */

async function generateEmail() {
  const url = _val("urlInput");

  if (!url) { showError("Please enter a job listing URL."); return; }
  if (!/^https?:\/\/.+/.test(url)) { showError("URL must start with http:// or https://"); return; }

  clearError();
  _get("resultsSection").classList.add("d-none");
  _get("progressSection").classList.remove("d-none");
  _get("generateBtn").disabled = true;
  setProgress(10, "Sending request…");

  const body = {
    url,
    ...(settings.company_name        ? { company_name:        settings.company_name }        : {}),
    ...(settings.founder_name        ? { founder_name:        settings.founder_name }        : {}),
    ...(settings.company_description ? { company_description: settings.company_description } : {}),
    ...(settings.portfolio_link_1    ? { portfolio_link_1:    settings.portfolio_link_1 }    : {}),
    ...(settings.portfolio_link_2    ? { portfolio_link_2:    settings.portfolio_link_2 }    : {}),
  };

  const ticker = progressTicker([
    [22, "Scraping job page…"],
    [46, "Analysing job details…"],
    [68, "Matching portfolio…"],
    [82, "Writing email…"],
  ]);

  try {
    const res = await fetch(`${API_BASE}/api/generate`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(body),
    });

    clearInterval(ticker);

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      showError(err.detail || "Request failed. Check that the API server is running.");
      return;
    }

    const data = await res.json();
    setProgress(100, "Done!");
    await delay(500);
    _get("progressSection").classList.add("d-none");

    // Populate results
    _get("outRole").textContent        = data.job_details.role        || "N/A";
    _get("outExperience").textContent  = data.job_details.experience  || "N/A";
    _get("outDescription").textContent = data.job_details.description || "N/A";
    renderSkills(data.job_details.skills);
    renderLinks(data.portfolio_links);
    _get("outEmail").textContent = data.email;

    const section = _get("resultsSection");
    section.classList.remove("d-none");
    section.scrollIntoView({ behavior: "smooth", block: "start" });

  } catch (_) {
    clearInterval(ticker);
    _get("progressSection").classList.add("d-none");
    showError("Cannot reach the API server. Make sure it is running (run: python run.py)");
  } finally {
    _get("generateBtn").disabled = false;
  }
}

function progressTicker(steps) {
  let i = 0;
  return setInterval(() => {
    if (i < steps.length) { setProgress(...steps[i]); i++; }
  }, 900);
}

function setProgress(pct, label) {
  const bar = _get("progressBar");
  if (bar) bar.style.width = `${pct}%`;
  const lbl = _get("progressLabel");
  if (lbl && label) lbl.textContent = label;
}

function renderSkills(skills) {
  const wrap = _get("outSkills");
  wrap.innerHTML = "";
  (skills || []).forEach(s => {
    const pill = document.createElement("span");
    pill.className = "skill-pill";
    pill.textContent = s;
    wrap.appendChild(pill);
  });
}

function renderLinks(links) {
  const wrap = _get("outLinks");
  wrap.innerHTML = "";
  (links || []).forEach(href => {
    const a = document.createElement("a");
    a.href = href; a.target = "_blank"; a.rel = "noopener noreferrer";
    a.textContent = href;
    wrap.appendChild(a);
  });
}

/* ══════════════════════════════════════════════════════
   COPY / DOWNLOAD
   ══════════════════════════════════════════════════════ */

function copyEmail() {
  const text = _get("outEmail").textContent;
  navigator.clipboard.writeText(text).then(
    ()  => showToast("✓ Email copied to clipboard"),
    ()  => showToast("Copy failed — select text manually"),
  );
}

function downloadEmail() {
  const text = _get("outEmail").textContent;
  const a = Object.assign(document.createElement("a"), {
    href:     URL.createObjectURL(new Blob([text], { type: "text/plain" })),
    download: "cold_email.txt",
  });
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(a.href);
  showToast("✓ Email downloaded");
}

/* ══════════════════════════════════════════════════════
   UI HELPERS
   ══════════════════════════════════════════════════════ */

function showError(msg) {
  _get("errorMessage").textContent = msg;
  _get("errorSection").classList.remove("d-none");
  _get("resultsSection").classList.add("d-none");
  _get("progressSection").classList.add("d-none");
}

function clearError() {
  _get("errorSection").classList.add("d-none");
}

let _toastTimer = null;

function showToast(msg) {
  const el = _get("toastMessage");
  if (!el) return;

  // Clear running exit animation
  el.classList.remove("toast-exit", "d-none");
  el.textContent = msg;

  if (_toastTimer) clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => {
    el.classList.add("toast-exit");
    setTimeout(() => el.classList.add("d-none"), 260);
  }, 2800);
}

/* ══════════════════════════════════════════════════════
   API STATUS CHECKER
   ══════════════════════════════════════════════════════ */

async function checkApiStatus() {
  const el = _get("apiStatus");
  if (!el) return;

  const label = el.querySelector(".status-label");
  el.className = "api-status checking";
  if (label) label.textContent = "Checking…";

  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(4000) });
    if (res.ok) {
      el.className = "api-status online";
      if (label) label.textContent = "API online";
    } else {
      throw new Error("non-ok");
    }
  } catch {
    el.className = "api-status offline";
    if (label) label.textContent = "API offline";
  }
}

/* ══════════════════════════════════════════════════════
   MICRO-INTERACTIONS
   ══════════════════════════════════════════════════════ */

function initMicroInteractions() {
  // Button press ripple feel
  document.querySelectorAll(".btn-forge, .btn-ghost").forEach(btn => {
    btn.addEventListener("mousedown", function(e) {
      this.style.transform = "scale(0.97)";
    });
    btn.addEventListener("mouseup mouseleave", function() {
      this.style.transform = "";
    });
  });

  // Input label lift on focus
  document.querySelectorAll(".field-input, .url-input").forEach(input => {
    input.addEventListener("focus",  () => input.closest(".field-group, .forge-card__body")?.classList.add("field-focused"));
    input.addEventListener("blur",   () => input.closest(".field-group, .forge-card__body")?.classList.remove("field-focused"));
  });
}

/* ══════════════════════════════════════════════════════
   UTILS
   ══════════════════════════════════════════════════════ */

const _get = id => document.getElementById(id);
const _val = id => (_get(id)?.value || "").trim();
const _set = (id, v) => { const el = _get(id); if (el) el.value = v || ""; };
const delay = ms => new Promise(r => setTimeout(r, ms));

/* ══════════════════════════════════════════════════════
   BOOT
   ══════════════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", () => {
  // Router
  const router = new Router();
  router.init();

  // Restore settings form
  restoreSettingsForm();

  // Wire events
  _get("generateBtn")   ?.addEventListener("click", generateEmail);
  _get("saveSettingsBtn")?.addEventListener("click", saveSettings);
  _get("copyEmailBtn")  ?.addEventListener("click", copyEmail);
  _get("downloadEmailBtn")?.addEventListener("click", downloadEmail);

  _get("urlInput")?.addEventListener("keydown", e => {
    if (e.key === "Enter") generateEmail();
  });

  // API health check — immediately + every 30s
  checkApiStatus();
  setInterval(checkApiStatus, 30_000);

  // Micro-interactions
  initMicroInteractions();
});
