def determine_next_action(state):

    if not state["cluster"]:
        return "discover_cluster"

    if state["services"] is None:
        return "discover_services"

    if len(state["services"]) == 0:
        return "no_services"

    if state["selected_service"] is None:

        if len(state["services"]) == 1:
            return "select_service"

        return "ask_user"

    if state["service_status"] is None:
        return "check_service_status"

    if state["tasks"] is None:
        return "get_ecs_tasks"

    return "diagnose"


test_states = [

    {
        "name": "Nothing known",
        "state": {
            "cluster": None,
            "services": None,
            "selected_service": None,
            "service_status": None,
            "tasks": None
        }
    },

    {
        "name": "Cluster known",
        "state": {
            "cluster": "java-app",
            "services": None,
            "selected_service": None,
            "service_status": None,
            "tasks": None
        }
    },

    {
        "name": "No services",
        "state": {
            "cluster": "java-app",
            "services": [],
            "selected_service": None,
            "service_status": None,
            "tasks": None
        }
    },

    {
        "name": "One service",
        "state": {
            "cluster": "myecs-cluster",
            "services": ["hotel-mysql-service"],
            "selected_service": None,
            "service_status": None,
            "tasks": None
        }
    },

    {
        "name": "Multiple services",
        "state": {
            "cluster": "myecs-cluster",
            "services": [
                "hotel-mysql-service",
                "vru-hotel-app-task-service-"
            ],
            "selected_service": None,
            "service_status": None,
            "tasks": None
        }
    },

    {
        "name": "Service selected",
        "state": {
            "cluster": "myecs-cluster",
            "services": ["hotel-mysql-service"],
            "selected_service": "hotel-mysql-service",
            "service_status": None,
            "tasks": None
        }
    },

    {
        "name": "Service status known",
        "state": {
            "cluster": "myecs-cluster",
            "services": ["hotel-mysql-service"],
            "selected_service": "hotel-mysql-service",
            "service_status": {
                "desired_count": 1,
                "running_count": 1
            },
            "tasks": None
        }
    },

    {
        "name": "Everything known",
        "state": {
            "cluster": "myecs-cluster",
            "services": ["hotel-mysql-service"],
            "selected_service": "hotel-mysql-service",
            "service_status": {
                "desired_count": 1,
                "running_count": 1
            },
            "tasks": [
                {
                    "last_status": "RUNNING"
                }
            ]
        }
    }
]


for test in test_states:

    next_action = determine_next_action(test["state"])

    print(
        f"{test['name']:25} -> {next_action}"
    )