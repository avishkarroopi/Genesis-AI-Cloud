"""
GENESIS AI Router — Surgical repair.
Safe version — no long blocking.
"""

import os
import re
import time
import subprocess
import requests
from core import config
from core.config import GROQ_API_KEY
from core.config import OPENROUTER_API_KEY
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# --- Verified OpenRouter model IDs (2026-04-08) ---
OR_CODING_MODEL = "deepseek/deepseek-chat"      # Coding-grade model
OR_REASONING_MODEL = "deepseek/deepseek-r1"     # Reasoning model
OLLAMA_FALLBACK_MODEL = "phi3"                   # Only installed local model

# --- Intent keyword lists (used on raw user command ONLY) ---
CODING_TASKS = [
    "code", "python", "script", "function", "program",
    "algorithm", "debug", "compile", "write function",
    "fix code"
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
model_ready = True  # Model is strictly prepared by parent sequence


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

    # wait max 3 seconds only
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
# CLASSIFY INTENT (user command only)
# -------------------------

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


# -------------------------
# MAIN ROUTER
# -------------------------

def route_ai_request(prompt, owner_address="Sir", user_command=None, stream=False, stream_callback=None):
    """Route the AI request to the appropriate model provider.

    Args:
        prompt: The full enriched prompt (system prompt + context + user command).
                This is sent to the model AS-IS.
        owner_address: How to address the owner.
        user_command: The raw user command text, used ONLY for intent classification.
                      If None, falls back to classifying the full prompt (legacy behavior).
        stream: Optional flag to stream response via stream_callback.
        stream_callback: Callable accepting string token chunks.
    """
    # --- ISSUE 1 FIX: Classify on user_command only ---
    classify_text = user_command if user_command else prompt

    try:
        intent = _classify_intent(classify_text)
        print(f"[BRAIN] Router selected: {intent}", flush=True)

        if intent == "AUTOMATION":
            import json
            payload = {
                "action": "automation",
                "command": user_command
            }
            return f"[TOOL_CALL]{{\"tool\": \"automation_engine.trigger_webhook\", \"args\": {json.dumps(payload)}}}[/TOOL_CALL]"

    except Exception as e:
        intent = "GENERAL"
        print(f"[BRAIN] Router fallback to GENERAL: {e}", flush=True)

    def _do_route():
        try:
            from core import face_bridge
        except ImportError:
            face_bridge = None

        # Research augmentation for RESEARCH intent
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

        # Keys
        groq_key = GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        or_key = OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY")

        # --- Provider functions ---

        def try_groq():
            """Try Groq cloud API. Available as primary or fallback for ANY intent."""
            if not groq_key:
                return None
            try:
                print("[ROUTER] Trying GROQ...", flush=True)
                if face_bridge: face_bridge.send_event("set_model", {"model": "GROQ"})
                t0 = time.time()
                ret = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [
                            {"role": "user", "content": augmented_prompt}
                        ],
                        "max_tokens": 1024,
                        "stream": stream
                    },
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    timeout=15.0 if stream else 5.0,
                    stream=stream
                )
                ret.raise_for_status()
                
                if stream:
                    import json
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
            except requests.exceptions.RequestException as e:
                print(f"[ROUTER] GROQ failed (network): {e}", flush=True)
                return None
            except Exception as e:
                print(f"[ROUTER] GROQ failed ({type(e).__name__}): {e}", flush=True)
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
                        "messages": [
                            {"role": "user", "content": augmented_prompt}
                        ],
                        "max_tokens": 1024,
                        "stream": stream
                    },
                    headers=headers,
                    timeout=15,
                    stream=stream
                )
                ret.raise_for_status()
                
                if stream:
                    import json
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
                    # Strip <think> blocks from reasoning models
                    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

                    if face_bridge: face_bridge.send_event("set_network", {"network": "CONNECTED"})
                    print(f"OPENROUTER OK ({model_id}) | {time.time() - t0:.1f}s", flush=True)
                    return text if text else None
            except requests.exceptions.RequestException as e:
                print(f"[ROUTER] OpenRouter failed (network): {e}", flush=True)
                return None
            except Exception as e:
                print(f"[ROUTER] OpenRouter failed ({type(e).__name__}): {e}", flush=True)
                return None

        def try_ollama():
            """Fallback to local Ollama. ALWAYS uses phi3."""
            if face_bridge: face_bridge.send_event("set_model", {"model": "LOCAL"})
            url = f"{_OLLAMA_URL}/api/generate"
            payload = {
                "model": OLLAMA_FALLBACK_MODEL,  # ISSUE 5 FIX: Always phi3
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
            except requests.exceptions.RequestException as e:
                if face_bridge: face_bridge.send_event("set_network", {"network": "ERROR"})
                print(f"[ROUTER ERROR] Ollama (network): {e}", flush=True)
                return None
            except Exception as e:
                if face_bridge: face_bridge.send_event("set_network", {"network": "ERROR"})
                print(f"[ROUTER ERROR] Ollama: {e}", flush=True)
                return None

        # --- ISSUE 4+6 FIX: Correct provider execution order per intent ---
        res = None

        if intent == "CODING":
            # CODING: OpenRouter(deepseek-chat) → Groq → Ollama(phi3)
            res = try_or(OR_CODING_MODEL)
            if not res:
                res = try_groq()
            if not res:
                res = try_ollama()

        elif intent in ("RESEARCH", "REASONING"):
            # RESEARCH/REASONING: OpenRouter(deepseek-r1) → Groq → Ollama(phi3)
            res = try_or(OR_REASONING_MODEL)
            if not res:
                res = try_groq()
            if not res:
                res = try_ollama()

        else:
            # GENERAL: Groq → OpenRouter(deepseek-chat) → Ollama(phi3)
            res = try_groq()
            if not res:
                res = try_or(OR_CODING_MODEL)
            if not res:
                res = try_ollama()

        return res if res else "Yes?"

    # Run the blocking HTTP calls in a worker thread
    future = _router_pool.submit(_do_route)
    try:
        return future.result(timeout=35)
    except TimeoutError:
        print("[ROUTER] Thread timeout: request took too long", flush=True)
        return "Yes?"
    except Exception as e:
        print(f"[ROUTER] Thread error: {e}", flush=True)
        return "Yes?"


def warmup_models():
    return True