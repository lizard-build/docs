import json
import os
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

if len(sys.argv) != 2 or not os.environ.get("APP_URL"):
    raise SystemExit("Set APP_URL and pass the service name")


def health():
    request = Request(os.environ["APP_URL"] + "/health", headers={"Cache-Control": "no-cache"})
    with urlopen(request, timeout=5) as response:
        body = json.load(response)
    if body.get("ready") is not True or not isinstance(body.get("instanceId"), str) or not body["instanceId"]:
        raise ValueError("Health must include ready and instanceId")
    return body["instanceId"]


before = health()
subprocess.run(["lizard", "restart", "--service", sys.argv[1], "--json"], check=True, timeout=30)
deadline = time.monotonic() + 120
candidate, stable = None, 0
while time.monotonic() < deadline:
    try:
        current = health()
        stable = (stable + 1 if current == candidate else 1) if current != before else 0
        candidate = current
        if stable >= 3:
            print(f"Replacement process ready: {before} -> {current}")
            break
    except (URLError, TimeoutError, ValueError, OSError):
        stable = 0
    time.sleep(2)
else:
    raise SystemExit("No stable replacement process within 120 seconds; inspect lizard events and logs")
