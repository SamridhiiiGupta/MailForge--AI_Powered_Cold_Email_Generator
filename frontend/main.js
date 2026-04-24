/**
 * MailForge — Frontend
 * Calls the FastAPI backend at /api/generate.
 * No hardcoded company names. No Streamlit redirects. No mock data.
 */

const API_BASE = "http://localhost:8000";

// ── DOM references ────────────────────────────────────────────────────────────

const urlInput        = document.getElementById("urlInput");
const generateBtn     = document.getElementById("generateBtn");
const progressSection = document.getElementById("progressSection");
const progressBar     = document.getElementById("progressBar");
const progressLabel   = document.getElementById("progressLabel");
const resultsSection  = document.getElementById("resultsSection");
const errorSection    = document.getElementById("errorSection");
const errorMessage    = document.getElementById("errorMessage");

// Results fields
const outRole        = document.getElementById("outRole");
const outExperience  = document.getElementById("outExperience");
const outSkills      = document.getElementById("outSkills");
const outDescription = document.getElementById("outDescription");
const outLinks       = document.getElementById("outLinks");
const outEmail       = document.getElementById("outEmail");

// Settings
const settingsCompanyName    = document.getElementById("settingsCompanyName");
const settingsFounderName    = document.getElementById("settingsFounderName");
const settingsCompanyDesc    = document.getElementById("settingsCompanyDesc");
const settingsPortfolioLink1 = document.getElementById("settingsPortfolioLink1");
const settingsPortfolioLink2 = document.getElementById("settingsPortfolioLink2");
const saveSettingsBtn        = document.getElementById("saveSettingsBtn");

// Action buttons
const copyEmailBtn     = document.getElementById("copyEmailBtn");
const downloadEmailBtn = document.getElementById("downloadEmailBtn");

// ── State ──────────────────────────────────────────────────────────────────────

let settings = loadSettings();

// ── Settings persistence ──────────────────────────────────────────────────────

function loadSettings() {
  const raw = sessionStorage.getItem("gmg_settings");
  return raw
    ? JSON.parse(raw)
    : { company_name: "", founder_name: "", company_description: "", portfolio_link_1: "", portfolio_link_2: "" };
}

function saveSettings() {
  settings = {
    company_name:        settingsCompanyName.value.trim(),
    founder_name:        settingsFounderName.value.trim(),
    company_description: settingsCompanyDesc.value.trim(),
    portfolio_link_1:    settingsPortfolioLink1.value.trim(),
    portfolio_link_2:    settingsPortfolioLink2.value.trim(),
  };
  sessionStorage.setItem("gmg_settings", JSON.stringify(settings));
  showToast("Settings saved.");
}

function restoreSettingsForm() {
  settingsCompanyName.value    = settings.company_name    || "";
  settingsFounderName.value    = settings.founder_name    || "";
  settingsCompanyDesc.value    = settings.company_description || "";
  settingsPortfolioLink1.value = settings.portfolio_link_1 || "";
  settingsPortfolioLink2.value = settings.portfolio_link_2 || "";
}

// ── UI helpers ────────────────────────────────────────────────────────────────

function setProgress(pct, label) {
  progressBar.style.width   = `${pct}%`;
  progressBar.setAttribute("aria-valuenow", pct);
  if (label && progressLabel) progressLabel.textContent = label;
}

function showError(message) {
  errorMessage.textContent = message;
  errorSection.classList.remove("d-none");
  resultsSection.classList.add("d-none");
}

function clearError() {
  errorSection.classList.add("d-none");
}

function showToast(message) {
  // Simple status message — replace with a toast library if desired
  const el = document.getElementById("toastMessage");
  if (!el) return;
  el.textContent = message;
  el.classList.remove("d-none");
  setTimeout(() => el.classList.add("d-none"), 3000);
}

function renderSkills(skills) {
  outSkills.innerHTML = "";
  (skills || []).forEach(skill => {
    const badge = document.createElement("span");
    badge.className = "badge bg-primary me-1 mb-1";
    badge.textContent = skill;
    outSkills.appendChild(badge);
  });
}

function renderLinks(links) {
  outLinks.innerHTML = "";
  (links || []).forEach(link => {
    const a = document.createElement("a");
    a.href        = link;
    a.target      = "_blank";
    a.rel         = "noopener noreferrer";
    a.textContent = link;
    a.className   = "d-block text-truncate mb-1";
    outLinks.appendChild(a);
  });
}

// ── Core generate flow ────────────────────────────────────────────────────────

async function generateEmail() {
  const url = urlInput.value.trim();

  if (!url) {
    showError("Please enter a job listing URL.");
    return;
  }
  if (!/^https?:\/\/.+/.test(url)) {
    showError("URL must start with http:// or https://");
    return;
  }

  // Reset UI
  clearError();
  resultsSection.classList.add("d-none");
  progressSection.classList.remove("d-none");
  generateBtn.disabled = true;
  setProgress(10, "Sending request…");

  const body = {
    url,
    ...settings.company_name    ? { company_name:        settings.company_name }        : {},
    ...settings.founder_name    ? { founder_name:        settings.founder_name }        : {},
    ...settings.company_description ? { company_description: settings.company_description } : {},
    ...settings.portfolio_link_1 ? { portfolio_link_1:   settings.portfolio_link_1 }    : {},
    ...settings.portfolio_link_2 ? { portfolio_link_2:   settings.portfolio_link_2 }    : {},
  };

  // Fake progress ticks while waiting (real progress lives server-side)
  const fakeProgress = fakeProgressTicks([
    [20, "Scraping job page…"],
    [45, "Analysing job details…"],
    [65, "Matching portfolio…"],
    [80, "Writing email…"],
  ]);

  try {
    const response = await fetch(`${API_BASE}/api/generate`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(body),
    });

    clearInterval(fakeProgress);

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }));
      showError(err.detail || "Request failed. Check that the API server is running.");
      return;
    }

    const data = await response.json();

    setProgress(100, "Done!");
    setTimeout(() => progressSection.classList.add("d-none"), 600);

    // Populate results
    outRole.textContent        = data.job_details.role        || "N/A";
    outExperience.textContent  = data.job_details.experience  || "N/A";
    outDescription.textContent = data.job_details.description || "N/A";
    renderSkills(data.job_details.skills);
    renderLinks(data.portfolio_links);
    outEmail.textContent = data.email;

    resultsSection.classList.remove("d-none");
    resultsSection.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    clearInterval(fakeProgress);
    progressSection.classList.add("d-none");
    showError(
      "Cannot reach the API server. Make sure it is running on port 8000 " +
      "(run: python -m app.api)"
    );
  } finally {
    generateBtn.disabled = false;
  }
}

function fakeProgressTicks(steps) {
  let i = 0;
  return setInterval(() => {
    if (i < steps.length) {
      setProgress(...steps[i]);
      i++;
    }
  }, 900);
}

// ── Copy / Download ───────────────────────────────────────────────────────────

copyEmailBtn.addEventListener("click", () => {
  navigator.clipboard.writeText(outEmail.textContent).then(
    ()  => showToast("Email copied to clipboard!"),
    ()  => showToast("Copy failed — please select and copy manually."),
  );
});

downloadEmailBtn.addEventListener("click", () => {
  const blob = new Blob([outEmail.textContent], { type: "text/plain" });
  const a    = Object.assign(document.createElement("a"), {
    href:     URL.createObjectURL(blob),
    download: "cold_email.txt",
  });
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(a.href);
  showToast("Email downloaded.");
});

// ── Events ────────────────────────────────────────────────────────────────────

generateBtn.addEventListener("click", generateEmail);
saveSettingsBtn.addEventListener("click", saveSettings);

urlInput.addEventListener("keydown", e => {
  if (e.key === "Enter") generateEmail();
});

// ── Init ──────────────────────────────────────────────────────────────────────

restoreSettingsForm();
