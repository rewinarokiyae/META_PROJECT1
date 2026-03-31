import subprocess
import time
import os
import requests
import sys

print("Booting local AIOps backend for verification...")
api_process = subprocess.Popen([sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"])

for i in range(15):
    try:
        res = requests.get("http://localhost:8000/tasks")
        if res.status_code == 200:
            break
    except Exception:
        pass
    time.sleep(1)

os.environ["OPENAI_API_KEY"] = "sk-proj-1sD6Nt0kgEGmMl63Jwj0KxZJl2JTz5P7RqKmaxfSP0RN2e8GCOwVBYvvYb0NYvAhAwNnm_NrHT3BlbkFJGTSQfsRMbhFQPoLPk9K3B7NksWYeRsMWWswAOCqZi5IhLzpL9xXHRwRbYShNd8ECgjqOVCvZMA"
os.environ["GROQ_API_KEY"] = "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"

print("\\n" + "="*50)
print("TESTING OPENAI PROVIDER")
print("="*50)
os.environ["LLM_PROVIDER"] = "openai"
res_openai = subprocess.run([sys.executable, "scripts/run_baseline.py"], capture_output=True, text=True)
print(res_openai.stdout)
if res_openai.stderr:
    print("ERRORS:", res_openai.stderr)

print("\\n" + "="*50)
print("TESTING GROQ PROVIDER")
print("="*50)
os.environ["LLM_PROVIDER"] = "groq"
res_groq = subprocess.run([sys.executable, "scripts/run_baseline.py"], capture_output=True, text=True)
print(res_groq.stdout)
if res_groq.stderr:
    print("ERRORS:", res_groq.stderr)

print("Shutting down backend...")
api_process.terminate()
