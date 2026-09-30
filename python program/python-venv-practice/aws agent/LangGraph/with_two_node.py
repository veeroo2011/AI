from langgraph.graph import StateGraph, START, END
from typing import TypedDict 

# Define our MyState dictionary expectation
class MyState(TypedDict):
    message: str
    response: str
    status: str

# Define node1
def node1(state):
    print("Node 1 received:", state)
    return {
        "response": "Node 1 processed the message"
    }

# Define node2
def node2(state):
    print("Node 2 received:", state)
    return {
      "status": "Completed"
    }

# stateGraph is a Graph Builder
graph_builder = StateGraph(MyState)

# Add node1 & node2
graph_builder.add_node("node1", node1)
graph_builder.add_node("node2", node2)

# Graph start from node1
graph_builder.add_edge(START, "node1")

# Execute from node1 to node2
graph_builder.add_edge("node1", "node2")

# End with node2
graph_builder.add_edge("node2", END) 

# Make the graph executable
graph = graph_builder.compile()

result = graph.invoke({ 
    "message": "Hello from initial state!"
})

print("Final state:", result)

############################################
# Node returns	    |          What happens
#-------------------------------------------
# New field	        |          Field is added to state
# Existing field	  |          Existing value is updated/replaced to state
# {}	              |          No state update