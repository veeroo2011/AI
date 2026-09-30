import boto3
ecs = boto3.client(
    "ecs",
    region_name="eu-west-1"
)
logs = boto3.client(
    "logs",
    region_name="eu-west-1"
)
# def validate_desired_count(desired_count: int):
#     if desired_count < 0:
#         raise ValueError(
#             "Desired count cannot be negative."
#         )

#     if desired_count > 10:
#         raise ValueError(
#             "Desired count cannot exceed 10."
#         )

#     return True


# def request_human_approval(
#     cluster_name: str,
#     service_name: str,
#     desired_count: int
# ):
#     """
#     Ask a human to approve an ECS desired-count change.
#     """

#     print("\n================================")
#     print("HUMAN APPROVAL REQUIRED")
#     print("================================")

#     print(f"Cluster       : {cluster_name}")
#     print(f"Service       : {service_name}")
#     print(f"New desired   : {desired_count}")

#     answer = input("Approve this change? (yes/no): ")

#     return answer.lower() == "yes"

# def update_ecs_desired_count(
#     cluster_name: str,
#     service_name: str,
#     desired_count: int
# ):
#     """
#     Change the desired task count of an ECS service.
#     """

#     validate_desired_count(desired_count)

#     print(
#         f"Would update {service_name} "
#         f"in {cluster_name} to desired count {desired_count}"
#     )

# approved = request_human_approval(
#     "myecs-cluster",
#     "hotel-mysql-service",
#     2
# )

# print("Approval result:", approved)

# def get_ecs_service_status(cluster_name: str, service_name: str):
#     """
#     Get the current status of an ECS service.

#     Use this tool when the user asks about
#     the current desired, running, or pending
#     task count of an ECS service.
#     """

#     if not cluster_name:
#         return {
#             "error": "Cluster name is required"
#         }

#     if not service_name:
#         return {
#             "error": "Service name is required"
#         }


#     # ecs = boto3.client(
#     #     "ecs",
#     #     region_name = ctx.context.region
#     # )
#     response = ecs.describe_services(
#         cluster=cluster_name,
#         services=[service_name]
#     )

#     if not response["services"]:
#         return {
#             "error": "Service not found",
#             "cluster_name": cluster_name,
#             "service_name": service_name
#         }

#     service = response["services"][0]

#     return {
#         "cluster_name": cluster_name,
#         "service_name": service["serviceName"],
#         "status": service["status"],
#         "desired_count": service["desiredCount"],
#         "running_count": service["runningCount"],
#         "pending_count": service["pendingCount"],
#         "task_definition": service["taskDefinition"]
#     }

# response = get_ecs_service_status("myecs-cluster", "hotel-mysql-service")
# # print(f"Cluster               : {cluster}")
# # print(f"Service               : {service}")
# print(f"Current desired       : {response["desired_count"]}")
# print(f"Current Running       : {response["running_count"]}")
# print(f"Current Pending       : {response["pending_count"]}")

# def diagnose_ecs_service(service_status):

#     desired_count = service_status["desired_count"]
#     running_count = service_status["running_count"]
#     pending_count = service_status["pending_count"]

#     if desired_count == 0 and running_count == 0:
#         return {
#             "condition": "scaled_to_zero",
#             "message": "The ECS service is configured with desired count 0, so no tasks are running.",
#             "evidence": {
#                 "desired_count": desired_count,
#                 "running_count": running_count,
#                 "pending_count": pending_count
#             }
#         }

#     if desired_count > 0 and running_count == 0 and pending_count == 0:
#         return {
#             "condition": "no_tasks_running",
#             "message": "The service wants tasks to run, but currently has no running or pending tasks.",
#             "evidence": {
#                 "desired_count": desired_count,
#                 "running_count": running_count,
#                 "pending_count": pending_count
#             }
#         }

#     if pending_count > 0:
#         return {
#             "condition": "tasks_pending",
#             "message": "The service has tasks pending that have not reached the running state yet.",
#             "evidence": {
#                 "desired_count": desired_count,
#                 "running_count": running_count,
#                 "pending_count": pending_count
#             }
#         }
#     if running_count < desired_count:
#         return {
#             "condition": "tasks_not_fully_running",
#             "message": "The service has fewer running tasks than its desired count.",
#             "evidence": {
#                 "desired_count": desired_count,
#                 "running_count": running_count,
#                 "pending_count": pending_count
#             }
#         }

#     if running_count == desired_count and pending_count == 0:
#         return {
#             "condition": "desired_state_reached",
#             "message": "The service has the requested number of running tasks.",
#             "evidence": {
#                 "desired_count": desired_count,
#                 "running_count": running_count,
#                 "pending_count": pending_count
#             }
#         }

#     return {
#         "condition": "unknown",
#         "message": "The current ECS service state does not match a known condition.",
#         "evidence": {
#             "desired_count": desired_count,
#             "running_count": running_count,
#             "pending_count": pending_count
#         }
#     }

# test_service_status = {
#     "desired_count": 2,
#     "running_count": 1,
#     "pending_count": 1
# }

# diagnosis = diagnose_ecs_service(test_service_status)

# print("\nDIAGNOSIS")
# print(diagnosis)

# define function which is version 2 of get_ecs_task_logs
# def get_ecs_task_logs(cluster_name, task_arn, limit=20):

#     if not cluster_name:
#         return {"error": "Cluster name is required"}

#     if not task_arn:
#         return {"error": "Task ARN is required"}

#     # 1. Get ECS task
#     task_response = ecs.describe_tasks(
#         cluster=cluster_name,
#         tasks=[task_arn]
#     )

#     if not task_response["tasks"]:
#         return {
#             "error": "Task not found",
#             "task_arn": task_arn
#         }

#     task = task_response["tasks"][0]

#     task_definition_arn = task["taskDefinitionArn"]

#     # 2. Get task definition
#     task_definition_response = ecs.describe_task_definition(
#         taskDefinition=task_definition_arn
#     )

#     task_definition = task_definition_response["taskDefinition"]

#     # 3. Find awslogs configuration
#     log_group_name = None
#     stream_prefix = None

#     for container in task_definition["containerDefinitions"]:

#         log_configuration = container.get("logConfiguration")

#         if not log_configuration:
#             continue

#         if log_configuration.get("logDriver") != "awslogs":
#             continue

#         options = log_configuration.get("options", {})

#         log_group_name = options.get("awslogs-group")
#         stream_prefix = options.get("awslogs-stream-prefix")

#         break

#     if not log_group_name:
#         return {
#             "error": "CloudWatch log group not found",
#             "task_arn": task_arn
#         }

#     if not stream_prefix:
#         return {
#             "error": "CloudWatch stream prefix not found",
#             "task_arn": task_arn
#         }

#     # 4. Extract task ID from task_arn argument which is passed to function
#     task_id = task_arn.split("/")[-1]

#     # 5. Find the task's log stream from pagination technique since multiple page can be there
#     paginator = logs.get_paginator("describe_log_streams")
    
#     log_stream_name = None
    
#     # log stream name will be search in each pages once found then break from loop
#     for page in paginator.paginate(logGroupName=log_group_name, logStreamNamePrefix=stream_prefix):
    
#         for stream in page.get("logStreams", []):
    
#             stream_name = stream["logStreamName"]
    
#             if stream_name.endswith("/" + task_id):
    
#                 log_stream_name = stream_name
#                 break # once log_stream_name match then break from inner for loop

#         if log_stream_name:
#             break    # once log_stream_name exist in current loop then break from outer for loop

#     if not log_stream_name:
#         return {
#             "error": "No matching log stream found",
#             "task_arn": task_arn,
#             "task_id": task_id,
#             "log_group_name": log_group_name
#         }

#     # 6. Get recent log events
#     log_response = logs.get_log_events(
#         logGroupName=log_group_name,
#         logStreamName=log_stream_name,
#         startFromHead=False, # donot get log events from begining
#         limit=limit
#     )

#     events = []

#     for event in log_response.get("events", []):

#         events.append({
#             "timestamp": event.get("timestamp"),
#             "message": event.get("message")
#         })

#     return {
#         "cluster_name": cluster_name,
#         "task_arn": task_arn,
#         "task_id": task_id,
#         "log_group_name": log_group_name,
#         "stream_prefix": stream_prefix,
#         "log_stream_name": log_stream_name,
#         "event_count": len(events),
#         "events": events
#     }

# result=get_ecs_task_logs(
#     cluster_name="myecs-cluster",
#     task_arn="arn:aws:ecs:eu-west-1:997554581092:task/myecs-cluster/f6b87058ed2e41e3b008736d5e4a02ca",
#     # container_name="Main"
# )
# print(result)

def diagnose_ecs_task(task_details):
    """
    Deterministically diagnose an ECS task using task evidence.
    """

    if not task_details:
        return {
            "condition": "no_task_details",
            "message": "No task details were provided.",
            "evidence": {}
        }

    last_status = task_details.get("last_status")
    stop_code = task_details.get("stop_code")
    stopped_reason = task_details.get("stopped_reason")
    containers = task_details.get("containers", [])

    if stop_code == "TaskFailedToStart":
        return {
            "condition": "task_failed_to_start",
            "message": (
                "The ECS task failed to start before the container "
                "reached the running state."
            ),
            "evidence": {
                "task_status": last_status,
                "stop_code": stop_code,
                "stopped_reason": stopped_reason
            }
        }

    # Check container-level evidence
    for container in containers:
        exit_code = container.get("exit_code")
        container_reason = container.get("reason")
        container_status = container.get("last_status")

        if container_status == "STOPPED" and exit_code is not None:
        
            if exit_code == 0:
                return {
                    "condition": "container_exited_successfully",
                    "message": (
                        f"Container '{container.get('name')}' stopped "
                        "with exit code 0."
                    ),
                    "evidence": {
                        "task_status": last_status,
                        "stop_code": stop_code,
                        "stopped_reason": stopped_reason,
                        "container_name": container.get("name"),
                        "container_status": container_status,
                        "exit_code": exit_code,
                        "container_reason": container_reason
                    }
                }
        
            return {
                "condition": "container_exit_failure",
                "message": (
                    f"Container '{container.get('name')}' stopped "
                    f"with exit code {exit_code}."
                ),
                "evidence": {
                    "task_status": last_status,
                    "stop_code": stop_code,
                    "stopped_reason": stopped_reason,
                    "container_name": container.get("name"),
                    "container_status": container_status,
                    "exit_code": exit_code,
                    "container_reason": container_reason
                }
            }

    return {
        "condition": "unknown",
        "message": "The available task evidence is insufficient to determine the failure.",
        "evidence": {
            "task_status": last_status,
            "stop_code": stop_code,
            "stopped_reason": stopped_reason
        }
    }
task_details = {
    "task_arn": "arn:aws:ecs:eu-west-1:997554581092:task/myecs-cluster/12f3519817874758a75641a2cc64fd92",
    "last_status": "STOPPED",
    "desired_status": "STOPPED",
    "health_status": "UNKNOWN",
    "stop_code": "TaskFailedToStart",
    "stopped_reason": "CannotPullContainerError: image not found",
    "started_at": None,
    "stopped_at": "2026-09-27T12:49:34.015000+05:30",
    "task_definition": "arn:aws:ecs:eu-west-1:997554581092:task-definition/hotel-mysql-task:2",
    "containers": [
        {
            "name": "Main",
            "last_status": "STOPPED",
            "exit_code": 125,
            "reason": None,
            "health_status": "UNKNOWN"
        }
    ]
}

print(diagnose_ecs_task(task_details))

# def correlate_ecs_evidence(service_result, task_result, log_result=None):
#     """
#     Correlate ECS service, task, and CloudWatch evidence.
#     """

#     service_diagnosis = service_result.get("diagnosis", {})
#     task_diagnosis = task_result.get("diagnosis", {})

#     service_condition = service_diagnosis.get("condition")
#     task_condition = task_diagnosis.get("condition")

#     # No task evidence available
#     if task_condition == "unknown":
#         return {
#             "condition": service_condition,
#             "message": "Task-level evidence is insufficient to determine the cause.",
#             "evidence": {
#                 "service": service_diagnosis,
#                 "task": task_diagnosis
#             }
#         }

#     # Container exited with a failure
#     if task_condition == "container_exit_failure":

#         log_events = []

#         if log_result:
#             log_events = log_result.get("events", [])

#         return {
#             "condition": "container_exit_failure",
#             "message": (
#                 "The ECS service has no running task because the "
#                 "container exited with a non-zero exit code."
#             ),
#             "evidence": {
#                 "service": service_diagnosis,
#                 "task": task_diagnosis,
#                 "logs": log_events
#             }
#         }

#     # Container exited successfully
#     if task_condition == "container_exited_successfully":
#         return {
#             "condition": "container_exited_successfully",
#             "message": (
#                 "The container exited with code 0, but the ECS service "
#                 "still does not have the requested running task."
#             ),
#             "evidence": {
#                 "service": service_diagnosis,
#                 "task": task_diagnosis
#             }
#         }

#     return {
#         "condition": "unknown",
#         "message": "The available ECS evidence is insufficient to determine the cause.",
#         "evidence": {
#             "service": service_diagnosis,
#             "task": task_diagnosis
#         }
#     }

# service_result = {
#     "diagnosis": {
#         "condition": "no_tasks_running",
#         "message": "The service wants tasks to run.",
#         "evidence": {
#             "desired_count": 1,
#             "running_count": 0,
#             "pending_count": 0
#         }
#     }
# }

# task_result = {
#     "diagnosis": {
#         "condition": "container_exit_failure",
#         "message": "Container 'Main' stopped with exit code 1.",
#         "evidence": {
#             "task_status": "STOPPED",
#             "stop_code": "EssentialContainerExited",
#             "exit_code": 1
#         }
#     }
# }

# log_result = {
#     "events": [
#         {
#             "timestamp": 1790497008549,
#             "message": "AI AGENT TEST FAILURE"
#         }
#     ]
# }

service_result = {
    "diagnosis": {
        "condition": "no_tasks_running"
    }
}

task_result = {
    "diagnosis": {
        "condition": "container_exit_failure"
    }
}

log_result = {
    "events": [
        {"message": "AI AGENT TEST FAILURE"}
    ]
}
# print(
#     correlate_ecs_evidence(
#         service_result,
#         task_result,
#         log_result
#     )
# )
