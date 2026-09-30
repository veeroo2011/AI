# A node can perform normal Python logic
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

class ECSState(TypedDict):
    desired_count: int
    running_count: int
    status: str

def calculate_status(state):
    if state["running_count"] == state["desired_count"]:
      return {
        "status": "healthy"
      }
    return {
      "status": "Unhealthy"
    }

def show_status(state):
    print("service_status: ", state["status"])
    return {}

graph_builder = StateGraph(ECSState)

graph_builder.add_node("calculate_status", calculate_status)
graph_builder.add_node("show_status", show_status)

graph_builder.add_edge(START, "calculate_status")
graph_builder.add_edge("calculate_status", "show_status")
graph_builder.add_edge("show_status", END)

graph = graph_builder.compile()

result = graph.invoke({
    "desired_count": 1,
    "running_count": 1
})

print("final state is ", result)