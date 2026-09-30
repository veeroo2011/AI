
# this langraph do not use mapping dicitonary for conditional_edge
# laggraph will interpreate to move to node based on router function return

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    desired_count: int
    running_count: int
    status: str


def check_service(state):
    if state["running_count"] == state["desired_count"]:
        return {"status": "healthy"}

    return {"status": "unhealthy"}

# function return the node name 
def decide_next_step(state):
    if state["status"] == "healthy":
        return "show_healthy"

    return "investigate"


def show_healthy(state):
    print("Service is healthy")
    return {}


def investigate(state):
    print("Service needs investigation")
    return {}


graph_builder = StateGraph(State)

graph_builder.add_node("check_service", check_service)
graph_builder.add_node("show_healthy", show_healthy)
graph_builder.add_node("investigate", investigate)

graph_builder.add_edge(START, "check_service")


# first check_service executed and then router function executed decide_next_step
# and this time router function return node name
# Here the routing function itself determines the destination node. no need to mention dictionary mapping
graph_builder.add_conditional_edges(
    "check_service",
    decide_next_step
)

graph_builder.add_edge("show_healthy", END)
graph_builder.add_edge("investigate", END)

graph = graph_builder.compile()


result = graph.invoke({
    "desired_count": 1,
    "running_count": 0
})

print("Final state:", result)