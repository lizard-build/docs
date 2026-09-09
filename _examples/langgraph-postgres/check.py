import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from uuid import uuid4

url, token, thread = (os.environ[k] for k in ["APP_URL", "API_TOKEN", "THREAD_ID"])

def call(path, method="GET", data=None, auth=True, expected=200):
    headers = {"Content-Type": "application/json"}
    if auth:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url + path, data=json.dumps(data).encode() if data is not None else None, headers=headers, method=method)
    try:
        response = urlopen(req, timeout=30)
    except HTTPError as error:
        response = error
    assert response.status == expected, (path, response.status, expected)
    return json.load(response)

call("/health", auth=False)
call(f"/threads/{thread}", auth=False, expected=401)
call(f"/threads/{uuid4()}", expected=404)
mode = sys.argv[1]
if mode == "start":
    state = call(f"/threads/{thread}", "POST", {"message": "saved before restart"})
    assert state["next"] == ["review"] and state["interrupts"]
    call(f"/threads/{thread}", "POST", {"message": "must not overwrite"}, expected=409)
    call(f"/threads/{thread}/resume", "POST", {"approved": "yes"}, expected=422)
elif mode == "waiting":
    state = call(f"/threads/{thread}")
    assert state["next"] == ["review"] and state["interrupts"]
    assert state["values"]["draft"] == "SAVED BEFORE RESTART"
elif mode == "resume":
    state = call(f"/threads/{thread}/resume", "POST", {"approved": True})
    assert not state["next"] and state["values"]["result"] == "SAVED BEFORE RESTART"
    call(f"/threads/{thread}/resume", "POST", {"approved": True}, expected=409)
elif mode == "done":
    state = call(f"/threads/{thread}")
    assert not state["next"] and state["values"]["result"] == "SAVED BEFORE RESTART"
else:
    raise ValueError("Use start, waiting, resume or done")
print(f"{mode}: health, auth, thread state and persistence checks passed")
