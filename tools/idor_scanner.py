import argparse
import json
from urllib.parse import urlencode

import requests


def main() -> int:
    parser = argparse.ArgumentParser(description="Simple IDOR probe helper")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--ids", nargs="+", required=True)
    parser.add_argument("--token", default="")
    args = parser.parse_args()

    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    results = []
    for object_id in args.ids:
        url = f"{args.base_url}?{urlencode({'id': object_id})}"
        response = requests.get(url, headers=headers, timeout=10)
        results.append({"id": object_id, "status": response.status_code, "length": len(response.text)})
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())