# BugHunterLab Architecture

## Core layers

1. User Interface Layer: Next.js dashboard, analyzers, evidence views, and report builder.
2. Recon and Asset Discovery Layer: Local wrappers for subfinder, amass, httpx, nmap, ffuf, nuclei, and sqlmap.
3. Vulnerability Intelligence Layer: Structured vulnerability knowledge base and payload sets.
4. Testing Methodology Engine: Endpoint-aware checklist generation and phase-based workflow guidance.
5. Evidence and PoC Management: Finding records, screenshots metadata, request/response storage, and PoC output.
6. Report Generation System: Markdown and plain-text exporter with bug bounty report sections.
7. Local AI Assistant: API-backed recommendations surfaced in the frontend workflow.