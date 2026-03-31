<div align="center">
  <h1>🚨 AI Operations War Room 🚨<br/>(A Frontier SRE LLM Agent Environment)</h1>
  <p><i>A hyper-realistic, OpenEnv-compliant reinforcement learning and evaluation suite simulating cascading production outages for LLM Agents.</i></p>
</div>

---

## 💥 The Vision: AI as On-Call Engineers
This environment simulates real-world production outages where AI agents must act as **On-Call SREs under extreme pressure**. 
It isn't just about parsing JSON; it's about **trajectory reasoning**. The AI must observe symptoms, deduce hidden root causes via multi-step diagnostics, and deploy fixes before cascading system failures bring down the API.

> *Example Narrative (Hard Scenario)*: A failed deployment causes API pods to crash-loop. If the agent ignores it, queries pile up, caching drops, and the backing DB eventually locks up from connection saturation. A naive agent might just try to "restart the DB", lowering latency temporarily but missing the root cause, eventually leading to a full critical outage!

---

## 🎮 The Incident Command Center UI
The environment features a world-class Streamlit dashboard mimicking a live DevOps War Room suitable for **instant visual evaluation** by engineering judges.

- **🚨 Incident Banner**: Dynamically shifts severity (CRITICAL, WARNING, STABLE) animating when limits are breached.
- **📊 Telemetry Panels**: Real-time Plotly dials visualizing CPU, Memory, and Latency cascades.
- **🧾 Diagnostic Stream**: A syntax-colored terminal pumping out realistic system warnings and kernel OOM logs.
- **📖 Timeline Storytelling**: Visually tracks the human-readable causality: `Action → Degradation ↑ → Rollback → Latency ↓`
- **🎮 Replay & Demo Modes**: An auto-play mode allowing judges to watch the SRE LLM perfectly diagnose the Hard scenario in a 60-second visual movie format.

---

## 🧠 Technical Depth & Grading Philosophy

### 1. OpenEnv Compliance
Built fundamentally around the strict OpenEnv `reset()`, `step()`, `state()` interface with Pydantic Models.

### 2. Time-Based Degradation & Hidden Roots
- **Hidden Root Causes**: Symptoms decoupled from origins. (e.g. CPU spikes heavily due to an invisible DB lock).
- **Delayed Effects**: Flushing a cache clears memory but briefly harms API latency.

### 3. Trajectory-Aware Grader
Instead of simplistic pass/fail, our Grader scores the AI out of `1.0`:
*   🏆 **40% Correctness**: Resolving the exact active issue.
*   ⚡ **30% Efficiency**: Solving it before system resources severely degrade.
*   🤔 **30% Reasoning Path**: Did the AI wildly spam actions? Did it `run_diagnostics` BEFORE it `rolled_back_deploy`?

---

## Baseline Agent & LLM Provider Configuration
This repository provides a hardened baseline `ReAct` (Observe -> Think -> Act) agent. You can configure it to use OpenAI (default) or Groq for faster/cheaper inference.

**Using OpenAI (Default):**
```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your_key_here
```

**Using Groq:**
```bash
export LLM_PROVIDER=groq
export GROQ_API_KEY=your_key_here
```

API keys are loaded securely via environment variables and are never hardcoded.

To run the baseline manually:
```bash
pip install -r requirements.txt
python scripts/run_baseline.py
```
We've optimized this project to operate effortlessly on Hugging Face Spaces or locally.

### Option A: Direct Hugging Face / Single Command (Recommended)
This launches a lightweight Python wrapper booting both the API and Streamlit.
```bash
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
python app.py
```
*(The UI will open on port 7860.)*

### Option B: Docker Setup
Perfect for isolated headless evaluation or CI/CD integration.
```bash
docker build -t aiops-env .
docker run -p 8000:8000 aiops-env
```

---
*Built with speed, modularity, and realism for frontier AI Evaluation.*
