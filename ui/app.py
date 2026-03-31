import streamlit as st
import requests
import time
import pandas as pd
import plotly.graph_objects as go
import os
import sys

# Ensure backend scripts can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import importlib
    import scripts.run_baseline
    importlib.reload(scripts.run_baseline)
    from scripts.run_baseline import get_action_from_llm
except ImportError:
    pass
    pass

from dotenv import load_dotenv

load_dotenv()
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Incident Command Center", layout="wide", page_icon="🚨")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @keyframes blink-critical {
        0% { opacity: 1.0; }
        50% { opacity: 0.5; box-shadow: 0 0 20px #ff4b4b; background-color: #ff4b4b; color: white;}
        100% { opacity: 1.0; }
    }
    .banner-critical { font-size: 2em; font-weight: bold; text-align: center; padding: 10px; border-radius: 5px; border: 2px solid #ff4b4b; animation: blink-critical 1.5s infinite; margin-bottom: 20px; }
    .banner-warning { font-size: 2em; font-weight: bold; text-align: center; padding: 10px; border-radius: 5px; background-color: rgba(255, 165, 0, 0.2); color: #ffa500; border: 2px solid #ffa500; margin-bottom: 20px; }
    .banner-stable { font-size: 2em; font-weight: bold; text-align: center; padding: 10px; border-radius: 5px; background-color: rgba(0, 255, 0, 0.1); color: #00ff00; border: 2px solid #00ff00; margin-bottom: 20px; }
    
    .log-container { background-color: #0e1117; font-family: 'Courier New', monospace; padding: 15px; border-radius: 5px; height: 350px; overflow-y: scroll; border: 1px solid #333; margin-top: 10px;}
    .log-error { color: #ff4b4b; font-weight: bold; }
    .log-warn { color: #ffa500; }
    .log-info { color: #aaaaaa; }
    .log-system { color: #00bfff; font-weight: bold;}
    .action-impact-good { color: #00ff00; font-weight: bold; font-size: 1.2em; }
    .action-impact-bad { color: #ff4b4b; font-weight: bold; font-size: 1.2em; }
</style>
""", unsafe_allow_html=True)

# --- STATE MANAGEMENT ---
if "obs" not in st.session_state:
    st.session_state.obs = None
if "history" not in st.session_state:
    st.session_state.history = []
if "rewards" not in st.session_state:
    st.session_state.rewards = [0.0]
if "step_count" not in st.session_state:
    st.session_state.step_count = 0
if "is_resolved" not in st.session_state:
    st.session_state.is_resolved = False
if "agent_thought" not in st.session_state:
    st.session_state.agent_thought = ""
if "agent_action" not in st.session_state:
    st.session_state.agent_action = ""
if "final_score" not in st.session_state:
    st.session_state.final_score = None
if "story_timeline" not in st.session_state:
    st.session_state.story_timeline = []
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False

def create_metric_chart(title, value, max_val, danger_threshold, invert=False):
    is_danger = (value < danger_threshold) if invert else (value > danger_threshold)
    color = "#ff4b4b" if is_danger else "#00bfff"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': title},
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {'axis': {'range': [None, max_val]},
                 'bar': {'color': color}}
    ))
    fig.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
    return fig

def reset_env(task_id):
    try:
        res = requests.post(f"{API_URL}/reset", json={"task_id": task_id, "seed": int(time.time()*1000)%10000})
        if res.status_code == 200:
            st.session_state.obs = res.json()
            st.session_state.history = []
            st.session_state.rewards = [0.0]
            st.session_state.step_count = 0
            st.session_state.is_resolved = False
            st.session_state.agent_thought = ""
            st.session_state.agent_action = ""
            st.session_state.final_score = None
            st.session_state.story_timeline = [f"Started {task_id.upper()} incident"]
            st.session_state.demo_mode = False
    except Exception as e:
        st.error(f"API Connection error: {e}")

def determine_severity(obs):
    if not obs: return "stable"
    cpu, mem, lat = obs['system_metrics']['cpu_percent'], obs['system_metrics']['memory_percent'], obs['system_metrics']['latency_ms']
    components = obs['components_health'].values()
    if lat > 1000 or mem > 90 or cpu > 90 or "failed" in components or obs['deployment_status'] == "failing":
        return "critical"
    if lat > 300 or mem > 70 or cpu > 70 or "degraded" in components:
        return "warning"
    return "stable"

def step_env(action_str):
    if getattr(st.session_state, "final_score", None) is not None: return
        
    old_lat = st.session_state.obs['system_metrics']['latency_ms'] if st.session_state.obs else 0
    try:
        res = requests.post(f"{API_URL}/step", json={"action_type": action_str})
        if res.status_code == 200:
            data = res.json()
            st.session_state.obs = data["observation"]
            st.session_state.history.append(action_str)
            st.session_state.rewards.append(data["info"].get("cumulative_reward", 0.0))
            st.session_state.step_count = data["info"].get("step_count", 0)
            st.session_state.is_resolved = data["info"].get("resolved", False)
            
            new_lat = st.session_state.obs['system_metrics']['latency_ms']
            if new_lat > old_lat + 100:
                st.session_state.story_timeline.append(f"Action '{action_str}' → Degradation ↑")
            elif new_lat < old_lat - 100:
                st.session_state.story_timeline.append(f"Action '{action_str}' → Latency ↓")
            else:
                st.session_state.story_timeline.append(f"Action '{action_str}' → No major change")
                
            if data["done"]:
                timeline = st.session_state.obs["timeline"]
                grade_res = requests.post(f"{API_URL}/grader", json={
                    "timeline": timeline, "action_history": st.session_state.history,
                    "is_resolved": st.session_state.is_resolved, "task_id": st.session_state.current_task
                })
                if grade_res.status_code == 200:
                    st.session_state.final_score = grade_res.json().get("score", 0.0)
    except Exception as e:
        st.error(f"Step fail: {e}")

# --- INIT ---
try:
    tasks_dict = requests.get(f"{API_URL}/tasks").json()
except:
    st.error("Backend API Offline. Start the API or run via `app.py` wrapper.")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("AIOps Control")
    
    st.markdown("---")
    st.markdown("**LLM Configuration**")
    provider_sel = st.selectbox("LLM Provider", ["openai", "groq"], index=1)
    os.environ["LLM_PROVIDER"] = provider_sel
    
    if provider_sel == "groq":
        os.environ["GROQ_API_KEY"] = "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"
        st.caption("✅ Default Key Connected")
    else:
        openai_key = st.text_input("OpenAI API Key", value=os.getenv("OPENAI_API_KEY", ""), type="password")
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key

    st.markdown("---")
    st.markdown("**Scenario Console**")
    task_sel = st.selectbox("Select Scenario", list(tasks_dict.keys()))
    if st.button("Initialize Scenario", width="stretch"):
        st.session_state.current_task = task_sel
        reset_env(task_sel)
        
    st.markdown("---")
    st.markdown("**Showcase Modes**")
    if st.button("▶️ Play Hard Demo", width="stretch", type="primary"):
        st.session_state.current_task = "hard"
        reset_env("hard")
        st.session_state.demo_mode = True

if st.session_state.obs is None:
    st.info("👈 Initialize a scenario to begin.")
    st.stop()

obs = st.session_state.obs
severity = determine_severity(obs)

# --- REPLAY & DEMO LOGIC ---
if st.session_state.demo_mode and not st.session_state.is_resolved and st.session_state.final_score is None:
    demo_script = [
        ("THOUGHT: Deployment status is failing and latency is extremely high. I need to run diagnostics first.", "run_diagnostics"),
        ("THOUGHT: Diagnostics confirm high crash loop backoff on new pods. Latency is cascading. We must scale up immediately to buy time against DB overload.", "scale_up"),
        ("THOUGHT: Scaled up nodes. Now I need to rollback the bad deployment to permanently fix traffic.", "rollback_deploy")
    ]
    step_idx = st.session_state.step_count
    if step_idx < len(demo_script):
        time.sleep(1.0) # cinematic pause
        st.session_state.agent_thought = demo_script[step_idx][0]
        st.session_state.agent_action = demo_script[step_idx][1]
        step_env(demo_script[step_idx][1])
        st.rerun()

# --- BANNER ---
if severity == "critical":
    st.markdown("<div class='banner-critical'>🚨 CRITICAL SEV-1 INCIDENT DETECTED 🚨</div>", unsafe_allow_html=True)
elif severity == "warning":
    st.markdown("<div class='banner-warning'>⚠️ SYSTEM DEGRADED: AWAITING ACTION ⚠️</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='banner-stable'>✅ SYSTEM STABLE: NO ANOMALIES ✅</div>", unsafe_allow_html=True)

# --- TRACKS ---
st.write("<br>", unsafe_allow_html=True)
st.subheader("📊 Live Telemetry")

cpu = obs['system_metrics']['cpu_percent']
mem = obs['system_metrics']['memory_percent']
lat = obs['system_metrics']['latency_ms']

tel_col1, tel_col2, tel_col3 = st.columns(3, gap="large")

with tel_col1:
    st.markdown("<h4 style='text-align: center'>CPU Usage</h4>", unsafe_allow_html=True)
    st.plotly_chart(create_metric_chart("", cpu, 100, 85), width="stretch")

with tel_col2:
    st.markdown("<h4 style='text-align: center'>Memory Usage</h4>", unsafe_allow_html=True)
    st.plotly_chart(create_metric_chart("", mem, 100, 85), width="stretch")

with tel_col3:
    st.markdown("<h4 style='text-align: center'>Latency</h4>", unsafe_allow_html=True)
    st.plotly_chart(create_metric_chart("", lat, 1500, 500), width="stretch")

st.write("<br>", unsafe_allow_html=True)

col1, col2 = st.columns([1.5, 1])

with col1:
    st.markdown("**Incident Timeline:**")
    story_html = " ➔ ".join([f"**{x}**" for x in st.session_state.story_timeline[-3:]])
    st.info(story_html if story_html else "Awaiting events...")
    
    st.subheader("🧾 System Diagnostic Stream")
    logs_html = "<div class='log-container'>"
    for log in obs['logs']:
        if any(x in log for x in ["ERROR", "timeout", "failed", "OOMKilled"]):
            logs_html += f"<span class='log-error'>[ERR] {log}</span><br>"
        elif "WARN" in log:
            logs_html += f"<span class='log-warn'>[WARN] {log}</span><br>"
        elif "SYSTEM" in log or "DIAGNOSTIC" in log or "INFO" in log:
            logs_html += f"<span class='log-system'>[SYS] {log}</span><br>"
        else:
            logs_html += f"<span class='log-info'>[LOG] {log}</span><br>"
    logs_html += "</div>"
    st.markdown(logs_html, unsafe_allow_html=True)

    df_rewards = pd.DataFrame({"Step": range(len(st.session_state.rewards)), "Cumulative Reward": st.session_state.rewards})
    fig_line = go.Figure(go.Scatter(x=df_rewards['Step'], y=df_rewards['Cumulative Reward'], mode='lines+markers', line=dict(color='#00bfff', width=3)))
    fig_line.update_layout(height=180, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
    st.plotly_chart(fig_line, width="stretch")

with col2:
    st.subheader("🎮 Ops Command")
    
    tab1, tab2 = st.tabs(["Manual Override", "LLM Agent Matrix"])
    
    with tab1:
        st.markdown("Execute actions directly.")
        actions = ["restart_service", "rollback_deploy", "scale_up", "check_logs", "run_diagnostics", "fix_database", "flush_cache", "ignore"]
        selected_action = st.selectbox("Action Directive:", actions)
        if st.button("EXECUTE", type="primary", disabled=(st.session_state.final_score is not None)):
            step_env(selected_action)
            st.rerun()
            
    with tab2:
        st.markdown("Invoke the autonomous ReAct baseline agent.")
        if st.button("Trigger Agent Next Step", type="primary", disabled=(st.session_state.final_score is not None)):
            with st.spinner("Analyzing incident trajectory..."):
                desc = tasks_dict[st.session_state.current_task]["description"]
                thought, act = get_action_from_llm(obs, desc, st.session_state.history)
                
                if thought.startswith("LLM Error:"):
                    st.error(thought)
                else:
                    st.session_state.agent_thought = thought
                    st.session_state.agent_action = act
                    step_env(act)
                    st.rerun()

        st.caption("AGENT REASONING:")
        st.code(st.session_state.agent_thought if st.session_state.agent_thought else "Awaiting orders...", language="text")
        if st.session_state.agent_action:
            st.success(f"Action Issued: {st.session_state.agent_action}")

if st.session_state.final_score is not None:
    st.markdown("---")
    st.header(f"🏆 Trajectory Evaluation Complete! Score: {st.session_state.final_score:.2f} / 1.0")
    if st.session_state.is_resolved:
        st.success("✅ **RESOLUTION ACHIEVED.** Root cause identified and neutralized efficiently.")
    else:
        st.error("🚫 **TIMED OUT OR CASCADED.** System failed to recover gracefully.")
