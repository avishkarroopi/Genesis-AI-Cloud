"""
Phase B — Autonomous Learning Loop
Record and evaluate generic command experiences over iterations.
"""

def evaluate_experience(command: str, result: str) -> bool:
    if "Error:" in result or "Failed" in result or "failed" in result.lower():
        return False
    if "timeout" in result.lower():
        return False
    if len(result) <= 20:
        return False
    return True

def record_experience(command: str, result: str):
    success = evaluate_experience(command, result)
    import datetime
    timestamp = datetime.datetime.now().isoformat()
    record = {
        "command": command,
        "result_summary": result[:200] + ("..." if len(result) > 200 else ""),
        "success": success,
        "timestamp": timestamp
    }
    
    try:
        from core.memory.memory_store import add_memory_safe
        fact = f"User asked about: {command}. Planner handled: {record['result_summary']}. Outcome: {'Success' if success else 'Failed'}."
        add_memory_safe(fact, metadata={"type": "experience", "success": success, "timestamp": timestamp, "category": "experience"})
    except Exception as e:
        print(f"[LEARNING] Failed to record experience: {e}", flush=True)

def get_learning_engine():
    """Safe minimal stub for the learning engine importer."""
    return None

def start_learning_engine():
    """Start the autonomous learning loop (stub — records experiences passively)."""
    print("[LEARNING] Learning engine started (passive mode).", flush=True)

