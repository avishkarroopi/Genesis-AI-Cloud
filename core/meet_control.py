# meet_control.py
import threading
from core.automation_engine import send_n8n_command  # type: ignore

def start_meet():
    return send_n8n_command("meet", "start_meeting")

def join_meet(link):
    return send_n8n_command("meet", "join_meeting", {"link": link})

def end_meet():
    return send_n8n_command("meet", "end_meeting")

def mute():
    return send_n8n_command("meet", "mute")

def unmute():
    return send_n8n_command("meet", "unmute")
