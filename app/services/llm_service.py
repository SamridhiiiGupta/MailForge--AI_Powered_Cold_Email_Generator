"""
LLM service: job extraction and cold email generation.
All model parameters (name, temperature) come from config — zero hardcoding.
"""

from typing import Any

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from app.config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMService:
    """Wraps all LLM interactions: job extraction and email writing."""

    def __init__(self) -> None:
        self._llm = ChatGroq(
            temperature=LLM_TEMPERATURE,
            groq_api_key=GROQ_API_KEY,
            model_name=LLM_MODEL,
        )
        logger.info("LLMService initialised | model=%s temperature=%s", LLM_MODEL, LLM_TEMPERATURE)

    # ── Job Extraction ────────────────────────────────────────────────────────

    _EXTRACT_PROMPT = PromptTemplate.from_template(
        """
        ### SCRAPED TEXT FROM WEBSITE:
        {page_data}

        ### INSTRUCTION:
        The scraped text is from a job listing page.
        Extract and return ONLY a valid JSON object (no preamble, no markdown fences) with:
          - "role"        : job title (string)
          - "experience"  : experience requirements (string, "Not specified" if absent)
          - "skills"      : list of required skills/technologies (array of strings)
          - "description" : concise job summary (string)

        ### VALID JSON ONLY:
        """
    )

    def extract_jobs(self, cleaned_text: str) -> list[dict[str, Any]]:
        """
        Extract structured job details from cleaned page text.

        Args:
            cleaned_text: Pre-cleaned text from the scraped page.

        Returns:
            List of job dicts. Typically one item; always at least a fallback dict.
        """
        logger.debug("Extracting job details from text (len=%d)", len(cleaned_text))
        chain = self._EXTRACT_PROMPT | self._llm

        try:
            raw = chain.invoke({"page_data": cleaned_text})
            result = JsonOutputParser().parse(raw.content)
            jobs = result if isinstance(result, list) else [result]
            logger.info("Extracted %d job(s)", len(jobs))
            return jobs
        except OutputParserException as exc:
            logger.warning("JSON parse failed, using fallback | error=%s", exc)
            return [self._fallback_job(cleaned_text)]
        except Exception as exc:
            logger.error("Job extraction failed | error=%s", exc)
            raise

    @staticmethod
    def _fallback_job(text: str) -> dict[str, Any]:
        """Best-effort fallback when LLM output cannot be parsed."""
        role = "Job Position"
        for keyword in ("Data Engineer", "Software Engineer", "Developer", "Analyst", "Manager"):
            if keyword.lower() in text.lower():
                role = keyword
                break
        return {
            "role": role,
            "experience": "Not specified",
            "skills": [],
            "description": text[:500].strip() + "…",
        }

    # ── Email Generation ──────────────────────────────────────────────────────

    _EMAIL_PROMPT = PromptTemplate.from_template(
        """
        ### JOB DESCRIPTION:
        {job_description}

        ### INSTRUCTION:
        You are {founder_name}, a Business Development Executive at {company_name}.
        {company_name} is {company_description}, dedicated to facilitating the seamless
        integration of business processes through automated tools.

        Write a concise, professional cold email to the hiring company about the job above,
        explaining how {company_name} can fulfil their needs.

        Include the most relevant portfolio links from this list (max 2): {link_list}

        Tone: confident, specific, and human — not generic.
        Do NOT include a preamble or subject line unless it improves the email.

        ### EMAIL:
        """
    )

    def write_email(
        self,
        job: dict[str, Any],
        portfolio_links: list[str],
        company_name: str,
        founder_name: str,
        company_description: str,
    ) -> str:
        """
        Generate a cold email for the given job and portfolio links.

        Args:
            job: Extracted job dict (role, skills, experience, description).
            portfolio_links: Relevant portfolio URLs to reference in the email.
            company_name: Sender's company name.
            founder_name: Sender's name / BDE name.
            company_description: One-liner describing the company.

        Returns:
            Generated email as plain text.
        """
        logger.debug("Generating email | job_role=%s", job.get("role"))
        chain = self._EMAIL_PROMPT | self._llm
        result = chain.invoke(
            {
                "job_description": str(job),
                "link_list": portfolio_links or ["No portfolio links available"],
                "company_name": company_name,
                "founder_name": founder_name,
                "company_description": company_description,
            }
        )
        logger.info("Email generated successfully | job_role=%s", job.get("role"))
        return result.content
