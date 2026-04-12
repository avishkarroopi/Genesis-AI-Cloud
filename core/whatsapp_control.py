# whatsapp_control.py
import threading
from core.automation_engine import send_n8n_command  # type: ignore

def send_message(contact, message):
    return send_n8n_command("whatsapp", "send_message", {"contact": contact, "message": message})

def read_messages():
    return send_n8n_command("whatsapp", "read_messages")

def notify(message):
    return send_n8n_command("whatsapp", "notify", {"message": message})
