from langgraph.graph import StateGraph, START, END
from typing import TypedDict 

# Define our MyState dictionary expectation
class ECSState(TypedDict):
    service_name: str
    desired_count: int
    running_count: int
    diagnosis: str


def check_service(state):
  print("service:", state["service_name"])
  print("desired:", state["desired_count"])
  print("running:", state["running_count"])

  return {
    "diagnosis": "Service has fewer running tasks than desired"
  }

def show_diagnosis(state):
  print("Diagnosis:", state["diagnosis"])

  return {}


# stateGraph is a Graph Builder
graph_builder = StateGraph(ECSState)

# Add node1 & node2
graph_builder.add_node("node1", check_service)
graph_builder.add_node("node2", show_diagnosis)

# Graph start from node1
graph_builder.add_edge(START, "node1")

# Execute from node1 to node2
graph_builder.add_edge("node1", "node2")

# End with node2
graph_builder.add_edge("node2", END) 

# Make the graph executable
graph = graph_builder.compile()

result = graph.invoke({ 
    "service_name": "hotel-mysql-service",
    "desired_count": 1,
    "running_count": 0
})

print("Final state:", result)

############################################
# Node returns	    |          What happens
#-------------------------------------------
# New field	        |          Field is added to state
# Existing field	  |          Existing value is updated/replaced to state
# {}	              |          No state update