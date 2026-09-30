from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    count: int


def counter(state):
    print("Counter:", state["count"])

    return {
        "count": state["count"] + 1
    }

def check_count(state):
    print("Checking count:", state["count"])

    return {}

# Routing function
def decide_next_step(state):
    if state["count"] >= 3:
        return "done"

    return "continue"


graph_builder = StateGraph(State)

graph_builder.add_node("counter", counter)
graph_builder.add_node("check_count", check_count)

graph_builder.add_edge(START, "counter")

graph_builder.add_edge("counter", "check_count")

# add conditional edge
graph_builder.add_conditional_edges(
  "check_count",
  decide_next_step,
  {
    "continue": "counter",
    "done": END.  # langGraph tells that graph terminates here no further routing
  }

)

graph = graph_builder.compile()

result = graph.invoke({
    "count": 0
})

print("Final state:", result)