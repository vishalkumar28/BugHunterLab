import argparse
import json

import requests


def main() -> int:
    parser = argparse.ArgumentParser(description="Basic API field fuzzer")
    parser.add_argument("--url", required=True)
    parser.add_argument("--token", default="")
    parser.add_argument("--field", default="role")
    parser.add_argument("--values", nargs="+", default=["admin", "true", "1"])
    args = parser.parse_args()

    headers = {"Authorization": f"Bearer {args.token}", "Content-Type": "application/json"}
    attempts = []
    for value in args.values:
        response = requests.post(args.url, headers=headers, json={args.field: value}, timeout=10)
        attempts.append({"value": value, "status": response.status_code, "preview": response.text[:120]})
    print(json.dumps(attempts, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())