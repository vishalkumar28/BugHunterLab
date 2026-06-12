from fastapi import APIRouter

router = APIRouter()

CHECKLIST_TEMPLATES = {
    "GET": [
        "Test for IDOR by replacing IDs with other users' IDs",
        "Check if response leaks PII or sensitive data",
        "Test for information disclosure in error messages",
        "Verify authentication is required",
        "Check caching headers (no-store for sensitive data)",
    ],
    "POST": [
        "Test for SQL injection in body parameters",
        "Test for XSS in any reflected input fields",
        "Check CSRF token presence and validation",
        "Test for mass assignment / over-posting",
        "Verify rate limiting on sensitive actions",
    ],
    "PUT": [
        "Test for IDOR — can you update another user's resource?",
        "Check for mass assignment vulnerabilities",
        "Verify ownership checks on the target resource",
        "Test partial updates bypass validation",
    ],
    "DELETE": [
        "Test for IDOR — can you delete another user's resource?",
        "Check if soft-delete data remains accessible",
        "Verify admin-only endpoints require admin auth",
        "Test for race conditions during deletion",
    ],
    "FILE": [
        "Test for path traversal in file names (../)",
        "Upload polyglot files (JPEG+PHP)",
        "Check content-type validation (bypass with MIME sniffing)",
        "Test for stored XSS via SVG upload",
        "Verify file size limits are enforced",
    ],
}


@router.get("")
def get_checklists(target_id: int = 1):
    """Return endpoint-specific checklists. Uses target_id for future customization."""
    return [
        {"endpoint": "/api/users/{id}", "method": "GET", "checklist": CHECKLIST_TEMPLATES["GET"]},
        {"endpoint": "/api/login", "method": "POST", "checklist": CHECKLIST_TEMPLATES["POST"] + [
            "Test for username enumeration via response differences",
            "Check lockout policy after N failed attempts",
        ]},
        {"endpoint": "/api/users/{id}", "method": "PUT", "checklist": CHECKLIST_TEMPLATES["PUT"]},
        {"endpoint": "/api/upload", "method": "POST", "checklist": CHECKLIST_TEMPLATES["FILE"]},
        {"endpoint": "/api/admin/*", "method": "GET", "checklist": [
            "Verify endpoint is restricted to admin role",
            "Test horizontal privilege escalation",
            "Check for path-based auth bypass (/api/v2/admin vs /api/admin)",
        ]},
    ]
