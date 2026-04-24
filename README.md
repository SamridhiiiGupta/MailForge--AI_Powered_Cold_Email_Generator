# ✉️ MailForge: AI-Powered Cold Email Generator

> Paste a job listing URL → get a personalised cold email in seconds.  
> Powered by **Groq (LLaMA 3.1)**, **LangChain**, **FastAPI**, and **Streamlit**.

---

## How it works

```
Job URL → Scrape → Clean → LLM extracts job details
                                  ↓
                      Match portfolio by skills
                                  ↓
                      LLM writes cold email → You
```

---

## Folder structure

```
mailforge/
├── app/
│   ├── config.py              # All settings — reads from .env
│   ├── api.py                 # FastAPI backend
│   ├── main.py                # Streamlit UI
│   ├── services/
│   │   ├── scraper.py         # Web scraping (3-strategy fallback)
│   │   ├── llm_service.py     # Job extraction + email generation
│   │   └── portfolio_service.py
│   └── utils/
│       ├── text_cleaner.py    # HTML → plain text
│       └── logger.py          # Structured logging
├── frontend/
│   ├── index.html             # Web UI
│   ├── main.js                # Calls FastAPI backend
│   └── styles.css
├── tests/                     # Pytest unit tests
├── data/
│   └── portfolio.csv          # Your portfolio (edit this!)
├── .env.example               # Environment variable template
├── run.py                     # Dev launcher
└── requirements.txt
```

---

## Quick start

### 1. Clone / download

```bash
git clone https://github.com/you/mailforge.git
cd mailforge
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in at minimum:

```env
GROQ_API_KEY=your_key_here      # https://console.groq.com/keys
COMPANY_NAME=Your Company
FOUNDER_NAME=Your Name
COMPANY_DESCRIPTION=a leading technology consulting company
```

### 5. Customise your portfolio

Edit `data/portfolio.csv` — replace the example URLs with links to your real projects:

```csv
Techstack,Links
"Python, Django, MySQL",https://github.com/you/real-project
"Machine Learning, Python, TensorFlow",https://your-ml-project.com
```

---

## Running the app

### Option A — Streamlit (recommended for quick use)

```bash
streamlit run app/main.py
```

Opens at **http://localhost:8501**

### Option B — Web UI + FastAPI (for sharing / embedding)

```bash
python run.py
```

- API → **http://localhost:8000**
- Frontend → **http://localhost:8080**
- API docs → **http://localhost:8000/docs** (development only)

### Option C — API only

```bash
python run.py --api-only
# or
python -m uvicorn app.api:app --reload
```

---

## Running tests

```bash
pytest
```

Expected output:

```
tests/test_text_cleaner.py      ........   8 passed
tests/test_portfolio_service.py .......    7 passed
```

With coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

---

## API reference

### `POST /api/generate`

**Request body:**

```json
{
  "url": "https://jobs.example.com/software-engineer-123",
  "company_name": "Your Company",       // optional — overrides .env
  "founder_name": "Your Name",          // optional
  "company_description": "a ...",       // optional
  "portfolio_link_1": "https://...",    // optional — overrides CSV matching
  "portfolio_link_2": "https://..."     // optional
}
```

**Response:**

```json
{
  "email": "Dear Hiring Manager, ...",
  "job_details": {
    "role": "Software Engineer",
    "experience": "3+ years",
    "skills": ["Python", "Django"],
    "description": "..."
  },
  "portfolio_links": ["https://example.com/python-portfolio"]
}
```

### `GET /health`

Returns `{ "status": "ok", "version": "1.0.0" }` — use for liveness checks.

---

## Environment variables reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ | — | Your Groq API key |
| `LLM_MODEL` | | `llama-3.1-8b-instant` | Groq model name |
| `LLM_TEMPERATURE` | | `0` | 0 = deterministic |
| `COMPANY_NAME` | | `Your Company Name` | Used in emails |
| `FOUNDER_NAME` | | `Your Name` | Used in emails |
| `COMPANY_DESCRIPTION` | | `a leading technology consulting company` | Used in emails |
| `PORTFOLIO_FILE` | | `data/portfolio.csv` | Path to portfolio CSV |
| `PORTFOLIO_LINK_1` | | _(empty)_ | Override portfolio link |
| `PORTFOLIO_LINK_2` | | _(empty)_ | Override portfolio link |
| `MAX_PORTFOLIO_LINKS` | | `2` | Max links per email |
| `ENV` | | `development` | `development` or `production` |
| `LOG_LEVEL` | | `INFO` | `DEBUG` / `INFO` / `WARNING` |
| `SCRAPE_TIMEOUT` | | `15` | Seconds per scrape attempt |
| `API_PORT` | | `8000` | FastAPI port |
| `FRONTEND_PORT` | | `8080` | Static frontend port |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `EnvironmentError: Missing required env var 'GROQ_API_KEY'` | Add key to `.env` |
| URL fails to load | Use a direct job-page link, not search results |
| `Cannot reach the API server` | Run `python run.py --api-only` first |
| No skills extracted | Page may need JavaScript — try a different URL |
| Wrong portfolio links | Set `PORTFOLIO_LINK_1/2` in `.env` or Settings tab |

---

## Security notes

- `.env` is in `.gitignore` — it will never be committed
- API keys are server-side only — never sent to the frontend
- CORS is restricted to `localhost:8080` (update for production)
- Swagger UI is disabled in `ENV=production`
- Input URLs are validated before scraping

---

## License

MIT — see `LICENSE`.
