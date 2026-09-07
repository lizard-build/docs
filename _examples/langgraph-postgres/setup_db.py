import os
from langgraph.checkpoint.postgres import PostgresSaver

if __name__ == "__main__":
    with PostgresSaver.from_conn_string(os.environ["DATABASE_URL"]) as saver:
        saver.conn.execute("SELECT pg_advisory_lock(19082027)")
        saver.setup()
    print("LangGraph checkpoint schema ready", flush=True)
