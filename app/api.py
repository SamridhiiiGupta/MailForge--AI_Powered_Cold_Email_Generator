"""
FastAPI backend for the MailForge.
This is the single API layer that the frontend calls — no more Streamlit redirects.
"""

from __future__ import annotations

from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, field_validator

from app.config import API_HOST, API_PORT, ENV
from app.services.llm_service import LLMService
from app.services.portfolio_service import PortfolioService
from app.services.scraper import ScraperError, scrape_url
from app.utils.logger import get_logger
from app.utils.text_cleaner import clean_text, truncate

logger = get_logger(__name__)

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="MailForge: AI-Powered Cold Email Generator",
    description="MailForge: AI-Powered Cold Email Generator. Paste a job URL, get a personalised cold email in seconds.",
    version="1.0.0",
    docs_url="/docs" if ENV != "production" else None,   # Hide Swagger in prod
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ── Service singletons ────────────────────────────────────────────────────────
# Instantiated once at startup — safe because they hold no mutable request state.
_llm = LLMService()
_portfolio = PortfolioService()


# ── Schemas ───────────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    url: HttpUrl
    company_name: Optional[str] = None
    founder_name: Optional[str] = None
    company_description: Optional[str] = None
    portfolio_link_1: Optional[str] = None
    portfolio_link_2: Optional[str] = None

    @field_validator("url", mode="before")
    @classmethod
    def _url_must_be_http(cls, v: str) -> str:
        if not str(v).startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class JobDetails(BaseModel):
    role: str
    experience: str
    skills: list[str]
    description: str


class GenerateResponse(BaseModel):
    email: str
    job_details: JobDetails
    portfolio_links: list[str]


# ── Centralised error handler ─────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler so unhandled exceptions never leak stack traces to clients.
    In development the detail is included; in production it is hidden.
    """
    logger.error("Unhandled exception | path=%s | error=%s", request.url.path, exc, exc_info=True)
    detail = str(exc) if ENV == "development" else "An unexpected error occurred."
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail},
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Infra"])
async def health_check():
    """Liveness probe."""
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/generate", response_model=GenerateResponse, tags=["Email"])
async def generate_email(payload: GenerateRequest):
    """
    Main endpoint: scrape a job URL → extract job details → generate cold email.

    Steps:
      1. Scrape the URL.
      2. Clean and truncate the raw HTML.
      3. Extract structured job info via LLM.
      4. Match portfolio links.
      5. Generate the cold email.
    """
    url = str(payload.url)
    logger.info("Generate request received | url=%s", url)

    # 1. Scrape
    try:
        raw_html = scrape_url(url)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except ScraperError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    # 2. Clean
    cleaned = truncate(clean_text(raw_html))

    # 3. Extract jobs
    jobs = _llm.extract_jobs(cleaned)
    if not jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No job details could be extracted from the provided URL.",
        )
    job = jobs[0]

    # 4. Portfolio links
    override = [
        lnk
        for lnk in [payload.portfolio_link_1, payload.portfolio_link_2]
        if lnk
    ]
    links = _portfolio.query_links(job.get("skills", []), override_links=override or None)

    # 5. Email — fall back to config defaults if not supplied in request
    from app.config import COMPANY_DESCRIPTION, COMPANY_NAME, FOUNDER_NAME

    email = _llm.write_email(
        job=job,
        portfolio_links=links,
        company_name=payload.company_name or COMPANY_NAME,
        founder_name=payload.founder_name or FOUNDER_NAME,
        company_description=payload.company_description or COMPANY_DESCRIPTION,
    )

    return GenerateResponse(
        email=email,
        job_details=JobDetails(
            role=job.get("role", "N/A"),
            experience=job.get("experience", "N/A"),
            skills=job.get("skills", []),
            description=job.get("description", "N/A"),
        ),
        portfolio_links=links,
    )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "app.api:app",
        host=API_HOST,
        port=API_PORT,
        reload=(ENV == "development"),
        log_level="info",
    )
