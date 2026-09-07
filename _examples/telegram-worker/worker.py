import json
import os
import signal
import threading
import urllib.error
import urllib.request

stopping = threading.Event()


def api_call(token, method, payload):
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=35) as response:
        body = json.load(response)
    if not body.get("ok"):
        raise RuntimeError("Telegram rejected the request")
    return body["result"]


def process_updates(updates, send):
    next_offset = None
    for update in updates:
        message = update.get("message", {})
        if "text" in message and "chat" in message:
            send("sendMessage", {
                "chat_id": message["chat"]["id"],
                "text": "Echo: " + message["text"],
            })
        next_offset = update["update_id"] + 1
    return next_offset


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    offset = None
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stopping.set())
    print("Telegram worker started", flush=True)
    while not stopping.is_set():
        try:
            payload = {"timeout": 25, "allowed_updates": ["message"]}
            if offset is not None:
                payload["offset"] = offset
            updates = api_call(token, "getUpdates", payload)
            next_offset = process_updates(updates, lambda method, data: api_call(token, method, data))
            if next_offset is not None:
                offset = next_offset
        except Exception:
            # A request exception may contain the token URL. Do not print it.
            print("Telegram request failed; retrying in 5 seconds", flush=True)
            stopping.wait(5)


if __name__ == "__main__":
    main()
