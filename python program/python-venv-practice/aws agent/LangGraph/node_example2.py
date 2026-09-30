from typing import TypedDict

from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    message: str


def node_1(state):
    print("Node 1 executed")
    return {}


def node_2(state):
    print("Node 2 executed")
    return {}


graph_builder = StateGraph(State)

graph_builder.add_node("node_1", node_1)
graph_builder.add_node("node_2", node_2)

graph_builder.add_edge(START, "node_1")
graph_builder.add_edge("node_1", END)

graph = graph_builder.compile()

graph.invoke({
    "message": "Hello"
})