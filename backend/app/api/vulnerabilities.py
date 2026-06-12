from fastapi import APIRouter

router = APIRouter()

# Vulnerability knowledge base
VULNERABILITY_KB: dict = {
    "idor": {
        "description": "Insecure Direct Object Reference — accessing resources by manipulating identifiers without authorization checks.",
        "attack_conditions": ["Predictable IDs", "Missing ownership checks", "Exposed internal identifiers"],
        "exploitation_method": "Replace your ID with another user's ID in requests and observe the response.",
        "impact": "Unauthorized data access, modification, or deletion.",
        "testing_checklist": [
            "Replace numeric IDs in URLs/params",
            "Try UUIDs of other users",
            "Test batch endpoints",
            "Check indirect references via names/emails",
        ],
        "poc_examples": ["GET /api/user/2 (logged in as user 1)", "GET /api/invoice/9999"],
    },
    "sqli": {
        "description": "SQL Injection — unsanitized user input interpolated directly into SQL queries.",
        "attack_conditions": ["Unparameterized queries", "Dynamic query construction", "Error messages leaking DB info"],
        "exploitation_method": "Inject SQL metacharacters (' \" -- ;) into input fields and observe behavior.",
        "impact": "Data exfiltration, authentication bypass, remote code execution.",
        "testing_checklist": [
            "Test single quote in all inputs",
            "Try UNION-based payloads",
            "Use sqlmap with safe-level",
            "Check for blind injection via time delays",
        ],
        "poc_examples": ["' OR 1=1--", "1 UNION SELECT null,username,password FROM users--"],
    },
    "xss": {
        "description": "Cross-Site Scripting — injecting scripts into pages viewed by other users.",
        "attack_conditions": ["Unescaped user input rendered in HTML", "Missing CSP", "DOM-based sinks"],
        "exploitation_method": "Inject <script> tags or event handlers into input fields.",
        "impact": "Session hijacking, credential theft, malware delivery.",
        "testing_checklist": [
            "Test <script>alert(1)</script> in all inputs",
            "Check reflected parameters in URL",
            "Test DOM sinks: innerHTML, document.write",
            "Try SVG and img onerror payloads",
        ],
        "poc_examples": ["<script>alert(document.cookie)</script>", "<img src=x onerror=alert(1)>"],
    },
    "ssrf": {
        "description": "Server-Side Request Forgery — making the server fetch attacker-controlled URLs.",
        "attack_conditions": ["URL parameters passed to HTTP clients", "Webhook or import features", "PDF/image renderers"],
        "exploitation_method": "Replace URL values with internal addresses like http://169.254.169.254/.",
        "impact": "Internal service access, cloud metadata exposure, RCE.",
        "testing_checklist": [
            "Find URL input parameters",
            "Try http://localhost and http://127.0.0.1",
            "Try cloud metadata: http://169.254.169.254/latest/meta-data/",
            "Use Burp Collaborator for blind SSRF",
        ],
        "poc_examples": ["url=http://169.254.169.254/latest/meta-data/", "webhook=http://internal-service/admin"],
    },
    "broken_auth": {
        "description": "Broken Authentication — weaknesses in login, session, or token management.",
        "attack_conditions": ["Weak passwords allowed", "No MFA", "JWTs with 'none' algorithm", "Long-lived tokens"],
        "exploitation_method": "Try credential stuffing, JWT manipulation, or session fixation.",
        "impact": "Account takeover, privilege escalation.",
        "testing_checklist": [
            "Test JWT with alg:none",
            "Check token expiry",
            "Try password reset token reuse",
            "Test concurrent sessions",
        ],
        "poc_examples": ['{"alg":"none","typ":"JWT"}', "Reuse password reset link after use"],
    },
}


@router.get("")
def list_vulnerabilities():
    return VULNERABILITY_KB


@router.get("/{vuln_class}")
def get_vulnerability(vuln_class: str):
    entry = VULNERABILITY_KB.get(vuln_class.lower())
    if not entry:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Vulnerability class '{vuln_class}' not found")
    return entry
