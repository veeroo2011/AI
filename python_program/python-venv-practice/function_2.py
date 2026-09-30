from openai import OpenAI
import json
client = OpenAI()

def get_server_status(server_name):
  server = {
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
  return server.get(
    server_name,
    {
       "status": "unknown"
    }
  )

tools = [
    {
        "type": "function",
        "name": "get_server_status",
        "description": "Get the current status of the web server.",
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
response = client.responses.create(
    model="gpt-5.4-mini",
    input="What is the current status of web-02?",
    tools=tools
    )

print(response.output)
# Step 2: Process the LLM output
for item in response.output:
  if item.type == "function_call":
    print("LLM wants to call a tool")
    print("Tools name is: ", item.name)
    print("Tools arguments are: ", item.arguments)
    print("Tools call_id is: ", item.call_id)
    print("Calling the tool...")