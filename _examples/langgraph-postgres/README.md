# LangGraph with a Postgres checkpointer

Runnable source for the [LangGraph persistence guide](https://lizard.build/docs/guides/langgraph-postgres/).

Use Python 3.13 and `uv sync --frozen`. Set `DATABASE_URL` and a random `API_TOKEN` of at least 32 characters. Run the exact `Procfile` command: setup and the server both need `uv run --frozen`.

The deterministic graph drafts uppercase text, interrupts for approval and resumes with the same thread ID. It needs no model API key. Its HTTP API authenticates all thread access with one shared token. Postgres advisory locks serialize requests for the same thread.

With `APP_URL`, `API_TOKEN` and a UUID `THREAD_ID` exported, run `python3 check.py start`. Restart the service, run `waiting`, then `resume`. Restart once more and run `done`. The waiting and done checks only read checkpoints.

This is a single-user persistence example, not a queue, user authorization system, backup test or exactly-once side-effect implementation. Long tasks, model calls and higher concurrency need separate testing.
