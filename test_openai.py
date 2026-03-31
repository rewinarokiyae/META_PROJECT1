import os
import openai
import sys

# Attempt validation using OpenAI python library
os.environ["OPENAI_API_KEY"] = "sk-proj-1sD6Nt0kgEGmMl63Jwj0KxZJl2JTz5P7RqKmaxfSP0RN2e8GCOwVBYvvYb0NYvAhAwNnm_NrHT3BlbkFJGTSQfsRMbhFQPoLPk9K3B7NksWYeRsMWWswAOCqZi5IhLzpL9xXHRwRbYShNd8ECgjqOVCvZMA"

print("Pinging OpenAI API...")
try:
    client = openai.OpenAI()
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "say explicitly 'API is working' and nothing else"}],
        max_tokens=20
    )
    print("STATUS: " + res.choices[0].message.content.strip())
except Exception as e:
    print("STATUS: FAILED")
    print("REASON:", str(e))
    sys.exit(1)
