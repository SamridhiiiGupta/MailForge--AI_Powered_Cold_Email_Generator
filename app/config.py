"""
Centralized configuration module.
All settings are read from environment variables (via .env file).
No hardcoded secrets or environment-specific values anywhere else.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    """Raise a clear error if a required env variable is missing."""
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

# ── Company (used in email generation) ───────────────────────────────────────
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
API_PORT: int = int(os.getenv("API_PORT", "8000"))
FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "8080"))

# ── App Behaviour ─────────────────────────────────────────────────────────────
ENV: str = os.getenv("ENV", "development")           # "development" | "production"
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
SCRAPE_TIMEOUT: int = int(os.getenv("SCRAPE_TIMEOUT", "15"))
