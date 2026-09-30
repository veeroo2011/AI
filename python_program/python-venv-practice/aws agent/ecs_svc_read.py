import boto3
import json
from pprint import pprint
from datetime import datetime


ecs = boto3.client(
  "ecs",
  region_name = "eu-west-1")

 #1. Add this helper function to convert date objects to readable text strings
def json_datetime_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()  # Converts datetime to "2026-09-08T08:23:43..."
    raise TypeError(f"Type {type(obj)} not serializable")

## define function to get the status of a service
#def get_ecs_service_status(cluster_name, service_name):
#  response = ecs.describe_services(
#    cluster=cluster_name,
#    services=[service_name]
#  )
#
#  # control if the service not exists or its empty
#  if not response["services"]:
#    return {
#        "error": "Service not found",
#        "service_name": service_name
#    }
#  # capture the whole details of service
#  service = response["services"][0]
#  return {
#    "service_name": service["serviceName"],
#    "status": service["status"],
#    "desired_count": service["desiredCount"],
#    "running_count": service["runningCount"],
#    "pending_count": service["pendingCount"],
#    "task_definition": service["taskDefinition"]
#  }
#
## calling the function to get the status of a service
#result = get_ecs_service_status("myecs-cluster", "hotel-mysql-service")
#
##print(result)
#
#
#def list_ecs_clusters():
#    response = ecs.list_clusters()
#    cluster_list = []
#    for arn in response["clusterArns"]:
#        cluster_name = arn.split("/")[-1]
#        cluster_list.append(cluster_name)
#    return {
#      "clusters": cluster_list
#    }
#
#print("Existing ECS clusters are", list_ecs_clusters())
#
#def list_ecs_services(cluster_name):
#    response = ecs.list_services(
#      cluster=cluster_name
#    )
#    service_list = []
#    for arn in response["serviceArns"]:
#        service_name = arn.split("/")[-1]
#        service_list.append(service_name)
#
#    return service_list
#
#print(list_ecs_services("myecs-cluster"))
#
#
#def get_ecs_tasks(cluster_name, service_name):
#    if not cluster_name:
#        return {
#            "error": "Cluster name is required"
#        }
#    if not service_name:
#        return {
#            "error": "Service name is required",
#            "cluster_name": cluster_name
#        }
#    response = ecs.list_tasks(
#        cluster=cluster_name,
#        serviceName=service_name
#    )
#    task_arn = response["taskArns"]
#
#    if not task_arn:
#        return {
#            "error": "No tasks found for the service",
#            "cluster_name": cluster_name,
#            "service_name": service_name,
#            "tasks": []
#        }
#    tasks_response = ecs.describe_tasks(
#      cluster = cluster_name,
#      tasks = task_arn
#    )
#
#    # define empty task 
#    tasks = []
#
#    for task in tasks_response["tasks"]:
#        tasks.append({
#            "task_arn": task["taskArn"],
#            "last_status": task["lastStatus"],
#            "desired_status": task["desiredStatus"],
#            "health_status": task["healthStatus"],
#            "task_definition": task["taskDefinitionArn"]
#        })
#    return {
#        "cluster_name": cluster_name,
#        "service_name": service_name,
#        "tasks": tasks
#        
#    }
#
#
#raw_result = get_ecs_tasks("myecs-cluster", "hotel-mysql-service")
#
#pretty_json = json.dumps(raw_result, default=json_datetime_serializer, indent=4)

#print("Tasks for the service are:\n", pretty_json)


#def get_stopped_ecs_tasks(cluster_name, service_name):
#    if not cluster_name:
#        return {
#            "error": "Cluster name is required"
#        }
#    if not service_name:
#        return {
#            "error": "Service name is required",
#            "cluster_name": cluster_name
#        }
#    response = ecs.list_tasks(
#        cluster=cluster_name,
#        serviceName=service_name,
#        desiredStatus="STOPPED"
#    )
#    task_arn = response["taskArns"]
#
#    if not task_arn:
#        return {
#            "error": "No tasks found for the service",
#            "cluster_name": cluster_name,
#            "service_name": service_name,
#            "stopped_tasks": []
#        }
#    tasks_response = ecs.describe_tasks(
#      cluster = cluster_name,
#      tasks = task_arn
#    )
#
#    # define empty task 
#    stopped_tasks = []
#
#    for task in tasks_response["tasks"]:
#        stopped_tasks.append({
#            "task_arn": task["taskArn"],
#            "last_status": task["lastStatus"],
#            "desired_status": task["desiredStatus"],
#            "health_status": task["healthStatus"],
#            "task_definition": task["taskDefinitionArn"]
#        })
#    return {
#        "cluster_name": cluster_name,
#        "service_name": service_name,
#        "tasks": stopped_tasks
#        
#    }
#
#
#raw_result = get_stopped_ecs_tasks("myecs-cluster", "hotel-mysql-service")
#
#pretty_json = json.dumps(raw_result, default=json_datetime_serializer, indent=4)
#
#print("Tasks for the service are:\n", pretty_json)
#################################


#agent_state = {
#    "cluster": None,
#    "services": [],
#    "service_status": {},
#    "next_action": None
#}
#
#
#def determine_next_action(state):
#
#    if not state["cluster"]:
#        return "discover_cluster"
#
#    if state["services"] is None:
#        return "discover_services"
#
#    if len(state["services"]) == 0:
#        return "no_services"
#
#    if len(state["services"]) == 1:
#        return "check_service_status"
#
#    if len(state["services"]) > 1:
#        return "ask_user"
#
#    return "done"
#
#agent_state["cluster"] = "myecs-cluster"
#agent_state["services"] = None
#
#agent_state["next_action"] = determine_next_action(agent_state)
#
#print(agent_state)


def get_ecs_service_events(cluster_name, service_name):
    if not cluster_name:
        return {
            "error": "cluster name is required"
        }
    if not service_name:
        return {
            "error": "service name is required",
            "cluster name": cluster_name
        }
    response = ecs.describe_services(
      cluster=cluster_name,
      services=[service_name]
    )

    if not response["services"]:
        return {
            "error": "Service not found",
            "cluster_name": cluster_name,
            "service": service_name
        }

    service = response["services"][0]

    events = []

    for event in service.get("events",[])[:5]:
        events.append({
            "id": event.get("id"),
            "CreatedAt": (
                event.get("createdAt").isoformat()
                if event.get("createdAt")
                else None
                ),
            "message": event.get("message")
        })

    return {
        #"services": service
        #"cluster_name": cluster_name,
        #"service": service_name,
        "events": events
    }

result = get_ecs_service_events("myecs-cluster", "hotel-mysql-service")
#print(result["services"][0])
#pretty_json = json.dumps(result["events"], default=json_datetime_serializer, indent=4)
print(result)
#def get_stopped_ecs_tasks(cluster_name, service_name):
#    tasks_response = ecs.describe_tasks(
#      cluster = cluster_name,
#      tasks = task_arn
#    )