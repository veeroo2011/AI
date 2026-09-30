import json
import boto3
from openai import OpenAI
import time


# ============================================================
# OpenAI CLIENT
# ============================================================
client = OpenAI()

# ============================================================
# AWS CLIENT
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
# ============================================================
# Define LLM function
# ============================================================

def generate_llm_diagnosis(state):

    evidence_analysis = state["evidence_analysis"]

    prompt = f"""
You are an AWS ECS troubleshooting assistant.

Analyze the ECS incident using the evidence analysis below.

IMPORTANT RULES:
- Treat the evidence analysis as observed/deterministically derived facts.
- Do not invent AWS resource state.
- Do not ignore contradictions between different evidence sources.
- Clearly distinguish facts from possible explanations.
- Do not treat an old service event as the cause of a newer event unless the timestamps support that conclusion.
- Respect the incident_type and incident_confidence calculated by the evidence analysis.
- If evidence_conflict is true, explicitly mention the conflict.
- If incident_confidence is LOW or MEDIUM, do not present the incident classification as certain.
- Do not claim that a CloudTrail actor performed the action when cloudtrail_actor_found is false.

Provide:

1. Current service condition
2. What happened to the investigated task
3. What CloudWatch shows
4. What CloudTrail shows
5. Relationship between the evidence
6. Likely explanation
7. What should be checked next

Evidence analysis:

{json.dumps(evidence_analysis, indent=2)}

Raw evidence:

Service status:
{json.dumps(state["service_status"], indent=2)}

Stopped tasks:
{json.dumps(state["stopped_tasks"], indent=2)}

Task details:
{json.dumps(state["task_details"], indent=2)}

CloudTrail:
{json.dumps(state["cloudtrail_event"], indent=2)}

CloudWatch:
{json.dumps(state["cloudwatch_logs"], indent=2)}

Service events:
{json.dumps(state["service_events"], indent=2)}
"""

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=prompt
    )

    return response.output_text

# ============================================================
# TOOL 1: LIST ECS CLUSTERS
# ============================================================

def list_ecs_clusters():

    response = ecs.list_clusters()

    clusters = []

    for arn in response["clusterArns"]:
        cluster_name = arn.split("/")[-1]
        clusters.append(cluster_name)

    return {
        "clusters": clusters
    }


# ============================================================
# TOOL 2: LIST ECS SERVICES
# ============================================================

def list_ecs_services(cluster_name):

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


# ============================================================
# TOOL 3: GET ECS SERVICE STATUS
# ============================================================

def get_ecs_service_status(cluster_name, service_name):

    if not cluster_name:
        return {
            "error": "Cluster name is required"
        }

    if not service_name:
        return {
            "error": "Service name is required"
        }

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


# ============================================================
# TOOL 4: GET RUNNING ECS TASKS
# ============================================================

def get_ecs_tasks(cluster_name, service_name):

    if not cluster_name:
        return {
            "error": "Cluster name is required"
        }

    if not service_name:
        return {
            "error": "Service name is required"
        }

    response = ecs.list_tasks(
        cluster=cluster_name,
        serviceName=service_name
    )

    task_arns = response["taskArns"]

    if not task_arns:
        return {
            #"cluster_name": cluster_name,
            #"service_name": service_name,
            "tasks": []
        }

    tasks_response = ecs.describe_tasks(
        cluster = cluster_name,
        tasks = task_arns
    )

    tasks = []

    for task in tasks_response["tasks"]:

        tasks.append({
            "task_arn": task["taskArn"],
            "last_status": task["lastStatus"],
            "desired_status": task["desiredStatus"],
            "health_status": task.get("healthStatus"),
            "task_definition": task["taskDefinitionArn"]
        })

    return {
        #"cluster_name": cluster_name,
        #"service_name": service_name,
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

# Define function for describe service

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

    # Executing loop for first 10 events
    for event in service.get("events",[])[:10]:
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
        "cluster_name": cluster_name,
        "service": service_name,
        "events": events
    }
# define function for diagnosis

def diagnose_failure(state):
    service_status = state["service_status"]
    stopped_tasks = state["stopped_tasks"]

    if service_status["desired_count"] == 0:
        result = "No ECS task is running and this is expected because desired count is 0."
    elif not stopped_tasks:
        result = "No stopped tasks were found."
    else:
        result = reason_summary(stopped_tasks)
    
    return result
    

def reason_summary(state):

    # Set initial value to zero
    UserInitiated = 0
    ServiceSchedulerInitiated = 0
    user_stopped = 0
    service_stopped = 0


    for task in agent_state["stopped_tasks"]["tasks"]:
        if task["stop_code"] == "UserInitiated":
            UserInitiated +=1 
        elif task["stop_code"] == "ServiceSchedulerInitiated":
            ServiceSchedulerInitiated += 1
        if task["stopped_reason"] == "Task stopped by user":
            user_stopped += 1
        elif task["stopped_reason"].startswith("Scaling activity initiated by "):
            service_stopped += 1
    return {
        "stop_code_summary": {
          "UserInitiated": UserInitiated,
          "ServiceSchedulerInitiated": ServiceSchedulerInitiated
        },
        "reason_summary": {
          "Task stopped by user": user_stopped,
          "Scaling activity initiated by deployment": service_stopped
        }
    }

# define function for stopped task
def analyze_stopped_tasks(state):

    service_status = state["service_status"]
    stopped_tasks = state["stopped_tasks"]
    service_events = state["service_events"]

    tasks = stopped_tasks.get("tasks", []) if stopped_tasks else []

    user_initiated = 0
    scheduler_initiated = 0

    for task in tasks:
        if task["stop_code"] == "UserInitiated":
            user_initiated += 1
        if task["stop_code"] == "ServiceSchedulerInitiated":
            scheduler_initiated += 1

    event_message = []
    
    # Collecting only message from events
    if service_events:
        for event in service_events.get("events", []):
            message = event.get("message", "")
            event_message.append(message)

    #Collecting only message which has start keyword from events
    task_start_events = []
    if event_message:
        for message in event_message:
            if "started" in message:
                task_start_events.append(message)
    
    failure_events = []
    failed_keyword = ["failed", "error", "unable", "cannot", "failure" ]
    if event_message:
        for message in event_message:
            for keyword in failed_keyword:
                if keyword in message:
                    failure_events.append(message)

    return {
        "service_unhealthy": (
            service_status["running_count"]
            < service_status["desired_count"]
        ),
        "desired_count": service_status["desired_count"],
        "running_count": service_status["running_count"],
        "stopped_task_count": len(tasks),    
        "user_initiated": user_initiated,
        "scheduler_initiated": scheduler_initiated,
        "Total task_started_events": len(task_start_events),
        "failure_events": failure_events,
        "repeated_task_starts": len(task_start_events) > 1
    }

# Define helper function to check if task is still starting

def has_starting_task(state):
    tasks_status = state["tasks"]["tasks"]

    for status in tasks_status:
        if status["last_status"] in  ["PROVISIONING","PENDING","ACTIVATING"]:
            return True
    return False

# define function to get more details about specific tasks

def get_ecs_task_details(cluster_name, task_arn):

    if not cluster_name:
        return {"error": "Cluster name is required"}

    if not task_arn:
        return {"error": "Task ARN is required"}

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

    return {
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

# Define function for classify ecs task failure
def classify_ecs_task_failure(task_details):

    if not task_details:
        return {
            "failure_stage": "unknown",
            "failure_type": "unknown",
            "reason": "Task details are not available"
        }

    stop_code = task_details.get("stop_code")
    stopped_reason = task_details.get("stopped_reason") or ""

    # return when task is terminated by user
    if stop_code == "UserInitiated":
        return {
            "failure_stage": "task_termination",
            "failure_type": "USER_INITIATED_STOP",
            "container_started": True,
            "application_logs_expected": True,
            "stopped_reason": stopped_reason
        }

    if stop_code == "TaskFailedToStart":

        reason_lower = stopped_reason.lower()

        # ECR authorization / permission failure
        if (
            "amazon ecr" in reason_lower
            or "ecr:" in reason_lower
            or "getauthorizationtoken" in reason_lower
            or "registry auth" in reason_lower
            or "cannot pull" in reason_lower
        ):
            if (
                "accessdeniedexception" in reason_lower
                or "access denied" in reason_lower
                or "not authorized" in reason_lower
                or "unauthorized" in reason_lower
            ):
                return {
                    "failure_stage": "task_startup",
                    "failure_type": "ECR_AUTHORIZATION",
                    "container_started": False,
                    "application_logs_expected": False,
                    "stopped_reason": stopped_reason
                }
            # Generic network/connectivity failure
            if (
                "connection" in reason_lower
                or "network" in reason_lower
                or "connection refused" in reason_lower
                or "connection timeout" in reason_lower
                or "connection reset" in reason_lower
                or "timeout" in reason_lower
                or "i/o timeout" in reason_lower
            ):
                return {
                    "failure_stage": "task_startup",
                    "failure_type": "NETWORK_CONNECTIVITY",
                    "container_started": False,
                    "application_logs_expected": False,
                    "stopped_reason": stopped_reason
                }

        # Secrets Manager related failure
        if (
            "secretsmanager" in reason_lower
            or "secrets manager" in reason_lower
            or "unable to retrieve secrets" in reason_lower
        ):
            return {
                "failure_stage": "task_startup",
                "failure_type": "SECRETS_MANAGER",
                "container_started": False,
                "application_logs_expected": False,
                "stopped_reason": stopped_reason
            }

        return {
            "failure_stage": "task_startup",
            "failure_type": "OTHER_STARTUP_FAILURE",
            "container_started": False,
            "application_logs_expected": False,
            "stopped_reason": stopped_reason
        }

    containers = task_details.get("containers", [])

    for container in containers:

        if container.get("last_status") == "STOPPED":

            return {
                "failure_stage": "container",
                "failure_type": "ContainerStopped",
                "container_started": True,
                "application_logs_expected": True,
                "container_name": container.get("name"),
                "exit_code": container.get("exit_code"),
                "reason": container.get("reason")
            }

    return {
        "failure_stage": "unknown",
        "failure_type": "Unknown",
        "container_started": None,
        "application_logs_expected": None,
        "stopped_reason": stopped_reason
    }


# define function for inspecting specific stopped task details

def get_ecs_stop_task_cloudtrail_event(cluster_name, task_arn):

    if not cluster_name:
        return {"error": "Cluster name is required"}

    if not task_arn:
        return {"error": "Task ARN is required"}

    response = cloudtrail.lookup_events(
        LookupAttributes=[
            {
                "AttributeKey": "EventName",
                "AttributeValue": "StopTask"
            }
        ],
        MaxResults=1000
    )

    for event in response.get("Events", []):
        cloudtrail_event = json.loads(
            event["CloudTrailEvent"]
        )

        requestParameters = cloudtrail_event["requestParameters"]
        event_cluster_name = requestParameters["cluster"]
        event_task = requestParameters["task"]
        print(f"event_task is {event_task} and task_arn is {task_arn} and cluster_name is {cluster_name}")

        if (task_arn == event_task and cluster_name == event_cluster_name):

            userIdentity = cloudtrail_event.get("userIdentity",{})
    
            return {
                "task_arn": task_arn,
                "cluster_name": cluster_name,
                "event_name": cloudtrail_event.get("eventName"),
                "event_time": cloudtrail_event.get("eventTime"),
                "username": userIdentity["userName"],
                "identity_type": userIdentity["type"],
                "source_ip": cloudtrail_event.get("sourceIPAddress"),
                "user_agent": cloudtrail_event.get("userAgent")
            }

    return {
        "task_arn": task_arn,
        "cluster_name": cluster_name,
        "event_found": False
    }

# Define function for analyze_ecs_evidence
def analyze_ecs_evidence(state):

    service_status = state["service_status"]
    stopped_tasks = state["stopped_tasks"]
    task_details = state["task_details"]
    failure_classification = state["failure_classification"]
    cloudwatch_logs = state["cloudwatch_logs"]
    cloudtrail_event = state["cloudtrail_event"]

    tasks = stopped_tasks.get("tasks", []) if stopped_tasks else []
    
    analysis = {
        "service_below_desired_capacity": False,
        "stopped_task_count": len(tasks),
        "user_initiated_task": False,
        "container_exit_code": None,
        "cloudtrail_actor_found": False,
        "likely_external_stop": False,

        "cloudwatch_available": False,
        "log_event_count": 0,
        "application_started": False,
        "application_ready": False,
        "application_shutdown": False,
        "failure_stage": None,
        "failure_type": None,
        "incident_type": None,
        "incident_confidence": None,
        "evidence_conflict": False,
        "evidence_conflict_reason": None
    }

    # 1. Check desired vs running count
    if service_status["desired_count"] > service_status["running_count"]:
        analysis["service_below_desired_capacity"] = True

    # 2. Check selected task stop code
    if task_details:
        if task_details["stop_code"] == "UserInitiated":
            analysis["user_initiated_task"] = True

        containers = task_details.get("containers", {})
        if containers:
            analysis["container_exit_code"] = containers[0].get("exit_code")
 
    # 3. Check CloudTrail
    if cloudtrail_event:
        if cloudtrail_event.get("event_name") == "StopTask":
            if cloudtrail_event.get("username"):
                analysis["cloudtrail_actor_found"] = True

    # check failure_classification
    if failure_classification:
       analysis["failure_stage"] = failure_classification.get("failure_stage")
    
       analysis["failure_type"] = failure_classification.get("failure_type")

    # --------------------------------
    # 4. CloudWatch logs
    # --------------------------------

    if cloudwatch_logs:

        events = cloudwatch_logs.get("events", [])

        analysis["cloudwatch_available"] = bool(events)

        analysis["log_event_count"] = len(events)

        for event in events:

            message = event.get("message", "").lower()

            if "starting as process" in message:
                analysis["application_started"] = True

            if "ready for connections" in message:
                analysis["application_ready"] = True

            if "shutdown complete" in message:
                analysis["application_shutdown"] = True

    

    # 4. Combine evidence
    if (
        analysis["user_initiated_task"]
        and analysis["cloudtrail_actor_found"]
    ):
        analysis["likely_external_stop"] = True

    if analysis["failure_type"] == "USER_INITIATED_STOP":
    
        analysis["incident_type"] = "USER_INITIATED_TERMINATION"
    
        if (
            analysis["user_initiated_task"]
            and analysis["cloudtrail_actor_found"]
            and analysis["application_started"]
            and analysis["application_shutdown"]
            and analysis["container_exit_code"] == 0
        ):
            analysis["incident_confidence"] = "HIGH"
    
        elif (
            analysis["user_initiated_task"]
            and analysis["application_started"]
        ):
            analysis["incident_confidence"] = "MEDIUM"
    
        else:
            analysis["incident_confidence"] = "LOW"
    
    
    elif analysis["failure_type"] == "ECR_CONNECTIVITY":
    
        analysis["incident_type"] = "ECR_CONNECTIVITY_FAILURE"
        analysis["incident_confidence"] = "HIGH"
    
    
    elif analysis["failure_type"] == "ECR_AUTHORIZATION":
    
        analysis["incident_type"] = "ECR_AUTHORIZATION_FAILURE"
        analysis["incident_confidence"] = "HIGH"
    
    
    elif analysis["failure_type"] == "SECRETS_MANAGER":
    
        analysis["incident_type"] = "SECRETS_MANAGER_FAILURE"
        analysis["incident_confidence"] = "HIGH"
    
    
    elif analysis["failure_type"] == "NETWORK_CONNECTIVITY":
    
        analysis["incident_type"] = "NETWORK_CONNECTIVITY_FAILURE"
        analysis["incident_confidence"] = "HIGH"
    
    
    elif (
        analysis["failure_stage"] == "container"
        and analysis["container_exit_code"] not in [None, 0]
    ):
    
        analysis["incident_type"] = "APPLICATION_FAILURE"
        analysis["incident_confidence"] = "HIGH"
    
    
    else:
    
        analysis["incident_type"] = "UNKNOWN"
        analysis["incident_confidence"] = "LOW"

    if (
        analysis["failure_type"] == "USER_INITIATED_STOP"
        and analysis["container_exit_code"] not in [None, 0]
    ):
        analysis["evidence_conflict"] = True
        analysis["evidence_conflict_reason"] = (
            "Task was classified as user-initiated, "
            "but the container exited with a non-zero exit code."
        )

    # Conflicting evidence always reduces confidence
    
    if analysis["evidence_conflict"]:
        analysis["incident_confidence"] = "LOW"
        
    return analysis


# define investigation decision function

def determine_investigation_status(state):

    analysis = state["evidence_analysis"]

    if not analysis:
        return {
            "complete": False,
            "reason": "Evidence analysis is not available"
        }

    if analysis.get("evidence_conflict"):
        return {
            "complete": False,
            "reason": "Evidence conflict detected"
        }

    confidence = analysis.get("incident_confidence")

    if confidence == "HIGH":
        return {
            "complete": True,
            "reason": "Evidence is consistent and confidence is high"
        }

    if confidence == "MEDIUM":
        return {
            "complete": True,
            "reason": "Evidence is sufficient for diagnosis but some attribution is unavailable"
        }

    return {
        "complete": False,
        "reason": "Evidence confidence is low"
    }

# define function investigation function to find out missing evidence

def determine_missing_evidence(state):

    analysis = state["evidence_analysis"]

    if not analysis:
        return {
            "missing_evidence": "evidence_analysis",
            "reason": "Evidence analysis is not available"
        }

    if analysis.get("evidence_conflict"):
        return {
            "missing_evidence": "conflicting_evidence",
            "reason": analysis.get(
                "evidence_conflict_reason"
            )
        }

    if (
        analysis.get("user_initiated_task")
        and not analysis.get("cloudtrail_actor_found")
    ):
        return {
            "missing_evidence": "cloudtrail_attribution",
            "reason": (
                "The task is classified as user-initiated, "
                "but the CloudTrail actor was not found."
            )
        }

    if (
        analysis.get("failure_stage") == "container"
        and not analysis.get("cloudwatch_available")
    ):
        return {
            "missing_evidence": "cloudwatch_logs",
            "reason": (
                "The task reached the container stage, "
                "but CloudWatch logs are not available."
            )
        }

    return {
        "missing_evidence": None,
        "reason": "No obvious missing evidence identified"
    }

# define function which is version 2 of get_ecs_task_logs
def get_ecs_task_logs(cluster_name, task_arn, limit=20):

    if not cluster_name:
        return {"error": "Cluster name is required"}

    if not task_arn:
        return {"error": "Task ARN is required"}

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

# ============================================================
# AGENT STATE
# ============================================================

agent_state = {
    "cluster": None,
    "services": None,
    "selected_service": None,
    "investigated_task_arn": None,
    "service_status": None,
    "tasks": None,
    "stopped_tasks": None,
    "service_events": None,
    "cloudwatch_logs": None,
    "diagnosis": None,
    "stopped_task_summary": None,
    "recheck_count": 0,
    "max_rechecks": 5,
    "task_details": None,
    "failure_classification": None,
    "cloudtrail_event": None,
    "evidence_analysis": None,
    "next_action": None,
    "investigation_complete": False,
    "investigation_reason": None,
    "missing_evidence": None
}


# ============================================================
# PLANNER
# ============================================================

def determine_next_action(state):

    # --------------------------------------------------------
    # No cluster known
    # --------------------------------------------------------

    if not state["cluster"]:
        return "discover_cluster"


    # --------------------------------------------------------
    # Cluster known, services not discovered
    # --------------------------------------------------------

    if state["services"] is None:
        return "discover_services"


    # --------------------------------------------------------
    # Services discovered but none exist
    # --------------------------------------------------------

    if len(state["services"]) == 0:
        return "no_services"


    # --------------------------------------------------------
    # Service not selected
    # --------------------------------------------------------

    if state["selected_service"] is None:

        # Exactly one service
        if len(state["services"]) == 1:
            return "select_service"

        # Multiple services
        return "ask_user"


    # --------------------------------------------------------
    # Service selected but status not checked
    # --------------------------------------------------------

    if state["service_status"] is None:
        return "check_service_status"


    # --------------------------------------------------------
    # Service status known but tasks not checked
    # --------------------------------------------------------

    if state["tasks"] is None:
        return "get_ecs_tasks"

    # --------------------------------------------------------
    # Service status known but no tasks found
    # --------------------------------------------------------
    if state["stopped_tasks"] is None:
        desired_count = state["service_status"]["desired_count"]
        running_count = state["service_status"]["running_count"]

        # Service intentionally configured to run zero tasks
        if desired_count == 0:
            return "done"
        
        # Service has achieved desired capacity
        if running_count == desired_count:
            return "done"

        # A task is still starting
        if has_starting_task(state):

            # We still have retries available
            if state["recheck_count"] < state["max_rechecks"]:
                return "recheck_task"

            # Retries exhausted
            return "get_stopped_ecs_tasks"

         # Desired tasks are missing and no task is starting
        if running_count < desired_count:
            return "get_stopped_ecs_tasks"
        
        return "done"

    # --------------------------------------------------------
    # # SELECT ONE STOPPED TASK FOR DETAILED INVESTIGATION
    # --------------------------------------------------------

    if state["investigated_task_arn"] is None:
    
        stopped_tasks = state["stopped_tasks"].get("tasks", [])
    
        if stopped_tasks:
            state["investigated_task_arn"] = stopped_tasks[0]["task_arn"]
    
            print(
                f"\nInvestigating task: "
                f"{state['investigated_task_arn']}"
            )
    
            return "get_ecs_task_details"



    # --------------------------------------------------------
    # Stopped tasks found but detailed task information
    # not checked
    # --------------------------------------------------------
    
    if state["task_details"] is None:
    
        stopped_tasks = state["stopped_tasks"].get("tasks", [])
    
        if stopped_tasks:
            return "get_ecs_task_details"

    # --------------------------------------------------------
    #  Failure classification
    #---------------------------------------------------------

    if state["failure_classification"] is None:
        return "classify_ecs_task_failure"
    
    
    # --------------------------------------------------------
    #  Task found but Service Events inspects
    #---------------------------------------------------------

    if state["service_events"] is None: 
        return "get_ecs_service_events"

    # --------------------------------------------------------
    #  cloudtrail_event on stopped Task 
    #---------------------------------------------------------

    if state["cloudtrail_event"] is None:
        stopped_tasks = state["stopped_tasks"].get("tasks", [])

        if stopped_tasks:
            return "get_ecs_stop_task_cloudtrail_event"


    # --------------------------------------------------------
    #  cloudwatch log on stopped Task 
    #---------------------------------------------------------

    if state["cloudwatch_logs"] is None:
        stopped_tasks = state["stopped_tasks"].get("tasks", [])

        if stopped_tasks:
            return "get_ecs_task_logs"
    # --------------------------------------------------------
    #  analyze_ecs_evidence and cloudtrail_event on stopped Task 
    #---------------------------------------------------------

    if state["evidence_analysis"] is None:
        return "analyze_ecs_evidence"
    
    
    if not state["investigation_complete"]:
    
        investigation_status = determine_investigation_status(state)
    
        state["investigation_complete"] = investigation_status["complete"]
        state["investigation_reason"] = investigation_status["reason"]
    
        print(
            "\nInvestigation status:"
        )
    
        print(
            json.dumps(
                investigation_status,
                indent=2
            )
        )
    
        if not investigation_status["complete"]:
    
            if state["missing_evidence"] is None:
                return "determine_missing_evidence"
    
            return "investigate_more"
    
    
    if state["diagnosis"] is None:
        return "diagnose_failure"

    # --------------------------------------------------------
    # Everything completed
    # --------------------------------------------------------

    return "done"


# ============================================================
# DISPLAY STATE
# ============================================================

def print_state(state):

    print("\n================ AGENT STATE ================")

    print(
        json.dumps(
            state,
            indent=2
        )
    )

    print("==============================================")


# ============================================================
# START
# ============================================================

print("==============================================")
print("       ECS PLANNER-DRIVEN AGENT")
print("==============================================")


#user_cluster = input(
#    "\nEnter ECS cluster name: "
#).strip()


# Put user information into state

agent_state["cluster"] = "myecs-cluster" #user_cluster


# ============================================================
# PLANNER LOOP
# ============================================================

while True:

    # --------------------------------------------------------
    # Ask planner what to do next
    # --------------------------------------------------------

    agent_state["next_action"] = determine_next_action(
        agent_state
    )

    print_state(agent_state)

    print("\nPlanner decision:", agent_state["next_action"])


    # ========================================================
    # ACTION: DISCOVER CLUSTERS
    # ========================================================

    if agent_state["next_action"] == "discover_cluster":

        print("\nExecuting: list_ecs_clusters()")

        result = list_ecs_clusters()

        print("\nAWS result:")

        print(
            json.dumps(
                result,
                indent=2
            )
        )

        # Check whether requested cluster exists

        if agent_state["cluster"] in result["clusters"]:

            print(
                f"\nCluster '{agent_state['cluster']}' exists."
            )

        else:

            print(
                f"\nCluster '{agent_state['cluster']}' "
                f"was not found."
            )

            break


    # ========================================================
    # ACTION: DISCOVER SERVICES
    # ========================================================

    elif agent_state["next_action"] == "discover_services":

        cluster = agent_state["cluster"]

        print(
            f"\nExecuting: "
            f"list_ecs_services('{cluster}')"
        )

        result = list_ecs_services(cluster)

        print("\nAWS result:")

        print(
            json.dumps(
                result,
                indent=2
            )
        )

        # Update state

        agent_state["services"] = result["services"]


    # ========================================================
    # ACTION: NO SERVICES
    # ========================================================

    elif agent_state["next_action"] == "no_services":

        print(
            f"\nNo ECS services found in "
            f"cluster '{agent_state['cluster']}'."
        )

        break


    # ========================================================
    # ACTION: SELECT SERVICE
    # ========================================================

    elif agent_state["next_action"] == "select_service":

        agent_state["selected_service"] = (
            agent_state["services"][0]
        )

        print(
            "\nOnly one service found."
        )

        print(
            "Selected service:",
            agent_state["selected_service"]
        )


    # ========================================================
    # ACTION: ASK USER
    # ========================================================

    elif agent_state["next_action"] == "ask_user":

        print(
            "\nMultiple services found:"
        )

        for index, service in enumerate(
            agent_state["services"],
            start=1
        ):

            print(
                f"{index}. {service}"
            )


        while True:

            choice = input(
                "\nSelect service number: "
            ).strip()

            try:

                choice = int(choice)

                if 1 <= choice <= len(
                    agent_state["services"]
                ):
                    break

            except ValueError:
                pass

            print(
                "Invalid selection."
            )


        agent_state["selected_service"] = (
            agent_state["services"][choice - 1]
        )

        print(
            "\nSelected service:",
            agent_state["selected_service"]
        )


    # ========================================================
    # ACTION: SERVICE STATUS
    # ========================================================

    elif agent_state["next_action"] == "check_service_status":

        cluster = agent_state["cluster"]
        service = agent_state["selected_service"]

        print(
            f"\nExecuting: "
            f"get_ecs_service_status("
            f"'{cluster}', '{service}')"
        )

        result = get_ecs_service_status(
            cluster,
            service
        )

        print("\nAWS result:")

        print(
            json.dumps(
                result,
                indent=2
            )
        )

        # Update state

        agent_state["service_status"] = result


    # ========================================================
    # ACTION: ECS TASKS
    # ========================================================

    elif agent_state["next_action"] == "get_ecs_tasks":

        cluster = agent_state["cluster"]
        service = agent_state["selected_service"]

        print(
            f"\nExecuting: "
            f"get_ecs_tasks("
            f"'{cluster}', '{service}')"
        )

        result = get_ecs_tasks(
            cluster,
            service
        )

        print("\nAWS result: for get ecs tasks")

        print(
            json.dumps(
                result,
                indent=2
            )
        )

        # Update state

        agent_state["tasks"] = result

    # ========================================================
    # ACTION: ECS TASKS Rechecks
    # ========================================================

    elif agent_state["next_action"] == "recheck_task":

        cluster = agent_state["cluster"]
        service = agent_state["selected_service"]

        agent_state["recheck_count"] += 1
        print(
            f"\nWaiting before recheck "
            f"{agent_state['recheck_count']}/"
            f"{agent_state['max_rechecks']}..."
        )
        
        # wait for task to become running state
        time.sleep(10)

        # -----------------------------------------
        # Refresh service status
        # -----------------------------------------

        service_status = get_ecs_service_status(
            cluster,
            service
        )
        print("\nAWS result: for service status")
        print(json.dumps(service_status, indent=2))

        agent_state["service_status"] = service_status

        # -----------------------------
        # Refresh current tasks
        # -----------------------------
        result = get_ecs_tasks(
            cluster,
            service
        )

        print("\nAWS result: for get ecs tasks")

        print(
            json.dumps(
                result,
                indent=2
            )
        )

        # Update state

        agent_state["tasks"] = result
        # -----------------------------
        # Check if replacement task
        # disappeared
        # -----------------------------

        current_tasks = result.get("tasks", [])

        if not current_tasks:
            print("\nNo current task found. " "Checking stopped tasks...")
            stopped_result = get_stopped_ecs_tasks(
                cluster,
                service
            )
            print("\nAWS result: for stopped tasks")
            print(json.dumps(result, indent=2))
            agent_state["stopped_tasks"] = stopped_result

    # ========================================================
    # ACTION: ECS TASKS
    # ========================================================

    elif agent_state["next_action"] == "get_stopped_ecs_tasks":

        cluster = agent_state["cluster"]
        service = agent_state["selected_service"]

        print(
            f"\nExecuting: "
            f"get_stopped_ecs_tasks("
            f"'{cluster}', '{service}')"
        )

        result = get_stopped_ecs_tasks(
            cluster,
            service
        )

        # Update state

        agent_state["stopped_tasks"] = result

    # ========================================================
    # ACTION: ECS TASKS details
    # ========================================================
    elif agent_state["next_action"] == "get_ecs_task_details":
    
        cluster = agent_state["cluster"]
        task_arn = agent_state["investigated_task_arn"]
    
        print(
            f"\nExecuting: get_ecs_task_details("
            f"'{cluster}', '{task_arn}')"
        )
    
        result = get_ecs_task_details(
            cluster,
            task_arn
        )
    
        print("\nAWS result: for task details")
        print(json.dumps(result, indent=2))
    
        agent_state["task_details"] = result

    # ========================================================
    # ACTION: TASKS failure classification
    # ========================================================

    elif agent_state["next_action"] == "classify_ecs_task_failure":
    
        task_details = agent_state["task_details"]
    
        print(
            "\nExecuting: classify_ecs_task_failure()"
        )
    
        result = classify_ecs_task_failure(
            task_details
        )
    
        print("\nFailure classification:")
        print(json.dumps(result, indent=2))
    
        agent_state["failure_classification"] = result
    # ========================================================
    # ACTION: Service Events
    # ========================================================

    elif agent_state["next_action"] == "get_ecs_service_events":

        # Getting function arguments
        cluster = agent_state["cluster"]
        service = agent_state["selected_service"]

        print("events service executed")

        result = get_ecs_service_events(cluster, service)

        # Update state
        agent_state["service_events"] = result

    # ========================================================
    # ACTION: get_ecs_stop_task on cloudtrail_event
    # ========================================================
    elif agent_state["next_action"] == "get_ecs_stop_task_cloudtrail_event":

        cluster = agent_state["cluster"]
        task_arn = agent_state["investigated_task_arn"]

        print(
        f"\nExecuting: get_ecs_stop_task_cloudtrail_event("
        f"'{cluster}', '{task_arn}')"
        )

        result = get_ecs_stop_task_cloudtrail_event(cluster, task_arn)

        print("\nAWS result: for CloudTrail")
        print(json.dumps(result, indent=2))

        #update agent state
        agent_state["cloudtrail_event"] = result

    # ========================================================
    # ACTION: get cloudwatch log from stopped tasks
    # ========================================================

    elif agent_state["next_action"] == "get_ecs_task_logs":
        cluster = agent_state["cluster"]
    
        task_arn = agent_state["investigated_task_arn"]

        print(
        f"\nExecuting: get_ecs_task_logs("
        f"'{cluster}', '{task_arn}')"
        )
    
        result = get_ecs_task_logs(
           cluster,
           task_arn,
           limit=20
        )
    
        print("\nAWS result: for CloudWatch logs")
        print(json.dumps(result, indent=2))   
        agent_state["cloudwatch_logs"] = result

    # ========================================================
    # ACTION: get_ecs_stop_task on cloudtrail_event
    # ========================================================

    elif agent_state["next_action"] == "analyze_ecs_evidence":

        print("\nExecuting: analyze_ecs_evidence")

        result = analyze_ecs_evidence(agent_state)
        
        print("\nDeterministic analysis:")
        
        print(json.dumps(result, indent=2))

        agent_state["evidence_analysis"] = result

    # ========================================================
    # ACTION: find missing evidence
    # ========================================================

    elif agent_state["next_action"] == "determine_missing_evidence":
    
        print("\nExecuting: determine_missing_evidence()")
    
        result = determine_missing_evidence(agent_state)
    
        print("\nMissing evidence:")
    
        print( json.dumps(result, indent=2) )
    
        agent_state["missing_evidence"] = result
    # ========================================================
    # ACTION: Diagnose failure
    # ========================================================

    elif agent_state["next_action"] == "diagnose_failure":

        deterministic_diagnosis_result = diagnose_failure(agent_state)
        pattern_analysis = analyze_stopped_tasks(agent_state)
        evidence = {
          "cluster": agent_state["cluster"],
          "service": agent_state["services"],
          "service_status": agent_state["service_status"],
          "running_tasks": agent_state["tasks"]["tasks"],
          "stopped_task_summary": deterministic_diagnosis_result,
          "service_events": agent_state["service_events"],
          "pattern_analysis": pattern_analysis
        }

        # Sending evidence to LLM

        llm_result = generate_llm_diagnosis(agent_state)

         # update state
        agent_state["stopped_task_summary"] = deterministic_diagnosis_result
        agent_state["diagnosis"] = llm_result
        if agent_state["service_status"]["desired_count"] == agent_state["service_status"]["running_count"]:
            agent_state["next_action"] = "done"


    # ========================================================
    # ACTION: DONE
    # ========================================================

    elif agent_state["next_action"] == "done":

        print("\n==============================================")
        print("              WORKFLOW COMPLETE")
        print("==============================================")

        print(
            json.dumps(
                agent_state,
                indent=2
            )
        )

        break


    # ========================================================
    # UNKNOWN ACTION
    # ========================================================

    else:

        print(
            "\nUnknown planner action:",
            agent_state["next_action"]
        )

        break

#test_conflicting_evidence()