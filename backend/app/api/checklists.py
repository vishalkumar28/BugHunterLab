from fastapi import APIRouter

router = APIRouter()

CHECKLIST_TEMPLATES = {
    "RECON_GENERAL": [
        "Use subdomain enumeration tools like Sublist3r, Amass, and Subfinder",
        "Scan open ports with Nmap, Masscan, or Naabu",
        "Google Dork for exposed resources and sensitive files",
        "Perform DNS enumeration (dnsx, dnsrecon) and search wildcard DNS entries",
        "Check for exposed Git repos (.git), env files (.env), and robots.txt",
        "View old versions via Wayback Machine and analyze for hidden endpoints",
        "Spider directories with Burp Suite or Katana",
        "Analyze JavaScript for exposed endpoints and hardcoded secrets",
        "Fingerprint tech stacks (Wappalyzer, httpx)",
    ],
    "GET": [
        "Test for IDOR (BOLA) by replacing IDs with other users' IDs",
        "Check if response leaks PII or sensitive data",
        "Test for information disclosure in error messages (stack traces)",
        "Verify authentication is required and enforced properly",
        "Check caching headers (no-store for sensitive data) and test Cache Poisoning",
        "Test URL query strings for hidden parameters and HTTP Parameter Pollution (HPP)",
        "Test for reflected XSS in URL parameters",
        "Change HTTP method to POST/PUT/DELETE to test for Broken Function Level Authorization (BFLA)",
        "Test missing security headers and TLS/HTTPS enforcement",
    ],
    "POST": [
        "Test for SQL injection (UNION, Blind, Time-based) in body parameters",
        "Test for XSS (Stored, Reflected, DOM, Blind) in any input fields",
        "Check CSRF token presence, validation, and bypasses",
        "Test for Mass Assignment / Over-posting (e.g., is_admin: true)",
        "Verify rate limiting on sensitive actions and APIs",
        "Test for Server-Side Request Forgery (SSRF) in any URL parameters or webhooks",
        "Test for XXE vulnerabilities in XML parsing",
        "Test for Insecure Deserialization in JSON/YAML payloads",
        "Check for Server-Side Template Injection (SSTI)",
        "Test for Race Conditions (Time-of-Check to Time-of-Use) using concurrent requests",
        "Test for Business Logic flaws (e.g., negative pricing, skipping workflow steps)",
    ],
    "PUT": [
        "Test for IDOR — can you update another user's resource?",
        "Check for Mass Assignment vulnerabilities during updates",
        "Verify ownership checks on the target resource",
        "Test if partial updates bypass business logic validation",
        "Check for race conditions during resource modification",
    ],
    "DELETE": [
        "Test for IDOR — can you delete another user's resource?",
        "Check if soft-delete data remains accessible via direct references",
        "Verify admin-only endpoints require admin auth (BFLA)",
        "Test for race conditions during deletion",
    ],
    "FILE": [
        "Test for path traversal in file names (../../etc/passwd)",
        "Upload polyglot files (JPEG+PHP) and executable extensions (.php, .jsp, .aspx)",
        "Check content-type validation (bypass with MIME sniffing)",
        "Test for stored XSS via SVG upload",
        "Verify file size limits are enforced (DoS testing)",
        "Test for XXE via SVG or PDF parsing",
        "Check if uploaded files are executed by the server",
    ],
    "AUTH": [
        "Test broken authentication and weak password policies",
        "Test for username enumeration via response differences or timing",
        "Check lockout policy after N failed attempts",
        "Test cookie/session bypasses and session fixation",
        "Review JWT security (None algo, weak secret, kid manipulation, jku/jwk injection)",
        "Check session expiration and concurrent session management",
        "Test OAuth flows (open redirect in redirect_uri, missing state param, CSRF)",
        "Bruteforce responsibly where allowed",
    ],
    "CORS": [
        "Look for CORS misconfigurations (reflecting Origin, null Origin)",
        "Test weak regex in allowed origins (e.g., attacker-target.com)",
        "Check for pre-domain takeover if wildcard subdomains are allowed",
    ]
}


@router.get("")
def get_checklists(target_id: int = 1):
    """Return endpoint-specific checklists. Uses target_id for future customization."""
    return [
        {"endpoint": "Global Recon & OSINT", "method": "RECON", "checklist": CHECKLIST_TEMPLATES["RECON_GENERAL"]},
        {"endpoint": "/api/users/{id}", "method": "GET", "checklist": CHECKLIST_TEMPLATES["GET"]},
        {"endpoint": "/api/login", "method": "POST", "checklist": CHECKLIST_TEMPLATES["POST"] + CHECKLIST_TEMPLATES["AUTH"]},
        {"endpoint": "/api/users/{id}", "method": "PUT", "checklist": CHECKLIST_TEMPLATES["PUT"]},
        {"endpoint": "/api/upload", "method": "POST", "checklist": CHECKLIST_TEMPLATES["FILE"]},
        {"endpoint": "/api/admin/*", "method": "GET", "checklist": [
            "Verify endpoint is restricted to admin role",
            "Test horizontal and vertical privilege escalation",
            "Check for path-based auth bypass (/api/v2/admin vs /api/admin)",
            "Test for bypass using case variations (/Admin, /ADMIN)",
        ]},
        {"endpoint": "Cross-Origin Configuration", "method": "CORS", "checklist": CHECKLIST_TEMPLATES["CORS"]},
        {"endpoint": "/api/graphql", "method": "POST", "checklist": [
            "Test for Introspection query enabled",
            "Test for Batching attacks (brute-forcing/rate limit bypass)",
            "Check for excessive depth (DoS)",
            "Test for Alias overloading",
            "Verify authorization at field/resolver level",
        ]},
    ]
