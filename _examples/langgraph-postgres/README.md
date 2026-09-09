# LangGraph with a Postgres checkpointer

Runnable source for the [LangGraph persistence guide](https://lizard.build/docs/guides/langgraph-postgres/).

Use Python 3.13 and `uv sync --frozen`. Set `DATABASE_URL` and a random `API_TOKEN` of at least 32 characters. Run the exact `Procfile` command: setup and the server both need `uv run --frozen`.

The deterministic graph drafts uppercase text, interrupts for approval and resumes with the same thread ID. It needs no model API key. Its HTTP API authenticates all thread access with one shared token. Postgres advisory locks serialize requests for the same thread.

With `APP_URL`, `API_TOKEN` and a UUID `THREAD_ID` exported, run `python3 check.py start`. Run `python3 restart_and_wait.py graph`, then the checks with `waiting` and `resume`. Run the restart helper once more and check `done`. The waiting and done checks only read checkpoints.

The restart helper calls Lizard CLI and waits for three successful health responses from a new process. It compares the health endpoint's random `instanceId`, so a response from the old process cannot pass the check. It requires one replica and one HTTP worker, and fails after 120 seconds.

This is a single-user persistence example, not a queue, user authorization system, backup test or exactly-once side-effect implementation. Long tasks, model calls and higher concurrency need separate testing.
