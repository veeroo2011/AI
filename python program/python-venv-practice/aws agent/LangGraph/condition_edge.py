from typing import TypedDict

from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    desired_count: int
    running_count: int
    status: str


def check_service(state):
    if state["running_count"] == state["desired_count"]:
        return {
            "status": "healthy"
        }

    return {
        "status": "unhealthy"
    }

# this function will be used to for conditional_edge
def decide_next_step(state):
    if state["status"] == "healthy":
        return "healthy"

    return "unhealthy"


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


# its a conditional edge so it will first execute check_service
# once check_service executed then it goes to router and find what to execute next.
# it will execute decide_next_step and based on result of that function
# router goes to dictionary where return is mapped with exact node 
# if healthy then it execute show_healthy node
# if unhealthy then it execute investigate ndoe

graph_builder.add_conditional_edges(
    "check_service",  # ==> node1
    decide_next_step, # ==> Router function
    {                 # ==> dictionary mapping
        "healthy": "show_healthy",
        "unhealthy": "investigate"
    }
)

graph_builder.add_edge("show_healthy", END)
graph_builder.add_edge("investigate", END)

graph = graph_builder.compile()

# save this output and put inisde mermaid live editor to see graph in visual
#print(graph.get_graph().draw_mermaid())

result = graph.invoke({
    "desired_count": 1,
    "running_count": 1
})

print("Final state:", result)