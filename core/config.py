# ==========================================
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass


# -- AI Models & API Keys --
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3")
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "phi3")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.0-flash")
FALLBACK_ORDER = os.getenv("FALLBACK_ORDER", "ollama,gemini,openrouter,openai").split(",")

# All secrets MUST be provided via .env file — no hardcoded keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# -- Automation & n8n --
N8N_URL = os.getenv("N8N_URL", "http://localhost:5678")
N8N_KEY = os.getenv("N8N_API_KEY", "")
N8N_WEBHOOK = os.getenv("N8N_WEBHOOK", "")

# -- External Integrations --
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")
WHATSAPP_BUSINESS_ID = os.getenv("WHATSAPP_BUSINESS_ID", "")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# -- Robot & Hardware Control --
ROBOT_IP = os.getenv("ROBOT_IP", "127.0.0.1")
ROBOT_PORT = int(os.getenv("ROBOT_PORT", "9090"))
SERIAL_PORT = os.getenv("SERIAL_PORT", "COM3")
# -- Performance --
fast_mode = True
low_latency = True
SAFE_START = False
OWNER_NAME = os.getenv("OWNER_NAME", "Avishkar")

