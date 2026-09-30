# here node can call normal python function 
# here normal function is not added as node
from typing import TypedDict

from langgraph.graph import StateGraph, START, END


class ECSState(TypedDict):
    desired_count: int
    running_count: int
    status: str

# normal python function
def get_service_status(desired_count, running_count):
    if running_count == desired_count:
        return "Healthy"

    return "Unhealthy"

#  this node call normal funciton 
def check_service(state):
    status = get_service_status(
        state["desired_count"],
        state["running_count"]
    )

    return {
        "status": status
    }


def show_status(state):
    print("Service status:", state["status"])

    return {}


graph_builder = StateGraph(ECSState)

graph_builder.add_node("check_service", check_service)
graph_builder.add_node("show_status", show_status)

graph_builder.add_edge(START, "check_service")
graph_builder.add_edge("check_service", "show_status")
graph_builder.add_edge("show_status", END)

graph = graph_builder.compile()

result = graph.invoke({
    "desired_count": 1,
    "running_count": 0
})

print("Final state:", result) # result will be contain the updated state