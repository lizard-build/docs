import hmac
import os
from contextlib import contextmanager
from uuid import UUID, uuid4
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, StrictBool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command
from graph import compile_graph

TOKEN = os.environ["API_TOKEN"]
DB = os.environ["DATABASE_URL"]
INSTANCE_ID = str(uuid4())
if len(TOKEN) < 32:
    raise RuntimeError("API_TOKEN must contain at least 32 characters")
app = FastAPI(title="LangGraph checkpoint example", docs_url=None, redoc_url=None, openapi_url=None)
bearer = HTTPBearer(auto_error=False)


def authorize(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if not credentials or not hmac.compare_digest(credentials.credentials, TOKEN):
        raise HTTPException(401, "Unauthorized", headers={"WWW-Authenticate": "Bearer"})


class StartInput(BaseModel):
    message: str = Field(min_length=1, max_length=200)


class ResumeInput(BaseModel):
    approved: StrictBool


@contextmanager
def graph_for(thread: UUID):
    # Connection-scoped lock serializes requests for the same thread across processes.
    # Closing the connection releases the lock, including after an exception.
    with PostgresSaver.from_conn_string(DB) as saver:
        saver.conn.execute("SET lock_timeout = '5s'")
        saver.conn.execute("SELECT pg_advisory_lock(hashtextextended(%s, 0))", (str(thread),))
        yield compile_graph(saver), {"configurable": {"thread_id": str(thread)}}


def snapshot(graph, config):
    state = graph.get_state(config)
    return {"thread_id": config["configurable"]["thread_id"], "values": state.values,
            "next": list(state.next), "interrupts": [i.value for task in state.tasks for i in task.interrupts]}


@app.middleware("http")
async def no_cache(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex"
    return response


@app.exception_handler(Exception)
async def internal_error(_request, _error):
    return JSONResponse(status_code=503, content={"detail": "Database or graph unavailable"})


@app.get("/health")
def health():
    with PostgresSaver.from_conn_string(DB) as saver:
        saver.conn.execute("SELECT 1 FROM checkpoints LIMIT 1")
    return {"ready": True, "instanceId": INSTANCE_ID}


@app.post("/threads/{thread}", dependencies=[Depends(authorize)])
def start(thread: UUID, data: StartInput):
    with graph_for(thread) as (graph, config):
        if graph.get_state(config).values:
            raise HTTPException(409, "Thread already exists; read or resume it")
        graph.invoke({"message": data.message}, config)
        return snapshot(graph, config)


@app.get("/threads/{thread}", dependencies=[Depends(authorize)])
def read(thread: UUID):
    with graph_for(thread) as (graph, config):
        if not graph.get_state(config).values:
            raise HTTPException(404, "Thread not found")
        return snapshot(graph, config)


@app.post("/threads/{thread}/resume", dependencies=[Depends(authorize)])
def resume(thread: UUID, data: ResumeInput):
    with graph_for(thread) as (graph, config):
        state = graph.get_state(config)
        if not state.values:
            raise HTTPException(404, "Thread not found")
        if not any(task.interrupts for task in state.tasks):
            raise HTTPException(409, "Thread is not waiting for approval")
        graph.invoke(Command(resume=data.approved), config)
        return snapshot(graph, config)
