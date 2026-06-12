from fastapi import APIRouter

router = APIRouter()

@router.get("")
def get_learning_data():
    return {
        "1": {
            "title": "Phase 1: Fundamentals",
            "topics": ["Web Architecture", "HTTP Basics", "Common Vulnerabilities"],
        },
        "2": {
            "title": "Phase 2: Reconnaissance",
            "topics": ["Subdomain Enumeration", "Port Scanning", "Directory Brute-forcing"],
        },
        "3": {
            "title": "Phase 3: Vulnerability Scanning",
            "topics": ["Automated Scanners", "Manual Testing", "Logic Flaws"],
        },
        "4": {
            "title": "Phase 4: Exploitation & Reporting",
            "topics": ["Proof of Concept", "Report Writing", "Remediation"],
        }
    }
