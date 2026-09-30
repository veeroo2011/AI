# This agent will call call all tools at once and send result to LLM

import json
from openai import OpenAI

client = OpenAI()
name = input("Enter your servers name: ")
if name.lower() == "all":
    name = "web-01, web-02, web-03"

def get_server_status(server_name):
    servers = {
        "web-01": {
            "status": "healthy",
            "cpu": 42
        },
        "web-02": {
            "status": "unhealthy",
            "cpu": 95
        },
        "web-03": {
            "status": "healthy",
            "cpu": 15
        }
    }

    return servers.get(
        server_name,
        {
            "status": "unknown"
        }
    )


tools = [
    {
        "type": "function",
        "name": "get_server_status",
        "description": "Get the current status of a web server.",
        "parameters": {
            "type": "object",
            "properties": {
                "server_name": {
                    "type": "string",
                    "description": "The name of the server to check."
                }
            },
            "required": ["server_name"],
            "additionalProperties": False
        },
        "strict": True
    }
]


# Step 1: Ask the LLM 
response = client.responses.create(
    model="gpt-5.4-mini",
    input=f"What is the current status of {name}?",
    tools=tools
)


# Keep the original response ID
previous_response_id = response.id

tool_outputs = []


# Step 2: Process all tool calls
for item in response.output:

    if item.type == "function_call":

        print("LLM wants to call a tool")
        print("Tool name:", item.name)
        print("Tool arguments:", item.arguments)
        print("Tool call_id:", item.call_id)

        if item.name == "get_server_status":

            print("Calling the tool...")

            arguments = json.loads(item.arguments)

            server_name = arguments["server_name"]

            print("Server name extracted:", server_name)

            result = get_server_status(server_name)

            print("Server status:", result)

            # Collect the tool result
            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps(result)
                }
            )


# Step 3: Send ALL tool results back to the LLM
# API will be called only once and send all result 
# at once instead of calling the LLM API multiple times for each tool call.

# Remebers this rule:
# Inside the loop: execute and collect individual tool results.
# Outside the loop: send the collected results back to the LLM.
# Then repeat the overall cycle if the LLM requests more tools.
if tool_outputs:

    response = client.responses.create(
        model="gpt-5.4-mini",
        previous_response_id=previous_response_id,
        input=tool_outputs
    )


# Step 4: Final answer
print("\nFinal Answer from LLM:")
print(response.output_text)