#  here evidence result will be accumulated into one list instead of replacing with previous value
# ideally whenever we return any value if its same key then it will replace if it is differerent
# then it will add new field to the state

# it combine evidence result into one list instead of replacing
from typing import Annotated, TypedDict
from operator import add

from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    evidence: Annotated[list[str], add]


def node_1(state):
    print("Node 1 received:", state)

    return {
        "evidence": ["Service desired count is 1 but running count is 0"]
    }


def node_2(state):
    print("Node 2 received:", state)

    return {
        "evidence": ["Task failed to pull ECR registry authentication"]
    }


graph_builder = StateGraph(State)

graph_builder.add_node("node_1", node_1)
graph_builder.add_node("node_2", node_2)

graph_builder.add_edge(START, "node_1")
graph_builder.add_edge("node_1", "node_2")
graph_builder.add_edge("node_2", END)

graph = graph_builder.compile()

result = graph.invoke({
    "evidence": []
})

print("Final state:", result)


# Final state:
# {
#     'evidence': [
#         'Service desired count is 1 but running count is 0',
#         'Task failed to pull ECR registryauthentication'
#     ]
# }