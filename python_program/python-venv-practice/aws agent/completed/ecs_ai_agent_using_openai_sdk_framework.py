from agents import Agent, Runner, function_tool, RunContextWrapper, SQLiteSession
from dataclasses import dataclass
import json
import boto3
import time

# RunContextWrapper is a container object in the OpenAI Agents SDK that manages state,
# dependencies, and metadata during an agent's execution run without exposing those details directly to the LLM


# ============================================================
#   AWS CLIENT
# ============================================================

ecs = boto3.client(
    "ecs",
    region_name="eu-west-1"
)

cloudtrail = boto3.client(
    "cloudtrail",
    region_name="eu-west-1"
)

logs = boto3.client(
    "logs",
    region_name="eu-west-1"
)

@dataclass # @dataclass is a Python decorator that makes it easy to create a class whose main purpose is to store data
class DevOpsContext: # Create a class called DevOpsContext whose main job is to hold an environment and a region."
    environment: str
    region: str
    account_name: str

# Normal python function to Read the current ECS service state from AWS

def describe_ecs_service( context: DevOpsContext, cluster_name: str, service_name: str):
    """
    Read the current ECS service state from AWS.
    """

    if not cluster_name:
        return {
            "error": "Cluster name is required"
        }

    if not service_name:
        return {
            "error": "Service name is required"
        }

    ecs = boto3.client(
        "ecs",
        region_name=context.region
    )

    response = ecs.describe_services(
        cluster=cluster_name,
        services=[service_name]
    )

    if not response["services"]:
        return {
            "error": "Service not found",
            "cluster_name": cluster_name,
            "service_name": service_name
        }

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

# define function diagnose_ecs_service to provide dignosis based on task status whether running or not

def diagnose_ecs_service(service_status):

    desired_count = service_status["desired_count"]
    running_count = service_status["running_count"]
    pending_count = service_status["pending_count"]

    if desired_count == 0 and running_count == 0:
        return {
            "condition": "scaled_to_zero",
            "message": "The ECS service is configured with desired count 0, so no tasks are running.",
            "evidence": {
                "desired_count": desired_count,
                "running_count": running_count,
                "pending_count": pending_count
            }
        }

    if desired_count > 0 and running_count == 0 and pending_count == 0:
        return {
            "condition": "no_tasks_running",
            "message": "The service wants tasks to run, but currently has no running or pending tasks.",
            "evidence": {
                "desired_count": desired_count,
                "running_count": running_count,
                "pending_count": pending_count
            }
        }

    if pending_count > 0:
        return {
            "condition": "tasks_pending",
            "message": "The service has tasks pending that have not reached the running state yet.",
            "evidence": {
                "desired_count": desired_count,
                "running_count": running_count,
                "pending_count": pending_count
            }
        }
    if running_count < desired_count:
        return {
            "condition": "tasks_not_fully_running",
            "message": "The service has fewer running tasks than its desired count.",
            "evidence": {
                "desired_count": desired_count,
                "running_count": running_count,
                "pending_count": pending_count
            }
        }

    if running_count == desired_count and pending_count == 0:
        return {
            "condition": "desired_state_reached",
            "message": "The service has the requested number of running tasks.",
            "evidence": {
                "desired_count": desired_count,
                "running_count": running_count,
                "pending_count": pending_count
            }
        }

    return {
        "condition": "unknown",
        "message": "The current ECS service state does not match a known condition.",
        "evidence": {
            "desired_count": desired_count,
            "running_count": running_count,
            "pending_count": pending_count
        }
    }


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

        if stopped_reason and "CannotPullContainerError" in stopped_reason:
            return {
                "condition": "image_pull_failure",
                "message": (
                    "The ECS task failed to start because the container "
                    "image could not be pulled."
                ),
                "evidence": {
                    "task_status": last_status,
                    "stop_code": stop_code,
                    "stopped_reason": stopped_reason
                }
            }

        if (
            stopped_reason
            and "unable to pull secrets or registry auth" in stopped_reason
            and "Amazon ECR" in stopped_reason
        ):
            return {
                "condition": "ecr_connection_failure",
                "message": (
                    "The ECS task failed during startup because it could not "
                    "retrieve registry authentication from Amazon ECR."
                ),
                "evidence": {
                    "task_status": last_status,
                    "stop_code": stop_code,
                    "stopped_reason": stopped_reason
                }
            }

        if stopped_reason and "ResourceInitializationError" in stopped_reason:
            return {
                "condition": "resource_initialization_failure",
                "message": (
                    "The ECS task failed during resource initialization "
                    "before the container started."
                ),
                "evidence": {
                    "task_status": last_status,
                    "stop_code": stop_code,
                    "stopped_reason": stopped_reason
                }
            }

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

# define function for collecting all evidence from service_result, task_result and log_result
#@function_tool
def correlate_ecs_evidence(service_result: str, task_result: str, log_result: str=None):
    """
    Correlate ECS service, task, and CloudWatch evidence.
    """

    service_diagnosis = service_result.get("diagnosis", {})
    task_diagnosis = task_result.get("diagnosis", {})

    service_condition = service_diagnosis.get("condition")
    task_condition = task_diagnosis.get("condition")

    # No task evidence available
    if task_condition == "unknown":
        return {
            "condition": service_condition,
            "message": "Task-level evidence is insufficient to determine the cause.",
            "evidence": {
                "service": service_diagnosis,
                "task": task_diagnosis
            }
        }

    # Container exited with a failure
    if task_condition == "container_exit_failure":

        log_events = []

        if log_result:
            log_events = log_result.get("events", [])

        return {
            "condition": "container_exit_failure",
            "message": (
                "The ECS service has no running task because the "
                "container exited with a non-zero exit code."
            ),
            "evidence": {
                "service": service_diagnosis,
                "task": task_diagnosis,
                "logs": log_events
            }
        }

    # Container exited successfully
    if task_condition == "container_exited_successfully":
        return {
            "condition": "container_exited_successfully",
            "message": (
                "The container exited with code 0, but the ECS service "
                "still does not have the requested running task."
            ),
            "evidence": {
                "service": service_diagnosis,
                "task": task_diagnosis
            }
        }

    return {
        "condition": "unknown",
        "message": "The available ECS evidence is insufficient to determine the cause.",
        "evidence": {
            "service": service_diagnosis,
            "task": task_diagnosis
        }
    }

# define function to discover the list of ecs cluster
@function_tool
def list_ecs_clusters(ctx: RunContextWrapper[DevOpsContext]):
    """
    this function is used to discover the cluster
    """
    response = ecs.list_clusters()
    cluster_list = [] 
    for arn in response["clusterArns"]:
        cluster_name = arn.split("/")[-1]
        cluster_list.append(cluster_name)
    return {
      "clusters": cluster_list
    }

@function_tool
def list_ecs_services(ctx: RunContextWrapper[DevOpsContext], cluster_name: str):
    """
    it is used to list of ecs service running cluster
    """

    if not cluster_name:
        return {
            "error": "Cluster name is required"
        }

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

# Define function to Get the current status of an ECS service and return service_status and diagnosis
@function_tool # "Make this Python function available to the agent."
def get_ecs_service_status(ctx: RunContextWrapper[DevOpsContext], cluster_name: str, service_name: str):
    """
    Get the current status of an ECS service.

    Use this tool when the user asks about
    the current desired, running, or pending
    task count of an ECS service.
    """

    if not cluster_name:
        return {
            "error": "Cluster name is required"
        }

    if not service_name:
        return {
            "error": "Service name is required"
        }


    ecs = boto3.client(
        "ecs",
        region_name = ctx.context.region
    )
    response = ecs.describe_services(
        cluster=cluster_name,
        services=[service_name]
    )

    if not response["services"]:
        return {
            "error": "Service not found",
            "cluster_name": cluster_name,
            "service_name": service_name
        }

    service = response["services"][0]

    service_status = {
        "cluster_name": cluster_name,
        "service_name": service["serviceName"],
        "status": service["status"],
        "desired_count": service["desiredCount"],
        "running_count": service["runningCount"],
        "pending_count": service["pendingCount"],
        "task_definition": service["taskDefinition"]
    }

    # call diagnosis funciton to get result of task 
    diagnosis = diagnose_ecs_service(service_status)

    return {
        "service": service_status,
        "diagnosis": diagnosis
    }

# define function to verify if ecs has desire no count is running and if task is in starting then it will wait to become running
def verify_ecs_desired_count(
    context: DevOpsContext,
    cluster_name: str,
    service_name: str,
    expected_desired_count: int
):
    """
    Verify that an ECS service has reached the requested state.
    """

    ecs = boto3.client(
        "ecs",
        region_name=ctx.context.region
    )

    max_attempts = 8
    wait_seconds = 10

    for attempt in range(1, max_attempts + 1):

        response = ecs.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )

        service = response["services"][0]

        actual_desired_count = service["desiredCount"]
        running_count = service["runningCount"]
        pending_count = service["pendingCount"]

        verified = (
            actual_desired_count == expected_desired_count
            and running_count == expected_desired_count
            and pending_count == 0
        )

        print(
            f"Verification attempt {attempt}/{max_attempts}: "
            f"desired={actual_desired_count}, "
            f"running={running_count}, "
            f"pending={pending_count}, "
            f"verified={verified}"
        )

        if verified:
            return {
                "verified": True,
                "attempts": attempt,
                "cluster_name": cluster_name,
                "service_name": service_name,
                "expected_desired_count": expected_desired_count,
                "actual_desired_count": actual_desired_count,
                "running_count": running_count,
                "pending_count": pending_count,
                "status": service["status"]
            }

        if attempt < max_attempts:
            time.sleep(wait_seconds)

    return {
        "verified": False,
        "attempts": max_attempts,
        "cluster_name": cluster_name,
        "service_name": service_name,
        "expected_desired_count": expected_desired_count,
        "actual_desired_count": actual_desired_count,
        "running_count": running_count,
        "pending_count": pending_count,
        "status": service["status"]
    }

# define function Get the number of running and desired ECS tasks for a service.
@function_tool # "Make this Python function available to the agent"
def get_ecs_task_count(
    ctx: RunContextWrapper[DevOpsContext],
    cluster_name: str,
    service_name: str
):
    """
    Get the number of running and desired ECS tasks
    for a service.
    """

    ecs = boto3.client(
        "ecs",
        region_name=ctx.context.region
    )

    response = ecs.describe_services(
        cluster=cluster_name,
        services=[service_name]
    )

    service = response["services"][0]

    return {
        "desired_count": service["desiredCount"],
        "running_count": service["runningCount"],
        "pending_count": service["pendingCount"]
    }

# ============================================================
# To List the ECS tasks currently associated with a service
# ============================================================

@function_tool # "Make this Python function available to the agent."
def get_ecs_tasks(ctx: RunContextWrapper[DevOpsContext], cluster_name: str, service_name: str):

    """
    List the ECS tasks currently associated
    with a service.
    """
    if not cluster_name:
        return {
            "error": "Cluster name is required"
        }

    if not service_name:
        return {
            "error": "Service name is required"
        }

    ecs = boto3.client(
        "ecs",
        region_name=ctx.context.region
    )

    response = ecs.list_tasks(
        cluster=cluster_name,
        serviceName=service_name
    )

    task_arns = response["taskArns"]

    if not task_arns:
        return {
            "tasks": []
        }

    return {
        "cluster_name": cluster_name,
        "service_name": service_name,
        "tasks_arn": task_arns
    }

# define funciton to Get detailed information about a specific ECS task
@function_tool # "Make this Python function available to the agent."
def get_ecs_task_details(ctx: RunContextWrapper[DevOpsContext], cluster_name: str, task_arn: str):
    """
    Get detailed information about a specific ECS task.
    """
    if not cluster_name:
        return {"error": "Cluster name is required"}

    if not task_arn:
        return {"error": "Task ARN is required"}

    ecs = boto3.client(
        "ecs",
        region_name=ctx.context.region
    )

    response = ecs.describe_tasks(
        cluster=cluster_name,
        tasks=[task_arn]
    )

    if not response["tasks"]:
        return {
            "error": "Task not found",
            "task_arn": task_arn
        }

    task = response["tasks"][0]

    containers = []

    for container in task.get("containers", []):

        containers.append({
            "name": container.get("name"),
            "last_status": container.get("lastStatus"),
            "exit_code": container.get("exitCode"),
            "reason": container.get("reason"),
            "health_status": container.get("healthStatus")
        })

    task_details = {
        "task_arn": task.get("taskArn"),
        "last_status": task.get("lastStatus"),
        "desired_status": task.get("desiredStatus"),
        "health_status": task.get("healthStatus"),
        "stop_code": task.get("stopCode"),
        "stopped_reason": task.get("stoppedReason"),
        "started_at": (
            task["startedAt"].isoformat()
            if task.get("startedAt")
            else None
        ),
        "stopped_at": (
            task["stoppedAt"].isoformat()
            if task.get("stoppedAt")
            else None
        ),
        "task_definition": task.get("taskDefinitionArn"),
        "containers": containers
    }
 
    # sending task_details to diagnose_ecs_task 
    diagnosis = diagnose_ecs_task(task_details)
    
    return {
        "task": task_details,
        "diagnosis": diagnosis
    }

# define function to get list of stopped task
@function_tool
def get_ecs_stopped_tasks(
    ctx: RunContextWrapper[DevOpsContext],
    cluster_name: str,
    service_name: str,
    limit: int = 5
):
    """
    Get recently stopped ECS tasks for a service.
    """
    ecs = boto3.client(
        "ecs",
        region_name=ctx.context.region
    )

    response = ecs.list_tasks(
        cluster=cluster_name,
        serviceName=service_name,
        desiredStatus="STOPPED",
        maxResults=limit
    )

    return {
        "cluster_name": cluster_name,
        "service_name": service_name,
        "tasks": response.get("taskArns", [])
    }

# define function  get_ecs_task_logs
@function_tool
def get_ecs_task_logs(ctx: RunContextWrapper[DevOpsContext], cluster_name: str, task_arn: str, limit: int=20):

    """
    it is used to get the cloudwatch log for specific task arn
    Retrieves the most recent CloudWatch log events for a specific AWS ECS task.
    
    This tool automates the process of locating an ECS task's log configuration, 
    finding its unique CloudWatch log stream, and fetching the latest log entries. 
    Use this tool when you need to inspect application logs, debug application errors, 
    or check the runtime output of a specific ECS task.
    """
    if not cluster_name:
        return {"error": "Cluster name is required"}

    if not task_arn:
        return {"error": "Task ARN is required"}

   # AWS client connection for ecs and CloudWatch log
    ecs = boto3.client(
        "ecs",
        region_name=ctx.context.region
    )

    logs = boto3.client(
        "logs",
        region_name=context.region
    )
    # 1. Get ECS task
    task_response = ecs.describe_tasks(
        cluster=cluster_name,
        tasks=[task_arn]
    )

    if not task_response["tasks"]:
        return {
            "error": "Task not found",
            "task_arn": task_arn
        }

    task = task_response["tasks"][0]

    task_definition_arn = task["taskDefinitionArn"]

    # 2. Get task definition
    task_definition_response = ecs.describe_task_definition(
        taskDefinition=task_definition_arn
    )

    task_definition = task_definition_response["taskDefinition"]

    # 3. Find awslogs configuration
    log_group_name = None
    stream_prefix = None

    for container in task_definition["containerDefinitions"]:

        log_configuration = container.get("logConfiguration")

        if not log_configuration:
            continue

        if log_configuration.get("logDriver") != "awslogs":
            continue

        options = log_configuration.get("options", {})

        log_group_name = options.get("awslogs-group")
        stream_prefix = options.get("awslogs-stream-prefix")

        break

    if not log_group_name:
        return {
            "error": "CloudWatch log group not found",
            "task_arn": task_arn
        }

    if not stream_prefix:
        return {
            "error": "CloudWatch stream prefix not found",
            "task_arn": task_arn
        }

    # 4. Extract task ID from task_arn argument which is passed to function
    task_id = task_arn.split("/")[-1]

    # 5. Find the task's log stream from pagination technique since multiple page can be there
    paginator = logs.get_paginator("describe_log_streams")
    
    log_stream_name = None
    
    # log stream name will be search in each pages once found then break from loop
    for page in paginator.paginate(logGroupName=log_group_name, logStreamNamePrefix=stream_prefix):
    
        for stream in page.get("logStreams", []):
    
            stream_name = stream["logStreamName"]
    
            if stream_name.endswith("/" + task_id):
    
                log_stream_name = stream_name
                break # once log_stream_name match then break from inner for loop

        if log_stream_name:
            break    # once log_stream_name exist in current loop then break from outer for loop

    if not log_stream_name:
        return {
            "error": "No matching log stream found",
            "task_arn": task_arn,
            "task_id": task_id,
            "log_group_name": log_group_name
        }

    # 6. Get recent log events
    log_response = logs.get_log_events(
        logGroupName=log_group_name,
        logStreamName=log_stream_name,
        startFromHead=False, # donot get log events from begining
        limit=limit
    )

    events = []

    for event in log_response.get("events", []):

        events.append({
            "timestamp": event.get("timestamp"),
            "message": event.get("message")
        })

    return {
        "cluster_name": cluster_name,
        "task_arn": task_arn,
        "task_id": task_id,
        "log_group_name": log_group_name,
        "stream_prefix": stream_prefix,
        "log_stream_name": log_stream_name,
        "event_count": len(events),
        "events": events
    }


@function_tool
def get_environment(ctx: RunContextWrapper[DevOpsContext]): # This gives the tool access to the context associated with the current agent run.
    """
    Return the environment and AWS region from the current DevOps context.
    """
    return {
        "environment": ctx.context.environment,
        "region": ctx.context.region
    }

# define function to validate the desired count its a Guardrail will check if it is allow or not
def validate_desired_count(desired_count: int):
    if desired_count < 0:
        raise ValueError(
            "Desired count cannot be negative."
        )

    if desired_count > 10:
        raise ValueError(
            "Desired count cannot exceed 10."
        )

    return True


# define function to environment validate before human approval called
def validate_environment_for_update(context: DevOpsContext):
    if context.environment != "dev":
        return {
            "allowed": False,
            "status": "blocked",
            "reason": "environment_guardrail",
            "environment": context.environment,
            "message": f"ECS desired-count updates are not allowed in {context.environment}"
        }
    return {
        "allowed": True,
        "status": "allowed",
        "reason": None,
        "environment": context.environment,
        "message": "Environment allows the requested update."
    }

# define function for human approval required when there is a state change
def request_human_approval(
    context: DevOpsContext,
    cluster_name: str,
    service_name: str,
    request_desired: int,
    current_desired_count: int,
    current_running_count: int,
    current_pending_count: int
):
    """
    Ask a human to approve an ECS desired-count change.
    """

    print("\n================================")
    print("HUMAN APPROVAL REQUIRED")
    print("================================")
    
    print(f"Environment           : {context.environment}")
    print(f"Account               : {context.account_name}")
    print(f"Region                : {context.region}\n")
    
    print(f"Cluster               : {cluster_name}")
    print(f"Service               : {service_name}\n")

    print(f"Current desired       : {current_desired_count}")
    print(f"Current Running       : {current_running_count}")
    print(f"Current Pending       : {current_pending_count}\n")

    print(f"Requested desired     : {request_desired}\n")

    answer = input("Approve this change? (yes/no): ")

    return answer.lower() == "yes"


################################################################
# state change function to Change the desired task count of an ECS service
################################################################
@function_tool # Make this Python function available to the agent.
def update_ecs_desired_count(
    ctx: RunContextWrapper[DevOpsContext],
    cluster_name: str,
    service_name: str,
    desired_count: int):
    """
    Change the desired task count of an ECS service.
    """

    # Step 1: Validate the requested value
    validate_desired_count(desired_count)

    # Step 2: Validate environment
    environment_check = validate_environment_for_update(ctx.context)

    if not environment_check["allowed"]:
        return environment_check

    # call other fucntion to get the latest ecs task status
    service_response = describe_ecs_service(ctx.context, cluster_name, service_name)
    
    # capture ecs details
    current_desire_count = service_response["desired_count"]
    current_running_count = service_response["running_count"]
    current_pending_count = service_response["pending_count"]

    # Step 2: Ask for human approval since its a state change operation
    approved = request_human_approval(
        ctx.context, 
        cluster_name, 
        service_name, 
        desired_count, 
        current_desire_count, 
        current_running_count, 
        current_pending_count
    )

    # Step 3: Stop if human rejects the action
    if not approved:
        return {
            "status": "rejected",
            "cluster_name": cluster_name,
            "service_name": service_name,
            "desired_count": desired_count,
            "message": "Human approval was not granted."
        }

    try:
        # Eastablish AWS client connection
        ecs = boto3.client(
            "ecs",
            region_name=ctx.context.region
        )
    
        response = ecs.update_service(
            cluster=cluster_name,
            service=service_name,
            desiredCount=desired_count
        )
    
        service = response["service"]

        verification = verify_ecs_desired_count(
            ctx.context,
            cluster_name,
            service_name,
            desired_count
        )
    
        return {
            "status": (
                "updated_and_verified"
                if verification["verified"]
                else "updated_but_not_verified"
            ),
            "cluster_name": cluster_name,
            "service_name": service_name,
            "desired_count": verification["actual_desired_count"],
            "running_count": verification["running_count"],
            "pending_count": verification["pending_count"],
            "task_definition": service["taskDefinition"],
            "verified": verification["verified"],
            "message": (
                f"Successfully requested desired count "
                f"{desired_count} for {service_name} "
                f"in {cluster_name}. "
                f"Verification: {verification['verified']}."
            )
        }
    except Exception as e:
        return {
            "status": "failed",
            "cluster_name": cluster_name,
            "service_name": service_name,
            "desired_count": desired_count,
            "error": str(e),
            "message": (
                f"Failed to update {service_name} "
                f"in {cluster_name}."
            )
        }


agent = Agent(
    name="DevOps Agent",
    model="gpt-5.4-mini",
    instructions="""
    You are a DevOps ECS troubleshooting assistant.
    
    Rules:
    
    1. Always use AWS tools when the user asks for current ECS information.
    2. Never invent or assume AWS resource state.
    3. If required information such as cluster name or service name is missing,
       ask the user for it instead of guessing.
    4. Use read-only tools to gather evidence.
    5. When one tool depends on the output of another tool,
       use the required tool first.
    6. Clearly distinguish AWS facts returned by tools from your own explanation.
    7. Do not claim that an ECS resource is healthy unless the available evidence
       supports that conclusion.
    8. Do not describe guardrail, validation, approval, or application-generated
       results as AWS responses.

    9. When a tool returns a status such as "blocked", "rejected", or
       "environment_guardrail", explain that the application blocked or rejected
       the operation and mention environment, unless the tool explicitly says the result came from AWS.
    10. When the user reports an ECS service problem, first inspect
       the current ECS service status.
    
    11. After checking the service status, inspect the task count
        when needed.
    
    12. If tasks are present, inspect the relevant task details
        before explaining the problem.
    
    13. If the service diagnosis is "desired_state_reached" 
        but the user still reports that it is not working, inspect 
        the running task details and use that evidence before concluding
    
    13. Base the diagnosis only on evidence returned by the tools.
        Do not invent causes.
    
    14. If the available evidence is insufficient to determine
        the cause, clearly say what evidence is missing.
    15. If the user asks for the status of an ECS service without providing 
        the cluster details, the agent must first list the available clusters, 
        identify the correct one, and then retrieve the service status.
    16. If a stopped task has a diagnosis of "container_exit_failure", 
        call get_ecs_task_logs for that task before giving the final answer.
    """,
    tools=[
      get_ecs_service_status,
      get_ecs_task_count,
      get_ecs_tasks,
      get_ecs_task_details,
      get_environment,
      update_ecs_desired_count,
      list_ecs_clusters,
      list_ecs_services,
      get_ecs_task_logs,
      get_ecs_stopped_tasks
      ]
)

context = DevOpsContext(
    environment="dev",
    region="eu-west-1",
    account_name="nonprod"
)

session = SQLiteSession("devops_ecs_session") # SQLiteSession is a simple session implementation that stores conversation history in SQLite.

user_input = input("User: ")
result = Runner.run_sync(
    agent,
    user_input,
    context=context,
    session=session
)

print("\n==============================")
print("AGENT EXECUTION TRACE")
print("==============================")

for item in result.new_items:

    print("\nItem type:", type(item).__name__)

    if hasattr(item, "raw_item"):
        print("Raw item:")
        print(item.raw_item)

print("\n==============================")
print("FINAL ANSWER")
print("==============================")

print(result.final_output)


