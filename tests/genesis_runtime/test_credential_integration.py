"""
TEST — Credential Integration Verification
Validates that all credentials in .env are loaded and used correctly.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
except ImportError:
    pass

os.environ.setdefault("CLOUD_MODE", "true")


def test_groq_api_key_loaded():
    key = os.environ.get("GROQ_API_KEY")
    assert key and len(key) > 10, "GROQ_API_KEY missing or too short"


def test_openrouter_api_key_loaded():
    key = os.environ.get("OPENROUTER_API_KEY")
    assert key and len(key) > 10, "OPENROUTER_API_KEY missing or too short"


def test_database_url_loaded():
    url = os.environ.get("DATABASE_URL")
    assert url and "postgresql" in url, "DATABASE_URL missing or invalid"


def test_redis_url_loaded():
    url = os.environ.get("REDIS_URL")
    assert url and "redis" in url, "REDIS_URL missing or invalid"


def test_tavily_api_key_loaded():
    key = os.environ.get("TAVILY_API_KEY")
    assert key and len(key) > 5, "TAVILY_API_KEY missing"


def test_serpapi_key_loaded():
    key = os.environ.get("SERPAPI_KEY")
    assert key and len(key) > 10, "SERPAPI_KEY missing"


def test_firecrawl_api_key_loaded():
    key = os.environ.get("FIRECRAWL_API_KEY")
    assert key and len(key) > 5, "FIRECRAWL_API_KEY missing"


def test_telegram_bot_token_loaded():
    key = os.environ.get("TELEGRAM_BOT_TOKEN")
    assert key and ":" in key, "TELEGRAM_BOT_TOKEN missing or malformed"


def test_twilio_credentials_loaded():
    sid = os.environ.get("TWILIO_ACCOUNT_SID")
    token = os.environ.get("TWILIO_AUTH_TOKEN")
    assert sid and sid.startswith("AC"), "TWILIO_ACCOUNT_SID missing or invalid"
    assert token and len(token) > 10, "TWILIO_AUTH_TOKEN missing"


def test_slack_tokens_loaded():
    app = os.environ.get("SLACK_APP_TOKEN")
    socket = os.environ.get("SLACK_SOCKET_TOKEN")
    assert app and app.startswith("xoxb"), "SLACK_APP_TOKEN missing or invalid"
    assert socket and socket.startswith("xapp"), "SLACK_SOCKET_TOKEN missing or invalid"


def test_google_credentials_loaded():
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    assert client_id and ".apps.googleusercontent.com" in client_id, "GOOGLE_CLIENT_ID missing"
    assert client_secret and client_secret.startswith("GOCSPX"), "GOOGLE_CLIENT_SECRET missing"


def test_sentry_dsn_loaded():
    dsn = os.environ.get("SENTRY_DSN")
    assert dsn and "sentry.io" in dsn, "SENTRY_DSN missing or invalid"


def test_logtail_token_loaded():
    token = os.environ.get("LOGTAIL_SOURCE_TOKEN")
    assert token and len(token) > 5, "LOGTAIL_SOURCE_TOKEN missing"


def test_groq_api_connectivity():
    """Verify Groq API key works by listing models."""
    import requests
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        return
    try:
        resp = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10
        )
        assert resp.status_code == 200, f"Groq API returned {resp.status_code}"
    except requests.exceptions.ConnectionError:
        pass  # Network unavailable — skip


def test_tavily_api_connectivity():
    """Verify Tavily API key works with a test search."""
    import requests
    key = os.environ.get("TAVILY_API_KEY")
    if not key:
        return
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": key, "query": "test", "max_results": 1},
            timeout=10
        )
        assert resp.status_code == 200, f"Tavily API returned {resp.status_code}"
    except requests.exceptions.ConnectionError:
        pass  # Network unavailable — skip


def test_telegram_api_connectivity():
    """Verify Telegram bot token works by calling getMe."""
    import requests
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return
    try:
        resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        assert resp.status_code == 200, f"Telegram API returned {resp.status_code}"
    except requests.exceptions.ConnectionError:
        pass


def test_tool_registry_has_new_tools():
    """Verify system_time and twilio tools are registerable."""
    from core.tools.system_time_tool import register_system_time_tool
    from core.tools.twilio_tool import register_twilio_tool
    from core.tool_registry import get_tool_registry

    register_system_time_tool()
    register_twilio_tool()

    registry = get_tool_registry()
    assert registry.get_tool("system_time") is not None
    assert registry.get_tool("send_twilio_sms") is not None


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
