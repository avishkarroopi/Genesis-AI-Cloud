"""
GENESIS AI Router — Architecture Upgrade.
Native LLM tool-calling via Groq/OpenRouter function-calling API.
Keyword fallback retained as safety net.
"""

import os
import re
import time
import json
import subprocess
import requests
from core import config
from core.config import GROQ_API_KEY
from core.config import OPENROUTER_API_KEY
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# --- LangSmith Tracing Activation ---
try:
    from core.tracing import is_tracing_active
except Exception:
    def is_tracing_active(): return False

# --- Verified OpenRouter model IDs ---
OR_CODING_MODEL = "deepseek/deepseek-chat"
OR_REASONING_MODEL = "deepseek/deepseek-r1"
OLLAMA_FALLBACK_MODEL = "phi3"

# --- Tool Schema Definitions for Native LLM Tool-Calling ---
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "system_time",
            "description": "Get the current system date and time",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the internet for information on a topic",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "file_operations",
            "description": "Perform file operations: read, write, list, or delete files",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["read", "write", "list", "delete"]},
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "Content for write operation"}
                },
                "required": ["operation", "path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "code_execution",
            "description": "Execute a code snippet or script",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to execute"},
                    "language": {"type": "string", "description": "Programming language", "default": "python"}
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "Send a message via Telegram, Slack, or Twilio",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "enum": ["telegram", "slack", "twilio"]},
                    "recipient": {"type": "string", "description": "Chat ID, channel, or phone number"},
                    "text": {"type": "string", "description": "Message text"}
                },
                "required": ["platform", "recipient", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calendar_event",
            "description": "Create or query calendar events",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"}
                },
                "required": ["title", "start_time", "end_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email via Gmail",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
]

# --- Legacy keyword lists (fallback only) ---
CODING_TASKS = [
    "code", "python", "script", "function", "program",
    "algorithm", "debug", "compile", "write function", "fix code"
]
RESEARCH_TASKS = [
    "explain", "analyze", "compare", "research",
    "theory", "why", "how does", "study",
    "history", "details", "information"
]
REASONING_TASKS = [
    "strategy", "pros and cons", "decision", "plan",
    "evaluate", "assess"
]
AUTOMATION_TASKS = [
    "open", "launch", "run", "execute", "start",
    "automation", "workflow"
]
MEMORY_TASKS = [
    "remember", "recall", "memory", "what did i", "what did you",
    "who is", "what is my", "store this", "note that", "save this"
]

_router_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="Router")

print("ROUTER INIT", flush=True)

_OLLAMA_URL = "http://127.0.0.1:11434"
_MODEL = "phi3"
model_ready = True


# -------------------------
# GPU CHECK (safe)
# -------------------------

def _has_gpu():
    try:
        subprocess.check_output(
            ["nvidia-smi"],
            stderr=subprocess.DEVNULL,
            creationflags=0x08000000 if os.name == "nt" else 0,
        )
        print("[ROUTER] GPU detected", flush=True)
        return 99
    except Exception:
        print("[ROUTER] CPU mode", flush=True)
        return 0


_GPU_LAYERS = _has_gpu()


# -------------------------
# FAST OLLAMA CHECK
# -------------------------

def _ollama_running():
    try:
        r = requests.get(f"{_OLLAMA_URL}/api/tags", timeout=1)
        return r.status_code == 200
    except Exception:
        return False

_ollama_started = False


def _start_ollama_if_needed():
    global _ollama_started
    if _ollama_running():
        return True
    if _ollama_started:
        return False
    _ollama_started = True
    print("[ROUTER] Starting Ollama...", flush=True)
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=0x08000000 if os.name == "nt" else 0,
        )
    except Exception:
        print("[ROUTER] Ollama not found", flush=True)
        return False
    for _ in range(6):
        time.sleep(0.5)
        if _ollama_running():
            print("[ROUTER] Ollama OK", flush=True)
            return True
    print("[ROUTER] Ollama start timeout", flush=True)
    return False


class RoutingDecision:
    def __init__(self, intent, model, use_planner, use_tools):
        self.intent = intent
        self.model = model
        self.use_planner = use_planner
        self.use_tools = use_tools


# -------------------------
# TOOL CALL DISPATCHER
# -------------------------

def _dispatch_tool_call(tool_name: str, arguments: dict) -> str:
    """Dispatch a tool call from the LLM to the appropriate tool in the registry."""
    try:
        from core.tool_registry import get_tool_registry
        import asyncio

        registry = get_tool_registry()

        # Map LLM tool names to registry tool IDs
        tool_map = {
            "system_time": "system_time",
            "web_search": "web_search",
            "file_operations": "advanced_file_read",
            "code_execution": "run_script",
            "send_message": None,  # handled inline
            "calendar_event": "create_calendar_event",
            "send_email": "send_email",
        }

        # Special handling for messaging (platform-specific dispatch)
        if tool_name == "send_message":
            platform = arguments.get("platform", "telegram")
            if platform == "telegram":
                tool_id = "send_telegram_message"
                kwargs = {"chat_id": arguments.get("recipient", ""), "text": arguments.get("text", "")}
            elif platform == "slack":
                tool_id = "send_slack_message"
                kwargs = {"channel": arguments.get("recipient", ""), "text": arguments.get("text", "")}
            elif platform == "twilio":
                tool_id = "send_twilio_sms"
                kwargs = {"to_number": arguments.get("recipient", ""), "message": arguments.get("text", "")}
            else:
                return f"Unknown messaging platform: {platform}"
        else:
            tool_id = tool_map.get(tool_name)
            if not tool_id:
                return f"Unknown tool: {tool_name}"
            kwargs = arguments

        # Handle system_time inline (no registry needed)
        if tool_name == "system_time":
            import datetime
            return f"Current time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # Execute tool via registry
        async def _run():
            return await registry.execute_tool(tool_id, **kwargs)

        try:
            loop = asyncio.get_running_loop()
            future = asyncio.run_coroutine_threadsafe(_run(), loop)
            return str(future.result(timeout=15))
        except RuntimeError:
            return str(asyncio.run(_run()))

    except Exception as e:
        print(f"[ROUTER] Tool dispatch error: {e}", flush=True)
        return f"Tool execution failed: {e}"


# -------------------------
# KEYWORD ROUTING (fallback)
# -------------------------

def _keyword_routing(command):
    """Original keyword-based intent classification (fallback)."""
    low_cmd = command.lower()
    intent = "GENERAL"
    use_planner = False
    use_tools = False

    if any(kw in low_cmd for kw in AUTOMATION_TASKS):
        intent = "AUTOMATION"
        use_tools = True
    elif any(kw in low_cmd for kw in CODING_TASKS):
        intent = "CODING"
    elif any(kw in low_cmd for kw in RESEARCH_TASKS):
        intent = "RESEARCH"
        use_planner = True
    elif any(kw in low_cmd for kw in REASONING_TASKS):
        intent = "REASONING"
        use_planner = True

    return RoutingDecision(
        intent=intent,
        model=OLLAMA_FALLBACK_MODEL,
        use_planner=use_planner,
        use_tools=use_tools
    )


def _classify_intent(user_command):
    """Classify intent from the raw user command ONLY.
    Never pass system prompt, memory, or persona text here.
    Returns: 'GENERAL', 'CODING', 'RESEARCH', 'REASONING', or 'AUTOMATION'
    """
    low = user_command.lower()
    if any(re.search(rf"\b{kw}\b", low) for kw in AUTOMATION_TASKS):
        return "AUTOMATION"
    elif any(re.search(rf"\b{kw}\b", low) for kw in CODING_TASKS):
        return "CODING"
    elif any(re.search(rf"\b{kw}\b", low) for kw in RESEARCH_TASKS):
        return "RESEARCH"
    elif any(re.search(rf"\b{kw}\b", low) for kw in REASONING_TASKS):
        return "REASONING"
    elif any(re.search(rf"\b{kw}\b", low) for kw in MEMORY_TASKS):
        return "MEMORY"
    else:
        return "GENERAL"


def analyze_routing(command):
    """Phase-1: Try semantic router first, fallback to keywords."""
    try:
        from core.intelligence.semantic_router import get_semantic_router
        sr = get_semantic_router()
        result = sr.analyze(command)
        if result is not None:
            return result
    except Exception as e:
        print(f"[ROUTER] Semantic router failed, using keywords: {e}", flush=True)
    return _keyword_routing(command)


# -------------------------
# MAIN ROUTER (with native tool-calling)
# -------------------------

def route_ai_request(prompt, owner_address="Sir", user_command=None, stream=False, stream_callback=None):
    """Route the AI request to the appropriate model provider.

    Uses native LLM tool-calling when available (Groq function-calling API).
    Falls back to keyword routing + regex tool tags if tool-calling fails.
    """
    classify_text = user_command if user_command else prompt

    try:
        intent = _classify_intent(classify_text)
        print(f"[BRAIN] Router selected: {intent}", flush=True)

        if intent == "AUTOMATION":
            # Digital Twin pre-simulation
            try:
                from core.digital_twin.behavior_simulator import BehaviorSimulator
                sim = BehaviorSimulator()
                sim.simulate({"action": "automation", "command": user_command})
            except Exception as e:
                print(f"[ROUTER] Digital Twin simulation skipped: {e}", flush=True)

            payload = {"action": "automation", "command": user_command}
            return f'[TOOL_CALL]{{"tool": "automation_engine.trigger_webhook", "args": {json.dumps(payload)}}}[/TOOL_CALL]'

    except Exception as e:
        intent = "GENERAL"
        print(f"[BRAIN] Router fallback to GENERAL: {e}", flush=True)

    def _do_route():
        try:
            from core import face_bridge
        except ImportError:
            face_bridge = None

        # Research augmentation
        if intent == "RESEARCH":
            try:
                from core.research.research_engine import search_and_summarize
                research_data = search_and_summarize(prompt)
                if research_data:
                    augmented_prompt = f"External research results:\n{research_data}\n\nUser question:\n{prompt}"
                else:
                    augmented_prompt = prompt
            except Exception as e:
                print(f"[ROUTER] Research pipeline fallback: {e}", flush=True)
                augmented_prompt = prompt
        else:
            augmented_prompt = prompt

        # Creativity Engine augmentation
        if intent in ("RESEARCH", "REASONING"):
            try:
                from core.creativity_engine import get_creativity_engine
                c_engine = get_creativity_engine()
                innovation_hint = c_engine.get_innovation_prompt(domain=intent.lower())
                if innovation_hint:
                    augmented_prompt = f"{augmented_prompt}\n\n[Creative Perspective]: {innovation_hint}"
            except Exception:
                pass

        # Keys
        groq_key = GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        or_key = OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY")

        # --- Provider functions ---

        def try_groq_with_tools():
            """Try Groq with native tool-calling (function calling)."""
            if not groq_key:
                return None
            try:
                print("[ROUTER] Trying GROQ with tool-calling...", flush=True)
                if face_bridge: face_bridge.send_event("set_model", {"model": "GROQ"})
                t0 = time.time()

                messages = [{"role": "user", "content": augmented_prompt}]
                request_body = {
                    "model": "llama-3.1-8b-instant",
                    "messages": messages,
                    "max_tokens": 1024,
                    "tools": TOOL_SCHEMAS,
                    "tool_choice": "auto",
                }

                ret = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    json=request_body,
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    timeout=10.0,
                )
                ret.raise_for_status()
                data = ret.json()
                choice = data["choices"][0]
                message = choice["message"]

                # Check if LLM decided to call tools
                tool_calls = message.get("tool_calls", [])
                if tool_calls:
                    tool_results = []
                    for tc in tool_calls:
                        fn = tc["function"]
                        tool_name = fn["name"]
                        try:
                            tool_args = json.loads(fn.get("arguments", "{}"))
                        except Exception:
                            tool_args = {}
                        print(f"[ROUTER] LLM tool call: {tool_name}({tool_args})", flush=True)
                        result = _dispatch_tool_call(tool_name, tool_args)
                        tool_results.append(f"[{tool_name}]: {result}")

                    # Second LLM call with tool results for natural response
                    messages.append(message)
                    for i, tc in enumerate(tool_calls):
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": tool_results[i] if i < len(tool_results) else ""
                        })

                    ret2 = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        json={"model": "llama-3.1-8b-instant", "messages": messages, "max_tokens": 1024},
                        headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                        timeout=10.0,
                    )
                    ret2.raise_for_status()
                    final_text = ret2.json()["choices"][0]["message"]["content"].strip()
                    if face_bridge: face_bridge.send_event("set_network", {"network": "CONNECTED"})
                    print(f"GROQ TOOL-CALL OK | {time.time() - t0:.1f}s", flush=True)
                    return final_text if final_text else "\n".join(tool_results)

                # No tool calls — regular text response
                text = message.get("content", "").strip()
                if face_bridge: face_bridge.send_event("set_network", {"network": "CONNECTED"})
                print(f"GROQ OK | {time.time() - t0:.1f}s", flush=True)
                return text if text else None

            except Exception as e:
                print(f"[ROUTER] GROQ tool-calling failed: {e}", flush=True)
                return None

        def try_groq():
            """Try Groq cloud API (plain, no tool-calling)."""
            if not groq_key:
                return None
            try:
                print("[ROUTER] Trying GROQ (plain)...", flush=True)
                if face_bridge: face_bridge.send_event("set_model", {"model": "GROQ"})
                t0 = time.time()
                ret = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [{"role": "user", "content": augmented_prompt}],
                        "max_tokens": 1024,
                        "stream": stream
                    },
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    timeout=15.0 if stream else 5.0,
                    stream=stream
                )
                ret.raise_for_status()

                if stream:
                    full_text = ""
                    for line in ret.iter_lines():
                        if line:
                            decoded = line.decode('utf-8')
                            if decoded.startswith('data: '):
                                payload = decoded[6:]
                                if payload == '[DONE]':
                                    break
                                try:
                                    data_obj = json.loads(payload)
                                    content = data_obj['choices'][0]['delta'].get('content', '')
                                    if content:
                                        full_text += content
                                        if stream_callback:
                                            stream_callback(content)
                                except Exception:
                                    pass
                    if face_bridge: face_bridge.send_event("set_network", {"network": "CONNECTED"})
                    print(f"GROQ STREAM OK | {time.time() - t0:.1f}s", flush=True)
                    return full_text if full_text else None
                else:
                    text = ret.json()["choices"][0]["message"]["content"].strip()
                    if face_bridge: face_bridge.send_event("set_network", {"network": "CONNECTED"})
                    print(f"GROQ OK | {time.time() - t0:.1f}s", flush=True)
                    return text if text else None
            except Exception as e:
                print(f"[ROUTER] GROQ failed: {e}", flush=True)
                return None

        def try_or(model_id):
            """Try OpenRouter with a specific verified model ID."""
            if not or_key:
                return None
            try:
                print(f"[ROUTER] Trying OpenRouter ({model_id})...", flush=True)
                if face_bridge: face_bridge.send_event("set_model", {"model": "OPENROUTER"})
                t0 = time.time()
                headers = {
                    "Authorization": f"Bearer {or_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "genesis-ai",
                    "X-Title": "GENESIS"
                }
                ret = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json={
                        "model": model_id,
                        "messages": [{"role": "user", "content": augmented_prompt}],
                        "max_tokens": 1024,
                        "stream": stream
                    },
                    headers=headers,
                    timeout=15,
                    stream=stream
                )
                ret.raise_for_status()

                if stream:
                    full_text = ""
                    _in_think = False
                    for line in ret.iter_lines():
                        if line:
                            decoded = line.decode('utf-8')
                            if decoded.startswith('data: '):
                                payload = decoded[6:]
                                if payload == '[DONE]':
                                    break
                                try:
                                    data_obj = json.loads(payload)
                                    content = data_obj['choices'][0]['delta'].get('content', '')
                                    if content:
                                        if '<think>' in content: _in_think = True
                                        if '</think>' in content:
                                            _in_think = False
                                            content = content.split('</think>')[-1]
                                            content = content.lstrip('\n')
                                        if not _in_think and content:
                                            full_text += content
                                            if stream_callback:
                                                stream_callback(content)
                                except Exception:
                                    pass
                    if face_bridge: face_bridge.send_event("set_network", {"network": "CONNECTED"})
                    print(f"OPENROUTER STREAM OK ({model_id}) | {time.time() - t0:.1f}s", flush=True)
                    return full_text.strip() if full_text else None
                else:
                    text = ret.json()["choices"][0]["message"]["content"].strip()
                    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
                    if face_bridge: face_bridge.send_event("set_network", {"network": "CONNECTED"})
                    print(f"OPENROUTER OK ({model_id}) | {time.time() - t0:.1f}s", flush=True)
                    return text if text else None
            except Exception as e:
                print(f"[ROUTER] OpenRouter failed: {e}", flush=True)
                return None

        def try_ollama():
            """Fallback to local Ollama."""
            if face_bridge: face_bridge.send_event("set_model", {"model": "LOCAL"})
            url = f"{_OLLAMA_URL}/api/generate"
            payload = {
                "model": OLLAMA_FALLBACK_MODEL,
                "prompt": augmented_prompt,
                "stream": False,
                "options": {"num_predict": 500, "temperature": 0.1, "top_p": 0.9, "repeat_penalty": 1.1, "num_thread": 4, "num_gpu": _GPU_LAYERS}
            }
            if not _ollama_running():
                if not _start_ollama_if_needed():
                    print("[ROUTER] Ollama not ready, skipping.", flush=True)
                    return None
            try:
                t0 = time.time()
                r = requests.post(url, json=payload, timeout=(2, 15))
                r.raise_for_status()
                text = r.json().get("response", "").strip()
                if face_bridge: face_bridge.send_event("set_network", {"network": "CONNECTED"})
                print(f"OLLAMA OK (phi3) | {time.time() - t0:.1f}s", flush=True)
                return text if text else None
            except Exception as e:
                if face_bridge: face_bridge.send_event("set_network", {"network": "ERROR"})
                print(f"[ROUTER ERROR] Ollama: {e}", flush=True)
                return None

        # --- Provider execution order ---
        res = None

        if intent == "CODING":
            res = try_or(OR_CODING_MODEL)
            if not res: res = try_groq_with_tools()
            if not res: res = try_groq()
            if not res: res = try_ollama()

        elif intent in ("RESEARCH", "REASONING"):
            res = try_or(OR_REASONING_MODEL)
            if not res: res = try_groq_with_tools()
            if not res: res = try_groq()
            if not res: res = try_ollama()

        else:
            # GENERAL / MEMORY: Try tool-calling first, then plain
            res = try_groq_with_tools()
            if not res: res = try_groq()
            if not res: res = try_or(OR_CODING_MODEL)
            if not res: res = try_ollama()

        return res if res else "Yes?"

    # Run the blocking HTTP calls in a worker thread
    start_time = time.time()
    future = _router_pool.submit(_do_route)
    try:
        res = future.result(timeout=35)
        try:
            from core.ai_telemetry.reasoning_metrics import track_reasoning
            latency_ms = int((time.time() - start_time) * 1000)
            track_reasoning(intent=intent, latency_ms=latency_ms, success=bool(res and res != "Yes?"))
        except Exception:
            pass
        try:
            from core.telemetry.posthog_client import track_event
            track_event("prompt_executed", {"intent": intent, "latency_ms": int((time.time() - start_time) * 1000)})
        except Exception:
            pass
        return res
    except TimeoutError:
        print("[ROUTER] Thread timeout: request took too long", flush=True)
        try:
            from core.ai_telemetry.reasoning_metrics import track_reasoning
            track_reasoning(intent=intent, latency_ms=35000, success=False)
        except Exception: pass
        return "Yes?"
    except Exception as e:
        print(f"[ROUTER] Thread error: {e}", flush=True)
        try:
            from core.ai_telemetry.reasoning_metrics import track_reasoning
            latency_ms = int((time.time() - start_time) * 1000)
            track_reasoning(intent=intent, latency_ms=latency_ms, success=False)
        except Exception: pass
        return "Yes?"


def warmup_models():
    return True