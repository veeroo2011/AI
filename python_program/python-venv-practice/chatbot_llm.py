from openai import OpenAI
client = OpenAI() # create object client which will be used for communicating with LLM
conversation = []

while True:
  user_input = input("You: ")
  if user_input.lower() == "exit": # To Terminate program needs to type exit
    break
  conversation.append({
    "role": "user",
    "content": user_input
  })
  response = client.responses.create(
    model="gpt-5.4-mini",
    input=conversation
  )
  print("assistant:", response.output_text)
  conversation.append({
    "role": "assistant",
    "content": response.output_text
  })

#conversation will be look like
#  │
#  ├── user
#  │   My ECS service is called payments.
#  │
#  ├── assistant
#  │   Got it...
#  │
#  └── user
#      It is returning HTTP 503.