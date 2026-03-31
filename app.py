import subprocess
import sys
import time
import os
import requests

def main():
    print("Starting AIOps War Room (HF Space Compatible Wrapper)...")
    
    # 1. Start the FastAPI backend on port 8000
    api_process = subprocess.Popen([sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"])
    
    # Wait for API to be ready
    max_retries = 15
    ready = False
    for i in range(max_retries):
        try:
            res = requests.get("http://localhost:8000/tasks")
            if res.status_code == 200:
                ready = True
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
        
    if not ready:
        print("Backend failed to start in time.")
        api_process.terminate()
        sys.exit(1)
        
    print("Backend API is fully online. Starting Streamlit Command Center...")
    
    # HF Spaces sets PORT env variable for Streamlit, default to 7860
    ui_port = os.getenv("PORT", "7860")
    
    # 2. Start Streamlit UI
    ui_process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "ui/app.py", "--server.port", ui_port, "--server.address", "0.0.0.0"])

    try:
        api_process.wait()
        ui_process.wait()
    except KeyboardInterrupt:
        print("Shutting down AIOps War Room...")
        ui_process.terminate()
        api_process.terminate()
        
if __name__ == "__main__":
    main()
