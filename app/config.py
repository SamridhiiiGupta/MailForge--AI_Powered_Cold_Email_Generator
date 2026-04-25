"""
Centralized configuration module.
All settings are read from environment variables (via .env file).
No hardcoded secrets or environment-specific values anywhere else.

DEPLOYMENT NOTE:
  - Render sets PORT automatically — this config reads it.
  - Set ALLOWED_ORIGINS to your Vercel URL after deploying the frontend.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Missing required environment variable: '{key}'. "
            f"Check your .env file against .env.example."
        )
    return value


# ── LLM ──────────────────────────────────────────────────────────────────────
GROQ_API_KEY: str = _require("GROQ_API_KEY")
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0"))

# ── Company ───────────────────────────────────────────────────────────────────
COMPANY_NAME: str = os.getenv("COMPANY_NAME", "Your Company Name")
FOUNDER_NAME: str = os.getenv("FOUNDER_NAME", "Your Name")
COMPANY_DESCRIPTION: str = os.getenv(
    "COMPANY_DESCRIPTION", "a leading technology consulting company"
)

# ── Portfolio ─────────────────────────────────────────────────────────────────
PORTFOLIO_FILE: str = os.getenv("PORTFOLIO_FILE", "data/portfolio.csv")
PORTFOLIO_LINK_1: str = os.getenv("PORTFOLIO_LINK_1", "")
PORTFOLIO_LINK_2: str = os.getenv("PORTFOLIO_LINK_2", "")
MAX_PORTFOLIO_LINKS: int = int(os.getenv("MAX_PORTFOLIO_LINKS", "2"))

# ── Server ────────────────────────────────────────────────────────────────────
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
# Render sets PORT; fall back to API_PORT for local dev
API_PORT: int = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))
FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "8080"))

# ── CORS ─────────────────────────────────────────────────────────────────────
# Comma-separated list of allowed origins.
# In production, set this to your Vercel URL, e.g.:
#   ALLOWED_ORIGINS=https://mailforge.vercel.app,https://mailforge-xyz.vercel.app
ALLOWED_ORIGINS: list[str] = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8080,http://127.0.0.1:8080,http://localhost:3000"
    ).split(",")
    if o.strip()
]

# ── App Behaviour ─────────────────────────────────────────────────────────────
ENV: str = os.getenv("ENV", "development")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
SCRAPE_TIMEOUT: int = int(os.getenv("SCRAPE_TIMEOUT", "15"))
