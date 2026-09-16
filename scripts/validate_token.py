import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    token = os.getenv("BOT_TOKEN_TO_TEST", "").strip()
    if not token:
        return 2

    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        with urllib.request.urlopen(url, timeout=12) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 404):
            return 2
        return 3
    except Exception:
        return 3

    return 0 if payload.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
