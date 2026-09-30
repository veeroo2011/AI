# TypedDict is a Python typing feature that lets us describe the expected structure of a dictionary.
#
# 1. graph.invoke()
#         ↓
# 2. Initial state is created
#    {"message": "Hello from the state!"}
#         ↓
# 3. START
#         ↓
# 4. Edge says: START → hello
#         ↓
# 5. LangGraph calls hello_node(...)
#         ↓
# 6. Initial state is passed to hello_node
#         ↓
# 7. state_value receives that state

# graph.invoke() provides the initial state to the graph, 
# and LangGraph passes that state to the first node according to the graph's edges.


from langgraph.graph import StateGraph, START, END
from typing import TypedDict 

# Define our MyState
class MyState(TypedDict):
    message: str
    response: str

# MyState
# ├── message   → string
# └── response  → string
# It describes the shape of the state.


# The graph execution starts with a state, and nodes receive that state.
# LangGraph passes the current state INTO the node.

def hello_node(state):
    #print(state["message"])
    return {
        "response": "Node processed the message"
    }

# Now langGraph know 
# Graph
# |
# +-- State is MyState
#          |
#          +-- message: str
#          |
#          +-- response: str
# 


# stateGraph is a Graph Builder
graph_builder = StateGraph(MyState)

graph_builder.add_node("hello", hello_node) # here hello_node function is node and we provide name it as hello
                                            # so name of hello_node is hello

graph_builder.add_edge(START, "hello") # start from hello which means that node hello_node
graph_builder.add_edge("hello", END) # end with hello node

graph = graph_builder.compile() # it creates executable graph

# Start executing this graph, and use this dictionary as the initial state."
# we are providing the input/initial state for this execution as message
# invoke means run the graph
result = graph.invoke({ 
    "message": "Hello from the state!"
})

print(result)