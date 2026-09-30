from openai import OpenAI
import os
client = OpenAI()
os.environ["OPENAI_API_KEY"] =""
response = client.embeddings.create(
  input="Your text string goes here",
  model="text-embedding-3-small"
)
print(response.data[0].embedding)