from openai import OpenAI
import json
client = OpenAI()

name = input("Enter your servers name: ")
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
    input=f"What is the current status of servers {name} ?",
    tools=tools
    )

#print(response.output)
# Step 2: Process the LLM output
for item in response.output:
  if item.type == "function_call":
    print("LLM wants to call a tool")
    print("Tools name is: ", item.name)
    print("Tools arguments are: ", item.arguments)
    print("Tools call_id is: ", item.call_id)
    print("Calling the tool...")

    # Step 4: Execute the requested Python function
    if item.name == "get_server_status":

      # 3. Convert JSON arguments into Python dictionary
      arguments = json.loads(item.arguments)
      server_name = arguments["server_name"]

      print("Server name extracted:", server_name)

      result = get_server_status(server_name)
      print("server status is ", result)

      # Step 5: Send the tool result back to the LLM
      response = client.responses.create(
        model="gpt-5.4-mini",
        previous_response_id=response.id, 
        input=[
          {
            "type": "function_call_output",  # Indicates that this is the output of a function call, "This piece of input is the result of a tool/function call."
            "call_id": item.call_id, # This result belongs to that specific tool call." The call_id from the previous function call
            "output": json.dumps(result) # The output of the function call, which will be sent back to the LLM
          }
        ],
        tools=tools
      )
    # Step 5: Print the LLM's final answer
    print("Final Answer from LLM is :", response.output_text)

