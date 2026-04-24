"""
Streamlit UI for MailForge.
This is the primary interactive interface.
All business logic lives in services — this file handles UI only.
"""

import streamlit as st

from app.config import (
    COMPANY_DESCRIPTION,
    COMPANY_NAME,
    FOUNDER_NAME,
    PORTFOLIO_LINK_1,
    PORTFOLIO_LINK_2,
)
from app.services.llm_service import LLMService
from app.services.portfolio_service import PortfolioService
from app.services.scraper import ScraperError, scrape_url
from app.utils.logger import get_logger
from app.utils.text_cleaner import clean_text, truncate

logger = get_logger(__name__)

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    layout="wide",
    page_title="MailForge: AI-Powered Cold Email Generator",
    page_icon="✉️",
)

# ── Service singletons (cached across Streamlit reruns) ───────────────────────

@st.cache_resource
def get_llm_service() -> LLMService:
    return LLMService()


@st.cache_resource
def get_portfolio_service() -> PortfolioService:
    svc = PortfolioService()
    svc.load()
    return svc


# ── Session-state defaults ────────────────────────────────────────────────────

_DEFAULTS = {
    "company_name": COMPANY_NAME,
    "founder_name": FOUNDER_NAME,
    "company_description": COMPANY_DESCRIPTION,
    "portfolio_link_1": PORTFOLIO_LINK_1,
    "portfolio_link_2": PORTFOLIO_LINK_2,
}

for key, value in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ── Helpers ───────────────────────────────────────────────────────────────────

def _show_error(message: str) -> None:
    st.error(f"⚠️ {message}")


def _generate_email(url: str) -> None:
    """Orchestrate the full generation pipeline with progress feedback."""
    llm = get_llm_service()
    portfolio = get_portfolio_service()

    progress = st.progress(0, text="Scraping job page…")

    try:
        raw_html = scrape_url(url)
        progress.progress(30, text="Cleaning content…")
    except ValueError as exc:
        _show_error(str(exc))
        return
    except ScraperError as exc:
        _show_error(str(exc))
        return
    except Exception as exc:
        logger.error("Unexpected scrape error | error=%s", exc, exc_info=True)
        _show_error("Something went wrong while loading the page. Please try again.")
        return

    cleaned = truncate(clean_text(raw_html))
    progress.progress(55, text="Analysing job details…")

    try:
        jobs = llm.extract_jobs(cleaned)
    except Exception as exc:
        logger.error("Job extraction failed | error=%s", exc, exc_info=True)
        _show_error("Failed to extract job details. The page may not contain a job listing.")
        return

    if not jobs:
        _show_error("No job details found at this URL.")
        return

    job = jobs[0]
    progress.progress(70, text="Matching portfolio…")

    overrides = [
        lnk for lnk in [
            st.session_state["portfolio_link_1"],
            st.session_state["portfolio_link_2"],
        ] if lnk.strip()
    ]
    links = portfolio.query_links(job.get("skills", []), override_links=overrides or None)

    progress.progress(85, text="Writing email…")

    try:
        email = llm.write_email(
            job=job,
            portfolio_links=links,
            company_name=st.session_state["company_name"],
            founder_name=st.session_state["founder_name"],
            company_description=st.session_state["company_description"],
        )
    except Exception as exc:
        logger.error("Email generation failed | error=%s", exc, exc_info=True)
        _show_error("Email generation failed. Check your API key and try again.")
        return

    progress.progress(100, text="Done!")

    # ── Display results ───────────────────────────────────────────────────────

    with st.expander("📋 Extracted Job Details", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**Role:** {job.get('role', 'N/A')}")
            st.markdown(f"**Experience:** {job.get('experience', 'N/A')}")
        with col_b:
            skills = job.get("skills", [])
            st.markdown(f"**Skills:** {', '.join(skills) if skills else 'N/A'}")

        st.markdown(f"**Description:** {job.get('description', 'N/A')}")

    st.subheader("✉️ Generated Cold Email")
    st.code(email, language="markdown")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="⬇️ Download Email",
            data=email,
            file_name="cold_email.txt",
            mime="text/plain",
        )
    with col2:
        st.markdown("**Portfolio links used:**")
        for lnk in links:
            st.markdown(f"• [{lnk}]({lnk})")


# ── UI Layout ─────────────────────────────────────────────────────────────────

st.title("✉️ MailForge: AI-Powered Cold Email Generator")
st.caption("Paste a job listing URL. Get a personalised cold email. Powered by LLaMA 3.1 via Groq.")

tab_generate, tab_settings, tab_help = st.tabs(["Generate", "Company Settings", "Help"])

# ── Tab 1: Generate ───────────────────────────────────────────────────────────
with tab_generate:
    url_input = st.text_input(
        "Job listing URL",
        placeholder="https://jobs.example.com/software-engineer-123",
    )
    if st.button("Generate Cold Email", type="primary"):
        if not url_input.strip():
            _show_error("Please enter a URL before generating.")
        else:
            _generate_email(url_input.strip())

# ── Tab 2: Company Settings ───────────────────────────────────────────────────
with tab_settings:
    st.subheader("🏢 Company Settings")
    st.caption("These values are used in every generated email. Changes apply immediately.")

    with st.form("settings_form"):
        c1, c2 = st.columns(2)
        with c1:
            company_name = st.text_input("Company Name", value=st.session_state["company_name"])
            founder_name = st.text_input("Your Name", value=st.session_state["founder_name"])
        with c2:
            company_description = st.text_area(
                "Company Description (one sentence)",
                value=st.session_state["company_description"],
                height=80,
            )
            portfolio_link_1 = st.text_input(
                "Portfolio Link 1 (optional)", value=st.session_state["portfolio_link_1"]
            )
            portfolio_link_2 = st.text_input(
                "Portfolio Link 2 (optional)", value=st.session_state["portfolio_link_2"]
            )

        if st.form_submit_button("Save Settings"):
            st.session_state.update(
                {
                    "company_name": company_name,
                    "founder_name": founder_name,
                    "company_description": company_description,
                    "portfolio_link_1": portfolio_link_1,
                    "portfolio_link_2": portfolio_link_2,
                }
            )
            st.success("✅ Settings saved.")

# ── Tab 3: Help ───────────────────────────────────────────────────────────────
with tab_help:
    st.subheader("How to use")
    st.markdown(
        """
        1. **Set up your company** in the *Company Settings* tab.
        2. **Paste a job listing URL** into the *Generate* tab.
        3. Click **Generate Cold Email** — the app will:
           - Scrape the page
           - Extract the job role, skills, and requirements
           - Match the most relevant items from your portfolio
           - Write a personalised cold email using an LLM
        4. **Copy or download** the generated email.

        ---

        ### Troubleshooting
        | Problem | Fix |
        |---|---|
        | URL fails to load | Try a direct link to the job page (not a search results page) |
        | No skills detected | The job page may use JavaScript — try a different URL |
        | API error | Check that `GROQ_API_KEY` is set correctly in `.env` |
        | Wrong portfolio links | Set Portfolio Link 1/2 in *Company Settings* |
        """
    )
