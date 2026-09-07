# Telegram polling worker

Run `python -m unittest -v` for local tests. No test calls Telegram. Set `TELEGRAM_BOT_TOKEN` only when you intend to run the bot, then run `python worker.py`.

Use one process and one replica per token. The bot uses long polling and must not have an active webhook. Offsets live in process memory; a retry or restart can repeat delivery. Use durable update IDs and idempotent handlers before adding payments or other actions that must not repeat.

Source: https://core.telegram.org/bots/api#getupdates
