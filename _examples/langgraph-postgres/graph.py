from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt


class State(TypedDict, total=False):
    message: str
    draft: str
    approved: bool
    result: str


def draft(state: State):
    # Deterministic so the persistence test needs no model API key.
    return {"draft": state["message"].upper()}


def review(state: State):
    approved = interrupt({"draft": state["draft"], "question": "Approve this draft?"})
    if not isinstance(approved, bool):
        raise ValueError("Resume with a boolean")
    return {"approved": approved}


def finish(state: State):
    return {"result": state["draft"] if state["approved"] else "Rejected"}


def compile_graph(checkpointer):
    return (StateGraph(State).add_node("draft", draft).add_node("review", review)
            .add_node("finish", finish).add_edge(START, "draft").add_edge("draft", "review")
            .add_edge("review", "finish").add_edge("finish", END).compile(checkpointer=checkpointer))
