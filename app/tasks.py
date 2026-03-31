TASKS = {
    "easy": {
        "id": "easy",
        "description": "System showing high memory usage. Find the hidden root cause (cache) and fix it.",
        "incident_type": "cache_failure",
        "optimal_steps": 2 # run_diagnostics, flush_cache
    },
    "medium": {
        "id": "medium",
        "description": "High API latency with misleading CPU logs. Diagnose and fix the DB lock.",
        "incident_type": "db_lock",
        "optimal_steps": 2 # run_diagnostics, fix_database
    },
    "hard": {
        "id": "hard",
        "description": "Cascading failure starting from a bad deploy. Requires scaling up to mitigate, then rolling back.",
        "incident_type": "failed_deployment",
        "optimal_steps": 3 # run_diagnostics, scale_up, rollback_deploy
    }
}
