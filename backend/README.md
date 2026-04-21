# BugHunterLab Backend

FastAPI service for local bug bounty workflow orchestration, recon ingestion, evidence tracking, PoC generation, and report generation.

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```