VULNERABILITY_DB = {
    "SQL Injection": {
        "description": "Injection of attacker-controlled SQL syntax into backend queries.",
        "attack_conditions": ["Dynamic query building", "Unsanitized input reaches database layer"],
        "exploitation_method": "Probe parameters with boolean, error-based, and time-based payloads.",
        "impact": "Authentication bypass, data exposure, and data modification.",
        "testing_checklist": [
            "Identify numeric and string parameters",
            "Try quote breaking, boolean tests, and time delays",
            "Observe SQL errors, differential responses, or latency"
        ],
        "poc_examples": ["' OR '1'='1", "' UNION SELECT NULL--", "'; WAITFOR DELAY '0:0:5'--"]
    },
    "Cross Site Scripting": {
        "description": "Execution of untrusted script in a victim browser.",
        "attack_conditions": ["Input reflected or stored without safe output encoding"],
        "exploitation_method": "Inject HTML and JavaScript payloads into reflected, stored, and DOM sinks.",
        "impact": "Session theft, phishing, and account takeover.",
        "testing_checklist": [
            "Map input reflection points",
            "Check HTML, attribute, script, and URL contexts",
            "Validate CSP and output encoding behavior"
        ],
        "poc_examples": ["<svg/onload=alert(1)>", "\"><script>alert(1)</script>"]
    },
    "CSRF": {
        "description": "Cross-site request execution due to missing anti-CSRF protections.",
        "attack_conditions": ["State-changing requests rely only on ambient cookies"],
        "exploitation_method": "Forge authenticated cross-site requests from attacker-controlled origin.",
        "impact": "Unauthorized state change for victim accounts.",
        "testing_checklist": [
            "Identify state-changing routes",
            "Check SameSite cookie behavior",
            "Verify anti-CSRF tokens and origin checks"
        ],
        "poc_examples": ["Auto-submitting HTML form", "Cross-origin fetch with relaxed CORS assumptions"]
    },
    "IDOR": {
        "description": "Direct object references exposed without authorization controls.",
        "attack_conditions": ["Predictable identifiers", "Missing object-level authorization"],
        "exploitation_method": "Swap object identifiers across accounts and roles.",
        "impact": "Unauthorized data access or modification.",
        "testing_checklist": [
            "Enumerate object identifiers in URLs and bodies",
            "Test horizontal and vertical privilege changes",
            "Verify access with secondary account context"
        ],
        "poc_examples": ["Change /api/users/123 to /api/users/124", "Modify JSON owner_id or user_id"]
    },
    "SSRF": {
        "description": "Server-side fetch behavior that can be redirected to attacker-chosen resources.",
        "attack_conditions": ["Backend fetches user-controlled URLs"],
        "exploitation_method": "Point server fetchers at internal services or metadata endpoints.",
        "impact": "Internal access, cloud credential exposure, and pivoting.",
        "testing_checklist": [
            "Locate webhook, URL import, and PDF/image fetch features",
            "Try internal IPs, localhost, and metadata addresses",
            "Measure redirects and protocol handling"
        ],
        "poc_examples": ["http://127.0.0.1:8080", "http://169.254.169.254/latest/meta-data/"]
    },
    "Command Injection": {
        "description": "User input reaches shell or process execution unsafely.",
        "attack_conditions": ["Shell invocation with concatenated input"],
        "exploitation_method": "Inject shell metacharacters or chained commands.",
        "impact": "Remote code execution and server compromise.",
        "testing_checklist": [
            "Identify file utilities, ping, conversion, and backup features",
            "Try command separators and argument injection",
            "Confirm with safe timing or out-of-band effects"
        ],
        "poc_examples": [";id", "&& whoami", "| ping -n 5 127.0.0.1"]
    },
    "File Upload Vulnerabilities": {
        "description": "Unsafe upload handling enables code execution, overwrite, or parsing attacks.",
        "attack_conditions": ["Weak type validation", "Dangerous file processing"],
        "exploitation_method": "Upload polyglots, oversized files, and parser-triggering content.",
        "impact": "RCE, stored XSS, or denial of service.",
        "testing_checklist": [
            "Check extension, MIME, and content validation",
            "Test filename handling and path traversal",
            "Assess storage permissions and execution context"
        ],
        "poc_examples": ["image.php.jpg polyglot", "../../app.py filename traversal"]
    },
    "XXE": {
        "description": "External entity resolution in XML parsers.",
        "attack_conditions": ["XML parser with external entities enabled"],
        "exploitation_method": "Supply crafted XML with local file or SSRF entities.",
        "impact": "File disclosure, SSRF, and denial of service.",
        "testing_checklist": [
            "Locate XML import or SOAP endpoints",
            "Try external entity and parameter entity payloads",
            "Observe file leakage or parser behavior"
        ],
        "poc_examples": ["<!ENTITY xxe SYSTEM 'file:///etc/passwd'>"]
    },
    "Server Side Template Injection": {
        "description": "Template engines evaluate attacker-controlled expressions.",
        "attack_conditions": ["Unsafely rendering user input into templates"],
        "exploitation_method": "Probe expression syntax and escalate to object access or code exec.",
        "impact": "Sensitive data exposure or remote code execution.",
        "testing_checklist": [
            "Identify server-side rendering flows",
            "Test engine-specific expression payloads",
            "Confirm sandbox escape possibilities"
        ],
        "poc_examples": ["{{7*7}}", "${7*7}"]
    },
    "Race Conditions": {
        "description": "Concurrent requests break intended state transitions.",
        "attack_conditions": ["Non-atomic critical operations"],
        "exploitation_method": "Send simultaneous state-changing requests.",
        "impact": "Duplicate rewards, balance abuse, or auth bypass.",
        "testing_checklist": [
            "Map coupon, balance, redemption, and invite flows",
            "Replay concurrent requests with timing control",
            "Look for double spends or inconsistent state"
        ],
        "poc_examples": ["Parallel redemption requests", "Multi-click transfer sequence"]
    },
    "Request Smuggling": {
        "description": "Conflicting request parsing across hops allows hidden request injection.",
        "attack_conditions": ["Front-end/back-end parser disagreement"],
        "exploitation_method": "Probe TE/CL or CL/CL discrepancies.",
        "impact": "Cache poisoning, auth bypass, and response desync.",
        "testing_checklist": [
            "Identify proxy/load-balancer fronted services",
            "Test CL.TE and TE.CL variants carefully",
            "Measure timeout and queue desync indicators"
        ],
        "poc_examples": ["Transfer-Encoding plus Content-Length conflict"]
    },
    "Cache Poisoning": {
        "description": "Attacker-controlled input becomes cached for other users.",
        "attack_conditions": ["Cache key confusion", "Unsafe header variation"],
        "exploitation_method": "Inject headers or params that alter responses but miss cache key.",
        "impact": "Stored XSS, defacement, or session compromise.",
        "testing_checklist": [
            "Check cacheable dynamic routes",
            "Probe X-Forwarded-* and host-derived behaviors",
            "Validate cache hits for poisoned content"
        ],
        "poc_examples": ["Poison unkeyed header variations"]
    },
    "JWT attacks": {
        "description": "JWT validation weaknesses permit token forgery or abuse.",
        "attack_conditions": ["Weak secret, alg confusion, missing claims validation"],
        "exploitation_method": "Analyze signing algorithm, kid handling, and claim trust.",
        "impact": "Privilege escalation and account takeover.",
        "testing_checklist": [
            "Decode token and inspect alg and claims",
            "Test none or alg confusion where relevant",
            "Check audience, issuer, expiry, and key selection"
        ],
        "poc_examples": ["Modified role claim", "Weak HMAC secret brute-force"]
    },
    "OAuth attacks": {
        "description": "Weak OAuth and OIDC implementation exposes tokens or account binding.",
        "attack_conditions": ["Improper redirect URI or state handling"],
        "exploitation_method": "Manipulate authorization flow and account linking states.",
        "impact": "Token theft or account takeover.",
        "testing_checklist": [
            "Inspect redirect_uri validation",
            "Verify state, nonce, and PKCE handling",
            "Test account linking and scope escalation"
        ],
        "poc_examples": ["Open redirect in redirect_uri", "Missing state validation"]
    },
    "API vulnerabilities": {
        "description": "Common API weaknesses such as broken auth, mass assignment, and excessive data exposure.",
        "attack_conditions": ["Predictable routes and weak object controls"],
        "exploitation_method": "Model resources, roles, and body fields for abuse.",
        "impact": "Data exposure, privilege escalation, and workflow abuse.",
        "testing_checklist": [
            "Review OpenAPI or observed endpoints",
            "Test object-level auth and mass assignment",
            "Check rate limits and hidden parameters"
        ],
        "poc_examples": ["Add isAdmin=true", "Read neighboring resource IDs"]
    }
}


LANGUAGE_EXAMPLES = {
    "JavaScript": [
        {
            "vulnerability": "Prototype pollution",
            "snippet": "merge(target, JSON.parse(input)) without key filtering can poison __proto__."
        },
        {
            "vulnerability": "DOM XSS",
            "snippet": "location.hash inserted into innerHTML enables script execution."
        }
    ],
    "Python": [
        {
            "vulnerability": "SQL injection",
            "snippet": "cursor.execute(f\"SELECT * FROM users WHERE id = {user_input}\")"
        },
        {
            "vulnerability": "Command injection",
            "snippet": "os.system('ping ' + host)"
        }
    ],
    "PHP": [
        {
            "vulnerability": "Insecure deserialization",
            "snippet": "unserialize($_POST['data']) can invoke gadget chains."
        }
    ],
    "Node.js": [
        {
            "vulnerability": "Command injection",
            "snippet": "exec(`convert ${filename}`) with unsanitized filename."
        }
    ]
}