import os
from worker import api_call


def check(token, call=api_call):
    bot = call(token, "getMe", {})
    webhook = call(token, "getWebhookInfo", {})
    if webhook.get("url"):
        raise RuntimeError("This bot has an active webhook; use a separate polling bot")
    return bot["username"]


if __name__ == "__main__":
    try:
        username = check(os.environ["TELEGRAM_BOT_TOKEN"])
    except Exception:
        raise SystemExit("Bot preflight failed. Check the token and active webhook; no settings were changed.")
    print(f"Token accepted for @{username}; no active webhook")
