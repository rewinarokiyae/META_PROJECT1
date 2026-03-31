import random
from typing import Dict, Any, List

class Simulator:
    def __init__(self):
        self.reset()

    def reset(self, incident_type="random", seed: int = None):
        if seed is not None:
            random.seed(seed)
            
        self.components = {
            "api": "healthy",
            "db": "healthy",
            "cache": "healthy",
            "load_balancer": "healthy"
        }
        
        self.cpu = 20.0 + random.uniform(-2, 2)
        self.memory = 40.0 + random.uniform(-2, 2)
        self.latency = 50.0 + random.uniform(-5, 5)
        self.deployment_status = "stable"
        self.region = "us-east-1"
        self.is_resolved = False
        
        self.timeline: List[Dict[str, Any]] = [{"step": 0, "event": "Environment initialized"}]
        self.logs = ["System nominal"]
        
        INCIDENTS = ["cache_failure", "db_lock", "failed_deployment"]
        if incident_type == "random":
            self.root_cause = random.choice(INCIDENTS)
        else:
            self.root_cause = incident_type
            
        self.active_issues = {self.root_cause: True}
        self.step_count = 0
        
        # Setup initial misleading/surface symptoms based on root cause
        if self.root_cause == "cache_failure":
            self.memory += 40.0
            self.components["cache"] = "failed"
            self.logs.append("WARN: High memory utilization detected on Cache nodes")
            # Surface symptom looks like memory leak
        elif self.root_cause == "db_lock":
            self.latency += 200.0
            self.cpu += 30.0
            self.components["db"] = "degraded"
            # Misleading logs
            self.logs.append("ERROR: API timeout waiting for downstream")
            if random.random() > 0.5:
                self.logs.append("WARN: CPU usage spiking due to background processes")
        elif self.root_cause == "failed_deployment":
            self.deployment_status = "failing"
            self.components["api"] = "degraded"
            self.latency += 150.0
            self.logs.append("ERROR: Pods crashing locally on new deploy v2.4")

    def log_event(self, event: str):
        self.timeline.append({"step": self.step_count, "event": event})
        self.logs.append(event)
        
    def step(self, action_type: str) -> Dict[str, Any]:
        self.step_count += 1
        diagnostics_run = False
        correct_action = False
        action_result = "No effect"
        
        # Apply action effects
        if action_type == "restart_service":
            if self.root_cause == "cache_failure" and self.active_issues.get("cache_failure"):
                # Temporary fix - memory goes down but comes back if cache isn't flushed
                self.memory = max(30.0, self.memory - 20)
                action_result = "Service restarted. Memory temporarily dropping."
            else:
                action_result = "Service restarted. Some active connections dropped."
                self.latency += 10.0
                
        elif action_type == "fix_database":
            if self.root_cause == "db_lock" and self.active_issues.get("db_lock"):
                self.active_issues["db_lock"] = False
                self.components["db"] = "healthy"
                action_result = "Database locks cleared. Connections freed."
                correct_action = True
            else:
                action_result = "Database re-indexed. Short latency spike incurred."
                self.latency += 50.0
                
        elif action_type == "scale_up":
            if self.root_cause == "failed_deployment":
                action_result = "Scaled up API nodes. Bought some time against crashes."
                self.latency = max(50.0, self.latency - 50)
            else:
                action_result = "Scaled up instances, but root cause remains."
                self.cpu = max(20.0, self.cpu - 10)
                
        elif action_type == "rollback_deploy":
            if self.root_cause == "failed_deployment" and self.active_issues.get("failed_deployment"):
                self.deployment_status = "stable"
                self.components["api"] = "healthy"
                self.active_issues["failed_deployment"] = False
                action_result = "Rollback successful. Traffic recovering."
                correct_action = True
            else:
                action_result = "Rolled back to previous version. No notable impact."
                
        elif action_type == "flush_cache":
            if self.root_cause == "cache_failure" and self.active_issues.get("cache_failure"):
                self.components["cache"] = "healthy"
                self.active_issues["cache_failure"] = False
                self.memory = 40.0
                action_result = "Cache flushed and resized. Memory stable."
                correct_action = True
            else:
                action_result = "Cache flushed. Increased API latency temporarily."
                self.latency += 100.0

        elif action_type in ["check_logs", "run_diagnostics"]:
            diagnostics_run = True
            if action_type == "run_diagnostics":
                if self.root_cause == "db_lock":
                    action_result = "DIAGNOSTIC: DB locks detected on critical tables."
                elif self.root_cause == "cache_failure":
                    action_result = "DIAGNOSTIC: Cache node OOM exceptions found in kernel logs."
                elif self.root_cause == "failed_deployment":
                    action_result = "DIAGNOSTIC: High crash loop backoff rate on new API pods."
                else:
                    action_result = "DIAGNOSTIC: All systems normal."
            else:
                action_result = "Checked recent system logs."
                
        elif action_type == "ignore":
            action_result = "Ignored situation."
        else:
            action_result = f"INVALID ACTION: {action_type}"
            
        invalid_action = action_result.startswith("INVALID")
        if invalid_action:
            self.log_event(f"Agent attempted unsupported action: {action_type}")
        else:
            self.log_event(f"Action taken: {action_type} -> {action_result}")

        # Dynamic System Evolution (Degradation if not fixed)
        if self.active_issues.get("db_lock"):
            self.latency += random.uniform(10, 50)
            self.cpu += random.uniform(2, 5)
            self.log_event("SYSTEM: DB connections piling up, latency increasing.")
            if self.latency > 1000:
                self.components["api"] = "failed" # Cascading failure
                self.log_event("SYSTEM: API service failed due to DB timeout cascade.")
                
        if self.active_issues.get("cache_failure"):
            self.memory += random.uniform(2, 8)
            self.latency += random.uniform(5, 20)
            if self.memory > 95:
                self.components["api"] = "degraded"
                self.log_event("SYSTEM: API nodes struggling due to cache misses and OOM.")
                
        if self.active_issues.get("failed_deployment"):
            self.latency += random.uniform(20, 60)
            if self.step_count > 3:
                self.components["db"] = "degraded"
                self.log_event("SYSTEM: Bad queries from failing deploy overloading DB.")

        # Ensure bounds
        self.cpu = min(100.0, max(0.0, self.cpu))
        self.memory = min(100.0, max(0.0, self.memory))

        # Check resolution
        if not any(self.active_issues.values()):
            if not self.is_resolved:
                self.latency = max(50.0 + random.uniform(-5, 5), self.latency - 150.0)
                self.cpu = max(20.0 + random.uniform(-2, 2), self.cpu - 30.0)
                self.memory = max(40.0 + random.uniform(-2, 2), self.memory - 20.0)
                
                for k in self.components:
                    self.components[k] = "healthy"
                    
                if self.memory < 70.0 and self.latency < 200.0:
                    self.is_resolved = True
                    self.log_event("SYSTEM: All active issues resolved. Metrics fully normalized.")
                
        return {
            "correct_action": correct_action,
            "diagnostics_run": diagnostics_run,
            "action_result": action_result,
            "invalid_action": locals().get("invalid_action", False)
        }

    def get_state(self):
        return {
            "system_metrics": {
                "cpu_percent": round(self.cpu, 2),
                "memory_percent": round(self.memory, 2),
                "latency_ms": round(self.latency, 2)
            },
            "components_health": self.components.copy(),
            "logs": self.logs[-5:], # last 5 logs for context
            "deployment_status": self.deployment_status,
            "region_info": self.region,
            "timeline": self.timeline.copy()
        }
