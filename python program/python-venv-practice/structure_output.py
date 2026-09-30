# text is used here to get output in a structured format, instead of just plain text.
from openai import OpenAI
import json
client = OpenAI()

response = client.responses.create(
    model="gpt-5.4-mini",

    input="""
    Analyze this ECS problem:

    Desired tasks: 3
    Running tasks: 3
    Healthy tasks: 0
    Unhealthy tasks: 3
    Health check result: timeout

    Return the issue, severity, likely cause,
    and next investigation step.
    """,

    text={
        "format": {
            "type": "json_schema",
            "name": "devops_diagnosis",
            "schema": {
                "type": "object",
                "properties": {
                    "issue": {
                        "type": "string"
                    },
                    "severity": {
                        "type": "string"
                    },
                    "likely_cause": {
                        "type": "string"
                    },
                    "next_check": {
                        "type": "string"
                    }
                },
                "required": [
                    "issue",
                    "severity",
                    "likely_cause",
                    "next_check"
                ],
                "additionalProperties": False
            },
            "strict": True
        }
    }
)
result = json.loads(response.output_text)
print("Issue:", result["issue"])
print("Severity:", result["severity"])
print("Likely Cause:", result["likely_cause"])
print("Next Investigation Step:", result["next_check"])