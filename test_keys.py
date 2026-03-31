import os
import sys

print("=== API KEY VERIFICATION ===")

# Test OpenAI
print("\\n1. Testing OpenAI...")
os.environ["OPENAI_API_KEY"] = "sk-proj-1sD6Nt0kgEGmMl63Jwj0KxZJl2JTz5P7RqKmaxfSP0RN2e8GCOwVBYvvYb0NYvAhAwNnm_NrHT3BlbkFJGTSQfsRMbhFQPoLPk9K3B7NksWYeRsMWWswAOCqZi5IhLzpL9xXHRwRbYShNd8ECgjqOVCvZMA"

try:
    import openai
    client = openai.OpenAI()
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Reply exactly with 'OPENAI IS WORKING'"}],
        max_tokens=20
    )
    print("STATUS: SUCCESS")
    print("RESPONSE: " + res.choices[0].message.content.strip())
except Exception as e:
    print("STATUS: FAILED")
    print("REASON:", str(e))

# Test Groq
print("\\n2. Testing Groq...")
os.environ["GROQ_API_KEY"] = "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"

try:
    import groq
    client = groq.Groq()
    res = client.chat.completions.create(
        model="llama3-70b-8192",  # Using known active model
        messages=[{"role": "user", "content": "Reply exactly with 'GROQ IS WORKING'"}],
        max_tokens=20
    )
    print("STATUS: SUCCESS")
    print("RESPONSE: " + res.choices[0].message.content.strip())
except Exception as e:
    print("STATUS: FAILED")
    print("REASON:", str(e))
