# BugHunterLab

**Professional Bug Bounty & VAPT Platform** — Scope → Recon → Testing → PoC → Evidence → Report

---

## Quick Start (Docker — Recommended)

```bash
# 1. Clone the project (if not already)
cd /home/vishal/Desktop/projects/BugHunterLab

# 2. Build all containers
docker compose build --no-cache

# 3. Start everything
docker compose up -d

# 4. Check all services are healthy
docker compose ps
```

### Services after startup

| Service | URL | Purpose |
|---|---|---|
| **Frontend** | http://localhost:3000 | Next.js UI |
| **API** | http://localhost:8000 | FastAPI backend |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Flower** | http://localhost:5555 | Celery task monitor |
| **PostgreSQL** | localhost:5432 | Database |
| **Redis** | localhost:6379 | Task queue + pub/sub |

---

## Feature Walkthrough

### 1. Scope Analyzer
- Go to **Scope Analyzer** in the UI
- Enter program name and domain(s)
- Scores attack surface difficulty (beginner / intermediate / expert)

**API:**
```bash
curl -X POST http://localhost:8000/api/scope \
  -H "Content-Type: application/json" \
  -d '{"program_name":"HackerOne","scope_text":"hackerone.com","domains":["hackerone.com","api.hackerone.com"]}'
```

---

### 2. Recon (subfinder → httpx → DB)
- Click **Run Recon** on a scope target
- Pipeline: subfinder finds subdomains → httpx checks live hosts + tech detection → results saved to DB

**API:**
```bash
# Start recon (replace 1 with your target ID)
curl -X POST http://localhost:8000/api/recon/1

# View discovered assets
curl http://localhost:8000/api/recon/1
```

Live logs stream via WebSocket: `ws://localhost:8000/ws/logs/1`

---

### 3. Attack Surface Map
- Auto-populated after recon runs
- Shows subdomains, live hosts, and detected technologies

---

### 4. Bug Testing Guide / Checklists
- Per-endpoint checklists (GET/POST/PUT/DELETE/FILE)
- Based on HTTP method and target features

**API:**
```bash
curl "http://localhost:8000/api/checklists?target_id=1"
```

---

### 5. Findings
- Create a finding with title, severity, vulnerability class, description
- Supported severities: `low`, `medium`, `high`, `critical`

**API:**
```bash
curl -X POST http://localhost:8000/api/findings \
  -H "Content-Type: application/json" \
  -d '{
    "target_id": 1,
    "title": "IDOR on /api/users/{id}",
    "vulnerability_class": "IDOR",
    "severity": "high",
    "description": "Can access other users data by changing the ID in the URL"
  }'
```

---

### 6. Evidence Manager
- Upload screenshots, logs, HTTP dumps
- Max 20 MB per file

**API:**
```bash
# Upload screenshot
curl -X POST http://localhost:8000/api/evidence/1 \
  -F "file=@/path/to/screenshot.png"

# List files
curl http://localhost:8000/api/evidence/1

# Download
curl -O http://localhost:8000/api/evidence/1/filename.png
```

---

### 7. PoC Generator
- Generates cURL, Python, or Burp Suite PoC from a finding

**API:**
```bash
curl -X POST http://localhost:8000/api/poc \
  -H "Content-Type: application/json" \
  -d '{"finding_id": 1, "poc_type": "curl"}'
```

---

### 8. Report Builder
- Generates styled markdown + PDF report

**API:**
```bash
# Get report markdown
curl http://localhost:8000/api/report/1

# Download PDF
curl -O http://localhost:8000/api/report/1/pdf
```

---

### 9. Auto Scanner
- Select tool (subfinder, httpx, nuclei, nmap, ffuf, gau, katana)
- Add optional CLI args
- Live logs stream via WebSocket

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `docker compose up` fails with "cannot connect to docker" | Start Docker: `sudo systemctl start docker` |
| API container keeps restarting | `docker compose logs api` — check Python import errors |
| Worker shows no tasks | Check `docker compose logs worker` — ensure redis is healthy |
| Frontend shows "Failed to load dashboard" | Wait 10s for API to be ready, then refresh |
| PDF download returns HTML | WeasyPrint not installed — rebuild: `docker compose build api --no-cache` |
| Recon returns no results | subfinder/httpx not installed in container — check worker Dockerfile |

## Reset Everything

```bash
docker compose down -v  # removes all containers AND volumes (DB reset)
docker compose up -d
```