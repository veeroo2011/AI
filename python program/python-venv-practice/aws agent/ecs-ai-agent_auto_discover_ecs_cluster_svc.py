import json
import boto3
from pprint import pprint
from openai import OpenAI

client = OpenAI()

ecs = boto3.client(
  "ecs",
  region_name = "eu-west-1"
)


# define functin to list the ecs cluster

def list_ecs_clusters():
    response = ecs.list_clusters()
    cluster_list = [] 
    for arn in response["clusterArns"]:
        cluster_name = arn.split("/")[-1]
        cluster_list.append(cluster_name)
    return {
      "clusters": cluster_list
    }

# define function to list the ecs services
def list_ecs_services(cluster_name):
    response = ecs.list_services(
      cluster=cluster_name
    )
    services = []
    for arn in response["serviceArns"]:
        service_name = arn.split("/")[-1]
        services.append(service_name)

    return {
      "cluster_name": cluster_name,
      "services": services
    }

# define function to get the status of a service
def get_ecs_service_status(cluster_name, service_name):

  if not cluster_name:
    return {
        "error": "Cluster name is required"
  }

  if not service_name:
    return {
        "error": "Service name is required",
        "cluster_name": cluster_name
    }

  response = ecs.describe_services(
    cluster=cluster_name,
    services=[service_name]
  )

  # control if the service not exists or its empty
  if not response["services"]:
    return {
      "error": "Service not found",
      "cluster_name": cluster_name,
      "service_name": service_name
    }

  # capture the whole details of service
  service = response["services"][0]

  return {
    "cluster_name": cluster_name,
    "service_name": service["serviceName"],
    "status": service["status"],
    "desired_count": service["desiredCount"],
    "running_count": service["runningCount"],
    "pending_count": service["pendingCount"],
    "task_definition": service["taskDefinition"]
  }

# define function to get the task details
def get_ecs_tasks(cluster_name, service_name):
    if not cluster_name:
        return {
            "error": "Cluster name is required"
        }
    if not service_name:
        return {
            "error": "Service name is required",
            "cluster_name": cluster_name
        }
    response = ecs.list_tasks(
        cluster=cluster_name,
        serviceName=service_name
    )
    task_arn = response["taskArns"]

    if not task_arn:
        return {
            "error": "No tasks found for the service",
            "cluster_name": cluster_name,
            "service_name": service_name,
            "tasks": []
        }
    tasks_response = ecs.describe_tasks(
      cluster = cluster_name,
      tasks = task_arn
    )

    # define empty task 
    tasks = []

    for task in tasks_response["tasks"]:
        tasks.append({
            "task_arn": task["taskArn"],
            "last_status": task["lastStatus"],
            "desired_status": task["desiredStatus"],
            "health_status": task["healthStatus"],
            "task_definition": task["taskDefinitionArn"]
        })
    return {
        "cluster_name": cluster_name,
        "service_name": service_name,
        "tasks": tasks
        
    }

# define function for getting stopped tasks
def get_stopped_ecs_tasks(cluster_name, service_name):
    if not cluster_name:
        return {
            "error": "Cluster name is required"
        }
    if not service_name:
        return {
            "error": "Service name is required",
            "cluster_name": cluster_name
        }
    print(
    f"Checking STOPPED tasks for "
    f"cluster={cluster_name}, service={service_name}"
    )
    response = ecs.list_tasks(
        cluster=cluster_name,
        serviceName=service_name,
        desiredStatus="STOPPED"
    )
    task_arn = response["taskArns"]

    if not task_arn:
        return {
            "error": "No tasks found for the service",
            "cluster_name": cluster_name,
            "service_name": service_name,
            "stopped_tasks": []
        }
    tasks_response = ecs.describe_tasks(
      cluster = cluster_name,
      tasks = task_arn
    )

    # define empty task 
    stopped_tasks = []

    for task in tasks_response["tasks"]:
        stopped_tasks.append({
            "task_arn": task["taskArn"],
            "last_status": task["lastStatus"],
            "desired_status": task["desiredStatus"],
            "health_status": task["healthStatus"],
            "stop_code": task.get("stopCode"),
            "stopped_reason": task.get("stoppedReason"),
            "task_definition": task["taskDefinitionArn"]
        })
    return {
        "cluster_name": cluster_name,
        "service_name": service_name,
        "tasks": stopped_tasks
        
    }

# ============================================================
# AGENT STATE, We are not currenlty usin this state and planner
# ============================================================

agent_state = {
    "cluster": None,
    "services": None,
    "selected_service": None,
    "service_status": None,
    "next_action": None
}


# ============================================================
# PLANNER
# ============================================================

def determine_next_action(state):

    # No cluster known
    if not state["cluster"]:
        return "discover_cluster"

    # Cluster known but services haven't been discovered
    if state["services"] is None:
        return "discover_services"

    # We checked AWS and found zero services
    if len(state["services"]) == 0:
        return "no_services"

    # Service hasn't been selected
    if state["selected_service"] is None:

        # Exactly one service
        if len(state["services"]) == 1:
            return "select_service"

        # More than one service
        return "ask_user"

    # Service selected but status not checked
    if state["service_status"] is None:
        return "check_service_status"

    # Everything needed for this workflow is known
    return "done"


# ============================================================
# DISPLAY STATE
# ============================================================

def print_state(state):

    print("\n---------------- AGENT STATE ----------------")

    print(
        json.dumps(
            state,
            indent=2
        )
    )

    print("----------------------------------------------")


# Define tool description
tools = [
    {
        "type": "function",
        "name": "get_ecs_service_status",
        "description": """
        Get the current status of a specific ECS service.

        IMPORTANT:
        Call this tool ONLY when both cluster_name and
        service_name are known.

        Never call this tool with an empty service_name.
        If the service name is unknown, first use
        list_ecs_services to discover the services.
        """,
        "parameters": {
            "type": "object",
            "properties": {
              "cluster_name": {
                "type": "string",
                "description": "Name of the ECS cluster to check."
              },
              "service_name": {
                "type": "string",
                "description": "Name of the ECS service to check."
              }
            },
            "required": ["cluster_name", "service_name"],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "list_ecs_clusters",
        "description": "List the ecs clusters",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "list_ecs_services",
        "description": """
        List all ECS services in a specific cluster.

        Use this tool when the cluster name is known but
        the service name is unknown.
        """,
        "parameters": {
            "type": "object",
            "properties": {
              "cluster_name": {
                "type": "string",
                "description": "Name of the ECS cluster"
              },
            },
            "required": ["cluster_name"],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "get_ecs_tasks",
        "description": """
        Get the current ECS tasks for a specific service.

        Use this only when both cluster_name and service_name
        are known.

        This tool is useful for investigating the task state
        of an ECS service.
        """,
        "parameters": {
            "type": "object",
            "properties": {
              "cluster_name": {
                "type": "string",
                "description": "Name of the ECS cluster"
              },
              "service_name": {
                "type": "string",
                "description": "Name of the ECS service"
              },
            },
            "required": ["cluster_name", "service_name"],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "get_stopped_ecs_tasks",
        "description": """
        Get recently stopped ECS tasks for a specific service.
    
        Use this when a service has no running tasks,
        tasks are failing, or task failure investigation
        is required.
    
        Requires both cluster_name and service_name.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "cluster_name": {
                    "type": "string",
                    "description": "Name of the ECS cluster."
                },
                "service_name": {
                    "type": "string",
                    "description": "Name of the ECS service."
                }
            },
            "required": [
                "cluster_name",
                "service_name"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
]

# -------------------------
# First LLM call
# -------------------------

user_query = input("Please enter your query: ")

#calling the LLM to get the status of a service
response = client.responses.create(
    model="gpt-5.4-mini",
    input=user_query,
    instructions="""
    You are an AWS ECS troubleshooting assistant.
    
    You have three tools:
    
    1. list_ecs_clusters
       Use this to discover ECS clusters.
    
    2. list_ecs_services
       Use this when you know the cluster but do not know
       the service name.
    
    3. get_ecs_service_status
       Use this only when you know BOTH the cluster name
       and the service name.
    4. get_ecs_task
       Use this only when you know both cluster name and
       the service name. 
    5. get_stopped_ecs_tasks
       similar to get_ecs_task tool but additional 
       Use this only when no tasks is running
    
    Rules:
    
    - Never use an empty string for a required tool argument.
    - Never invent a service name.
    - If the user gives a cluster name but does not give
      a service name, first call list_ecs_services.
    - If list_ecs_services returns no services, report that
      the cluster has no ECS services.
    - If user gives service name but no cluster name, first call list_ecs_clusters.
      else report no service found in any of the clusters.
    - If user ask status of task and provide service name but do not provide
      cluster name first discover cluster name
    - Use tool results as the source of truth.
    - Do not invent AWS resource names or infrastructure state.
    """,
    tools=tools
    )

# Keep the original response ID
# previous_response_id = response.id



print("LLM response output:", response.output)

# -------------------------
# Agent loop
# -------------------------

while True:

  tool_outputs = []

  for item in response.output:
    if item.type == "function_call":
      #print("Tool name:", item.name)
      #print("Tool arguments:", item.arguments)

      # Convert JSON arguments into Python dictionary instead of simple text
      arguments = json.loads(item.arguments)

      # -------------------------
      # Tool 1
      # -------------------------
  
      if item.name == "list_ecs_clusters":

        #print("Executing tools list_ecs_clusters()")
        result = list_ecs_clusters()

      # -------------------------
      # Tool 2
      # -------------------------

      elif item.name == "list_ecs_services":
  
        result = list_ecs_services(
          arguments["cluster_name"]
        )

      # -------------------------
      # Tool 3
      # -------------------------
      elif item.name == "get_ecs_service_status":
        #print("calling the tools...", item.name)


        # store the cluster name and ecs service details in variables
        cluster_name = arguments["cluster_name"]
        service_name = arguments["service_name"]

        if not cluster_name or not service_name:
          result = {
            "error": "Cannot check service status because "
                     "cluster_name and service_name are required.",
            "cluster_name": cluster_name,
            "service_name": service_name
          }
        else:
          # calling function to get the status of a service
          result = get_ecs_service_status(cluster_name, service_name)
          #print("Server status:", result)
      
      # -------------------------
      # Tool 4 
      # -------------------------      
      elif item.name == "get_ecs_tasks":
        #print("calling the tools...", item.name)

        # store the cluster name and ecs service details in variables
        cluster_name = arguments["cluster_name"]
        service_name = arguments["service_name"]

        if not cluster_name or not service_name:
          result = {
            "error": "Cannot check service status because "
                     "cluster_name and service_name are required.",
            "cluster_name": cluster_name,
            "service_name": service_name
          }
        else:
          # calling function to get the status of a service
          result = get_ecs_tasks(cluster_name, service_name)
          #print(json.dumps(result, indent=2))

      # -------------------------
      # Tool 5
      # -------------------------
      elif item.name == "get_stopped_ecs_tasks":
      
          cluster_name = arguments["cluster_name"]
          service_name = arguments["service_name"]
      
          if not cluster_name or not service_name:
      
              result = {
                  "error": (
                      "Cannot get stopped tasks because "
                      "cluster_name and service_name are required."
                  ),
                  "cluster_name": cluster_name,
                  "service_name": service_name
              }
      
          else:
      
              result = get_stopped_ecs_tasks(
                  cluster_name,
                  service_name
              )
      
          print( "stopped tasks are: ",
              json.dumps(
                  result,
                  indent=2
              )
          )          


      else:
        result = {
          "error": f"Unknown tool: {item.name}"
        }

      print("Tool result:")
      print(json.dumps(result, indent=2))

      # -------------------------
      # Collect result
      # -------------------------
      tool_outputs.append({
          "type": "function_call_output",
          "call_id": item.call_id,
          "output": json.dumps(result)
      })

    # -------------------------
    # No tool calls = final answer
    # -------------------------
  if not tool_outputs:
    break

  # -------------------------
  # Send tool results to LLM
  # -------------------------

# Send the all the tool results back to the LLM for further processing
  response = client.responses.create(
    model="gpt-5.4-mini",
    previous_response_id = response.id,
    input=tool_outputs,
    tools=tools
  )

# -------------------------
# Final answer
# -------------------------

print("\nAssistant:")
print(response.output_text)

