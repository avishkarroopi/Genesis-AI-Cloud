# automation_skill.py
def trigger(event_name: str, payload: dict):
    return f"Triggered automation webhook {event_name} with {payload}"
