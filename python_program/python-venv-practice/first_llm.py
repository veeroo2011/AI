from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5.4-mini",
    instructions="""
    You are an AWS DevOps troubleshooting assistant.

    Rules:
    - Do not invent infrastructure state.
    - Use only the evidence provided.
    - Clearly distinguish facts from hypotheses.
    - If evidence is insufficient, identify what is missing.
    - Recommend investigation before remediation.
    """,
    input="""
You are troubleshooting an ECS service.

Service information:
- Desired tasks: 3
- Running tasks: 3
- Healthy tasks: 0
- Unhealthy tasks: 3

Target group:
- Target port: 8080
- Health check path: /health
- Health check result: timeout

Application:
- Listening on port 8080
- Application binds to 0.0.0.0

Why is the service returning HTTP 503?
"""
)

print(response.output_text)