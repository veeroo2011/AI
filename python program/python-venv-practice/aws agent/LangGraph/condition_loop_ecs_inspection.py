from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from operator import add

class ECSState(TypedDict):
    attempts: int
    evidence: Annotated[list[str], add]


def inspect_service(state):
    attempts = state["attempts"] + 1

    print("Inspection attempt:", attempts)

    return {
        "attempts": attempts,
        "evidence": [
            f"Inspection {attempts}: service has no running tasks"
        ]
    }


def decide_next_step(state):
    if state["attempts"] >= 3:
        return END

    return "inspect_service"


graph_builder = StateGraph(ECSState)

graph_builder.add_node("inspect_service", inspect_service)

graph_builder.add_edge(START, "inspect_service")

graph_builder.add_conditional_edges(
    "inspect_service",
    decide_next_step
)

graph = graph_builder.compile()


result = graph.invoke({
    "attempts": 0,
    "evidence": []
})

print("Final state:", result)