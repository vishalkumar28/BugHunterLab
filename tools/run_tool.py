from __future__ import annotations

import json
import shutil
import subprocess
import sys


SUPPORTED_TOOLS = {
    "subfinder": ["subfinder"],
    "amass": ["amass"],
    "httpx": ["httpx"],
    "nmap": ["nmap"],
    "ffuf": ["ffuf"],
    "nuclei": ["nuclei"],
    "sqlmap": ["sqlmap"],
}


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Missing tool name"}))
        return 1
    tool_name = sys.argv[1]
    args = sys.argv[2:]
    if tool_name not in SUPPORTED_TOOLS:
        print(json.dumps({"status": "error", "message": f"Unsupported tool: {tool_name}"}))
        return 1
    binary = SUPPORTED_TOOLS[tool_name][0]
    if shutil.which(binary) is None:
        print(json.dumps({
            "status": "mocked",
            "tool": tool_name,
            "message": f"{binary} not found in PATH. Install the tool to enable live execution.",
            "args": args,
        }))
        return 0
    completed = subprocess.run([binary, *args], capture_output=True, text=True, check=False)
    print(json.dumps({
        "status": "completed" if completed.returncode == 0 else "failed",
        "tool": tool_name,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
    }))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())