from openai import OpenAI

client = OpenAI()

# here conversation is provided at once to LLM. its not interactive with LLM like chatbot
conversation = [
    {
        "role": "user",
        "content": "My ECS service is called payments."
    },
    {
        "role": "assistant",
        "content": "Okay, I'll remember that for this conversation."
    },
    {
        "role": "user",
        "content": "It is returning HTTP 503."
    },
    {
        "role": "assistant",
        "content": "Let's investigate the likely causes."
    },
    {
        "role": "user",
        "content": "What should I check first?"
    }
]

response = client.responses.create(
    model="gpt-5.4-mini",
    input=conversation
)

print(response.output_text)