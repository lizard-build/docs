# Telegram polling worker

Run `python3 -m unittest -v` for local tests. No test calls Telegram. Set `TELEGRAM_BOT_TOKEN` only when you intend to run the bot, run `python3 check_bot.py` to validate the token and reject an active webhook, then run `python3 worker.py`.

Use one process and one replica per token. The bot uses long polling and must not have an active webhook. Offsets live in process memory; a retry or restart can repeat delivery. Use durable update IDs and idempotent handlers before adding payments or other actions that must not repeat.

Source: https://core.telegram.org/bots/api#getupdates
