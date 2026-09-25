"""Talk to a deployed OpenJarvis server (``jarvis serve``) over HTTPS.

Standard library only, so it runs without the repo's environment.

Configuration (environment):
    OPENJARVIS_URL      base URL, e.g. https://openjarvis-server.onrender.com
    OPENJARVIS_API_KEY  the server's API key (sent as ``Authorization: Bearer``)

Commands::

    python jarvis_cloud.py health
    python jarvis_cloud.py models
    python jarvis_cloud.py tools
    python jarvis_cloud.py ask "summarise today's inbox" [--model M]

Exit status: 0 on success, 1 on an HTTP error from the server, 2 on
configuration or connection errors.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

TIMEOUT = 300


class ConfigError(Exception):
    """Missing or invalid client configuration."""


def _request(method: str, path: str, body: dict | None = None) -> object:
    base = os.environ.get("OPENJARVIS_URL", "").rstrip("/")
    if not base:
        raise ConfigError("OPENJARVIS_URL is not set")
    headers = {"Accept": "application/json"}
    key = os.environ.get("OPENJARVIS_API_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        raw = resp.read().decode()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jarvis_cloud")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("health")
    sub.add_parser("models")
    sub.add_parser("tools")
    ask = sub.add_parser("ask")
    ask.add_argument("prompt")
    ask.add_argument("--model", help="Model id; default is the server's first model.")
    args = parser.parse_args(argv)

    try:
        if args.cmd == "health":
            out = _request("GET", "/health")
        elif args.cmd == "models":
            out = _request("GET", "/v1/models")
        elif args.cmd == "tools":
            out = _request("GET", "/v1/tools")
        else:
            model = args.model
            if not model:
                models = _request("GET", "/v1/models")
                data = models.get("data", []) if isinstance(models, dict) else []
                if not data:
                    print("server lists no models; pass --model", file=sys.stderr)
                    return 2
                model = data[0]["id"]
            messages = [{"role": "user", "content": args.prompt}]
            resp = _request(
                "POST", "/v1/chat/completions", {"model": model, "messages": messages}
            )
            print(resp["choices"][0]["message"]["content"])
            return 0
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        print(f"HTTP {exc.code}: {detail}", file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"could not reach OpenJarvis server: {exc}", file=sys.stderr)
        return 2

    print(out if isinstance(out, str) else json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
