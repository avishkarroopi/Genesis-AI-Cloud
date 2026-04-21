import os
import threading
import time
import json
import re
import datetime
import ast

# Fallback for LangChain components to ensure system runs even if dependencies are slow
try:
    from langchain.memory import ConversationBufferMemory  # type: ignore
    from langchain_core.messages import HumanMessage, AIMessage  # type: ignore
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    class HumanMessage:
        def __init__(self, content): self.content = content
    class AIMessage:
        def __init__(self, content): self.content = content

from core.ai_router import route_ai_request  # type: ignore
from core.config import *  # type: ignore

try:
    from body import screen_control  # type: ignore
except ImportError:
    screen_control = None  # Not available in cloud mode

try:
    from core import automation_engine  # type: ignore
except ImportError:
    automation_engine = None

try:
    from body import robot_control  # type: ignore
except ImportError:
    robot_control = None  # Not available in cloud / server mode

from core import genesis_tools
from core.memory.memory_manager import get_user_name, set_user_name, store_entity, get_entities, load_memory, get_all_memory, get_memory_key, set_memory_key
from core import prompt_config
from core.memory.memory_search import search_memory_safe
from core import context_manager

try:
    from core import automation_bridge  # type: ignore
except ImportError:
    automation_bridge = None

try:
    from core.owner_system import OwnerProfile
except ImportError:
    class OwnerProfile:
        def get_full_profile(self): return {}

try:
    from core import face_bridge  # type: ignore
except ImportError:
    face_bridge = None

# --- Phase-3.5 Personality System ---
def generate_startup_greeting():
    import datetime
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning, sir. How are you doing today?"
    elif 12 <= hour < 17:
        return "Good afternoon, sir. How are you doing today?"
    elif 17 <= hour < 21:
        return "Good evening, sir. How are you doing today?"
    else:
        return "Good evening, sir. How are you doing tonight?"

def generate_farewell_message():
    import datetime
    hour = datetime.datetime.now().hour
    if 5 <= hour < 17:
        return "Alright, boss. Take care. Have a great day ahead."
    elif 17 <= hour < 21:
        return "Alright, boss. Take care. Have a pleasant evening."
    else:
        return "Alright, boss. Take care. Good night."

try:
    import core.genesis_voice as _gv
    _orig_speak = _gv.speak
    def _patched_speak(text):
        if text.strip() == "Genesis online.":
            text = f"Genesis voice ready. Genesis online. {generate_startup_greeting()}"
        _orig_speak(text)
    _gv.speak = _patched_speak

    _orig_is_stop_command = _gv.is_stop_command
    def _patched_is_stop_command(text):
        is_stop = _orig_is_stop_command(text)
        if is_stop:
            _gv.speak(generate_farewell_message())
        return is_stop
    _gv.is_stop_command = _patched_is_stop_command
except Exception as e:
    print(f"[BRAIN] Warning: Could not bind Phase 3.5 personality layer: {e}")

# Custom Memory class to handle cases where LangChain is missing
class SimpleMemory:
    MAX_MESSAGES = 50  # Hard cap to prevent unbounded memory growth

    def __init__(self):
        self.messages = []
    
    def add_user_message(self, message):
        self.messages.append(HumanMessage(message))
        if len(self.messages) > self.MAX_MESSAGES:
            self.messages = self.messages[-self.MAX_MESSAGES:]
        
    def add_ai_message(self, message):
        self.messages.append(AIMessage(message))
        if len(self.messages) > self.MAX_MESSAGES:
            self.messages = self.messages[-self.MAX_MESSAGES:]
        
    def get_messages(self, limit=6):
        return self.messages[-limit:]

# Initialize memory (Global removed for cloud multi-tenancy)
# memory = SimpleMemory()  # REMOVED

# --- Phase-2: Vision detection cache for brain context ---
# _last_vision_objects = [] # REMOVED

def _on_vision_detected(event):
    """Handle VISION_DETECTED events and update world model."""
    try:
        data = event.data if hasattr(event, 'data') else event
        objects = data.get("objects", []) if isinstance(data, dict) else []
        # Update world model with detected objects
        try:
            from core.world_model import get_world_model, ObjectCategory, Position
            wm = get_world_model()
            import asyncio
            for label in objects[:5]:
                obj_id = f"vision_{label}_{int(time.time())}"
                try:
                    loop = asyncio.get_event_loop()
                    asyncio.run_coroutine_threadsafe(
                        wm.add_object(obj_id, ObjectCategory.OBJECT, label, Position(0, 0, 0)),
                        loop
                    )
                except Exception:
                    pass
        except Exception:
            pass
    except Exception:
        pass

class GenesisBrain:
    def __init__(self):
        # System prompt lives in prompt_config.py — single source of truth.
        # Do NOT define a duplicate here.
        self.owner_profile = OwnerProfile()

    def _execute_tool(self, tool_tag):
        try:
            from core.tool_registry import get_tool_registry
            import asyncio

            # --- Security check before tool execution ---
            try:
                from security.safe_mode import is_safe_mode_enabled
                from security.permissions import check_permission
                if is_safe_mode_enabled() and not check_permission("allow_shell"):
                    print("[BRAIN] Tool blocked by security policy", flush=True)
                    try:
                        from core.security.security_logger import log_permission_denied
                        log_permission_denied(tool_tag, "safe_mode + no allow_shell")
                    except Exception:
                        pass
                    return "Tool execution blocked by security policy."
            except ImportError:
                pass

            registry = get_tool_registry()

            try:
                import json
                tool_data = json.loads(tool_tag.strip())
                func_name = tool_data.get("tool", "")
                kwargs = tool_data.get("args", {})
                args = list(kwargs.values())
            except Exception as e:
                print(f"[BRAIN] Tool JSON parse failed: {e}", flush=True)
                return "Tool parsing failed."

            # --- Phase-3: Validate through sandbox before execution ---
            try:
                from core.security.tool_sandbox import validate_command
                for arg in args:
                    if isinstance(arg, str) and not validate_command(arg):
                        print(f"[BRAIN] Tool arg blocked by sandbox: {arg}", flush=True)
                        return "Command blocked by security sandbox."
            except Exception:
                pass

            print(f"[BRAIN] Routing Tool: {func_name}", flush=True)

            # --- Phase-3: Log the tool execution ---
            try:
                from core.security.security_logger import log_tool_execution
                log_tool_execution(func_name, args)
            except Exception:
                pass

            async def run_tool():
                return await registry.execute_tool(func_name, **kwargs)

            try:
                loop = asyncio.get_running_loop()
                future = asyncio.run_coroutine_threadsafe(run_tool(), loop)
                try:
                    return future.result(timeout=10)
                except Exception:
                    return "Tool execution completed."
            except RuntimeError:
                # No running loop — create an isolated one safely
                _tool_loop = asyncio.new_event_loop()
                try:
                    return _tool_loop.run_until_complete(run_tool())
                finally:
                    _tool_loop.close()

        except Exception as e:
            print(f"[BRAIN] Tool error: {e}", flush=True)

        return "Tool execution completed."

    def process_voice_input_async(self, session_context, command, owner_address="Sir", callback=None):
        """
        Process the incoming voice command. SYNCHRONOUS, fast layout.
        Called asynchronously from name but executes synchronously logic.
        """
        import redis
        import json
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        try:
            r_client = redis.from_url(redis_url, decode_responses=True)
        except Exception:
            r_client = None

        if isinstance(session_context, dict):
            user_id = session_context.get("user_id", "default")
        else:
            user_id = getattr(session_context, "user_id", "default")

        mem_key = f"genesis:memory:{user_id}"
        vis_key = f"genesis:perception:{user_id}"

        # Load SimpleMemory from Redis
        memory = SimpleMemory()
        if r_client:
            raw_mem = r_client.get(mem_key)
            if raw_mem:
                try:
                    loaded = json.loads(raw_mem)
                    for item in loaded:
                        if item.get("role") == "user":
                            memory.add_user_message(item.get("content", ""))
                        else:
                            memory.add_ai_message(item.get("content", ""))
                except Exception:
                    pass
        
        # Load vision objects from Redis
        _last_vision_objects = []
        if r_client:
            raw_vis = r_client.get(vis_key)
            if raw_vis:
                try:
                    vis_data = json.loads(raw_vis)
                    _last_vision_objects = vis_data.get("objects", [])
                except Exception:
                    pass

        # --- FIX 3: EXPLICIT BUFFER CLEAR ---
        response_text = ""
        sentence_buffer = ""
        stream_accumulator = ""
        stream_generator = None
        
        t_brain_start = time.time()
        print(f"BRAIN TRACE: command received (user={user_id})", flush=True)
        # brain processing start
        try:
            # Signal THINKING
            try:
                if face_bridge:
                    face_bridge.send_event("set_state", {"state": "THINKING"})
            except Exception:
                pass

            context_lines = []
            for msg in memory.get_messages(4):
                role = "User" if isinstance(msg, HumanMessage) else "Genesis"  # type: ignore
                context_lines.append(f"{role}: {msg.content}")
            context_str = "\n".join(context_lines)

            try:
                # Store user input in memory AFTER building context
                memory.add_user_message(command)
            except Exception as e:
                print(f"[BRAIN] Memory store failed: {e}", flush=True)

            now = datetime.datetime.now()
            time_str = now.strftime("%I:%M %p")

            # Fix 3 & 10: Capability Filter
            cmd_lower = command.lower()
            
            # --- PHASE 0 DETERMINISTIC INTERCEPTOR ---
            if "who created you" in cmd_lower or "who made you" in cmd_lower:
                response_text = "I was created by my owner."
                memory.add_ai_message(response_text)
                if callback: callback(response_text)
                return
            elif "who is your owner" in cmd_lower:
                response_text = "You are my owner, sir."
                memory.add_ai_message(response_text)
                if callback: callback(response_text)
                return
            elif "what systems are active" in cmd_lower:
                try:
                    from core.system.capability_registry import get_capabilities
                    caps = get_capabilities()
                    active = [k.replace("_", " ") for k, v in caps.items() if v]
                    response_text = f"The following systems are active: {', '.join(active)}."
                except Exception as e:
                    response_text = "System registry unavailable."
                memory.add_ai_message(response_text)
                if callback: callback(response_text)
                return
            elif "genesis status" in cmd_lower:
                try:
                    from core.system.capability_registry import get_capabilities
                    caps = get_capabilities()
                    active = len([v for v in caps.values() if v])
                    total = len(caps)
                    response_text = f"Genesis is online and fully operational. {active} out of {total} systems are active."
                except Exception:
                    response_text = "Genesis is online and functional."
                memory.add_ai_message(response_text)
                if callback: callback(response_text)
                return
            
            # --- STRUCTURED MEMORY ENTITY STORE ---
            store_match = re.search(r"^store this\s+([a-zA-Z]+)\s+([a-zA-Z0-9_]+)\s+(.+)$", cmd_lower)
            if store_match:
                e_name = store_match.group(1).capitalize()
                e_key = store_match.group(2)
                e_val = store_match.group(3)
                try:
                    store_entity(e_name, e_key, e_val)
                    response_text = f"Stored {e_key} for {e_name}."
                    memory.add_ai_message(response_text)
                    if callback:
                        callback(response_text)
                    return
                except Exception as e:
                    print(f"[MEMORY] Store Error: {e}", flush=True)

            try:
                from core.ai_router import analyze_routing
                router = analyze_routing(command)
                print("BRAIN TRACE: intent detected", flush=True)
            except Exception as e:
                print(f"[BRAIN] Router classification failed: {e}. Falling back.", flush=True)
                class FallbackRouter:
                    use_planner = False
                    use_tools = False
                router = FallbackRouter()

            # --- Phase-2: World Model + Vision awareness (replaces old hardcoded block) ---
            _WORLD_QUERIES = ["see", "look", "camera", "vision", "what objects",
                              "where am i", "environment", "around me", "what do you see"]
            if any(w in cmd_lower for w in _WORLD_QUERIES):
                try:
                    from core.world_model import get_world_model
                    wm = get_world_model()
                    env_state = wm.get_current_state()
                    has_data = "No environment data" not in env_state
                    # Also include any recent vision detections
                    if _last_vision_objects:
                        env_state += "\nRecently detected: " + ", ".join(_last_vision_objects[:5])
                    if has_data or bool(_last_vision_objects):
                        response_text = f"Here is what I can observe:\n{env_state}"
                    else:
                        response_text = "I don't have any active environment data at the moment. Vision and sensors are not currently active."
                except Exception as e:
                    print(f"[BRAIN] World model query failed: {e}", flush=True)
                    response_text = "I don't have active environment data right now."
                memory.add_ai_message(response_text)
                if callback:
                    callback(response_text)
                return
            
            if not response_text:
                from core.agent_registry import delegate_agent_task
                
                try:
                    if router.intent == "RESEARCH":
                        print("[BRAIN] Delegating to Research Agent", flush=True)
                        response_text = delegate_agent_task("research", command)
                    elif router.intent == "AUTOMATION":
                        print("[BRAIN] Delegating to Tool Agent", flush=True)
                        response_text = delegate_agent_task("tools", command)
                    elif router.intent in ["REASONING", "PLANNING"] or getattr(router, 'use_planner', False):
                        print("[BRAIN] Delegating to Planner Agent", flush=True)
                        response_text = delegate_agent_task("planner", command)
                except Exception as e:
                    print(f"[BRAIN] Agent delegation failed: {e}. Falling back.", flush=True)

            if not response_text:
                user_name = get_user_name()
                # ---- MEMORY + OWNER CONTEXT ----
                try:
                    mem = get_all_memory()
                    mem_lines = []
                    for k, v in mem.items():
                        if k == "entities" and isinstance(v, dict):
                            for e_name, e_data in v.items():
                                for e_k, e_v in e_data.items():
                                    mem_lines.append(f"Entity [{e_name}] {e_k}: {e_v}")
                        else:
                            mem_lines.append(f"{k}: {v}")
                    mem_context = "\n".join(mem_lines)
                except Exception:
                    mem_context = ""

                try:
                    from core.memory.memory_search import search_vector_memory
                    vector_memories = search_vector_memory(command)
                    if not isinstance(vector_memories, list):
                        vector_memories = []
                except Exception:
                    vector_memories = []

                try:
                    enhanced_context = context_manager.build_context(
                        command, 
                        mem_context, 
                        vector_memories, 
                        context_str
                    )
                except Exception as e:
                    print(f"[BRAIN] Context Manager failed: {e}", flush=True)
                    enhanced_context = f"Known memory:\n{mem_context}\n\nVector memory:\n{vector_memories}\n\nRules: Use this."

                # --- Phase-2: Inject world model context if available ---
                try:
                    from core.world_model import get_world_model
                    wm = get_world_model()
                    world_ctx = wm.get_current_state()
                    if world_ctx and "No environment data" not in world_ctx:
                        enhanced_context += f"\n\nEnvironment State:\n{world_ctx}"
                except Exception:
                    pass

                full_prompt = prompt_config.get_full_prompt(
                    command,
                    time_str,
                    user_name,
                    enhanced_context
                )

                # --- Phase-1: Tool Reasoning Injection ---
                try:
                    tool_awareness = (
                        "\n\nAvailable Tools:\n"
                        "- time_tool: get current time\n"
                        "- date_tool: get current date\n"
                        "- browser_tool: open browser or search the web\n"
                        "- shell_tool: run shell commands\n"
                        "- file_tool: file operations\n"
                        "- remember_tool: store information to memory\n"
                        "\nIf a tool is needed, respond with exactly this JSON block:\n"
                        "[TOOL_CALL]{\"tool\": \"tool_name\", \"args\": {\"arg1\": \"value\"}}[/TOOL_CALL]\n"
                        "If no tool is needed, respond naturally without any tool tags.\n"
                    )
                    full_prompt = full_prompt + tool_awareness
                except Exception:
                    pass

                try:
                    if face_bridge:
                        face_bridge.send_event("set_state", {"state": "PROCESSING"})
                except Exception:
                    pass

                t_router = time.time()

                # --- PHASE 1 STREAMING HELPER ---
                class SentenceBuffer:
                    def __init__(self):
                        from core.voice_agent import speak
                        self.buffer = ""
                        self.speak_fn = speak
                        self.sentence_regex = re.compile(r'([.?!]+)(\s+|$)')
                        self.in_tool = False
                        self.spoken_any = False

                    def on_token(self, token):
                        self.buffer += token
                        if '[TOOL_CALL]' in self.buffer:
                            self.in_tool = True
                        if '[/TOOL_CALL]' in self.buffer:
                            self.in_tool = False
                        
                        if not self.in_tool and '[' not in self.buffer:
                            match = self.sentence_regex.search(self.buffer)
                            if match:
                                end_pos = match.end()
                                sentence = self.buffer[:end_pos].strip()
                                if sentence:
                                    if not getattr(self, '_emotion_checked', False):
                                        try:
                                            from core.emotion_engine import analyze_text_emotion
                                            analyze_text_emotion(sentence)
                                        except Exception:
                                            pass
                                        self._emotion_checked = True
                                    self.speak_fn(sentence)
                                    self.spoken_any = True
                                self.buffer = self.buffer[end_pos:]
                    
                    def flush(self):
                        if not self.in_tool and self.buffer.strip() and '[' not in self.buffer:
                            self.speak_fn(self.buffer.strip())
                            self.spoken_any = True
                        self.buffer = ""
                
                s_buf = SentenceBuffer()
                
                # Call route request with streaming enabled
                response_text = route_ai_request(
                    full_prompt, 
                    owner_address, 
                    user_command=command, 
                    stream=True, 
                    stream_callback=s_buf.on_token
                )
                
                s_buf.flush()
                _already_streamed = getattr(s_buf, 'spoken_any', False)
                t_done = time.time()
                # model done

            if not response_text or not response_text.strip():
                print("MODEL SILENT — no response", flush=True)
                response_text = "Yes?"
            
            # Strip role labels if model echoes them
            response_text = re.sub(r'^(User|Genesis|Conversation)[^:]*:\s*', '', response_text, flags=re.IGNORECASE).strip()
            
            # Response trimming removed — planner and agent output must remain intact

            # Execute explicit tool tags if present
            if "[TOOL_CALL]" in response_text:
                tool_tags = re.findall(r"\[TOOL_CALL\](.*?)\[/TOOL_CALL\]", response_text, re.DOTALL)
                tool_results = []
                for tag in tool_tags:
                    result = self._execute_tool(tag)
                    if result and result != "Tool execution completed.":
                        tool_results.append(str(result))
                    response_text = response_text.replace(f"[TOOL_CALL]{tag}[/TOOL_CALL]", "").strip()
                # Reinsert tool results into the response
                if tool_results:
                    response_text = (response_text + "\n" + "\n".join(tool_results)).strip()
                    if '_already_streamed' in locals() and _already_streamed:
                        from core.voice_agent import speak
                        speak("\n".join(tool_results))
                if not response_text:
                    response_text = "Yes?"

            memory.add_ai_message(response_text)
            if len(memory.messages) > 4:
                memory.messages = memory.messages[-4:]

            # Save memory to Redis
            if r_client:
                save_payload = []
                for msg in memory.messages:
                    # Just check via class name string to avoid import issues
                    role = "user" if "human" in str(type(msg)).lower() else "ai"
                    save_payload.append({"role": role, "content": getattr(msg, 'content', str(msg))})
                try:
                    r_client.set(mem_key, json.dumps(save_payload))
                except Exception as e:
                    print(f"Failed saving redis mem: {e}", flush=True)

            # --- PART 3: CHROMADB MEMORY WRITE-BACK ---
            try:
                _STORE_TRIGGERS = ["remember that", "my name is", "this is my friend",
                                   "note that", "save this", "store this"]
                if any(trigger in cmd_lower for trigger in _STORE_TRIGGERS):
                    fact = command  # store the full original command as the fact
                    from core.memory.memory_store import add_memory_safe
                    add_memory_safe(fact, metadata={"type": "user_stored", "source": "voice"})
                    print(f"[BRAIN] Memory write-back: stored to ChromaDB", flush=True)
            except Exception as e:
                print(f"[BRAIN] Memory write-back failed (non-fatal): {e}", flush=True)

        except Exception as e:
            print(f"[BRAIN] ERROR | {e}", flush=True)
            response_text = "Yes?"
            _already_streamed = False
            
        try:
            from core.learning_engine import record_experience
            record_experience(command, response_text)
        except Exception as e:
            print(f"[BRAIN] Learning fallback failed: {e}", flush=True)
            
        if not getattr(s_buf, '_emotion_checked', False) if 's_buf' in locals() else True:
            try:
                from core.emotion_engine import analyze_text_emotion
                analyze_text_emotion(response_text)
            except Exception:
                pass
        
        # Ensure callback is definitively executed
        try:
            if callback:
                if '_already_streamed' in locals() and _already_streamed:
                    callback("#STREAMED#")
                else:
                    callback(response_text)
            else:
                try:
                    if face_bridge:
                        face_bridge.send_event("set_state", {"state": "IDLE"})
                except Exception:
                    pass
        except Exception as e:
            print(f"[BRAIN] CALLBACK ERROR | {e}", flush=True)
            if callback: 
                try:
                    callback("Yes?")
                except Exception as e:
                    print(f"[BRAIN] Callback fallback error: {e}", flush=True)

brain = GenesisBrain()


# --- LITE → CORE COMMAND HANDLER ---
def handle_lite_command(event):
    """Handle commands received from Lite client via Event Bus."""
    import asyncio
    command_text = event.data.get("text", "").strip()
    ws = event.data.get("ws")
    if not command_text:
        return

    # Issue 6: Respect processing lock to prevent concurrent voice+UI corruption
    try:
        from core.genesis_voice import acquire_processing, release_processing
    except ImportError:
        acquire_processing = None
        release_processing = None

    def _response_callback(response_text):
        if not ws:
            return
        try:
            from core.face_server import send_response_to_client
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(
                send_response_to_client(ws, "response", response_text), loop
            )
        except Exception as e:
            print(f"[BRAIN] Lite response send failed: {e}", flush=True)
            try:
                asyncio.run_coroutine_threadsafe(
                    send_response_to_client(ws, "error", "Command execution failed"), loop
                )
            except Exception:
                pass

    def _lite_pipeline():
        acquired = False
        try:
            if acquire_processing is not None:
                acquired = acquire_processing()
                if not acquired:
                    print("[BRAIN] Lite command blocked — voice pipeline busy", flush=True)
                    _response_callback("I'm currently processing another command. Please wait.")
                    return
            brain.process_voice_input_async(command_text, "Sir", _response_callback)
        except Exception as e:
            print(f"[BRAIN] Lite pipeline error: {e}", flush=True)
            _response_callback("Yes?")
        finally:
            if acquired and release_processing is not None:
                release_processing()

    threading.Thread(
        target=_lite_pipeline,
        daemon=True
    ).start()


# Register Lite command subscriber on Event Bus
try:
    from core.event_bus import get_event_bus
    _bus = get_event_bus()
    _bus.subscribe("COMMAND_RECEIVED", handle_lite_command)
    print("[BRAIN] Subscribed to COMMAND_RECEIVED (Lite → Core)", flush=True)
    # --- Phase-2: Subscribe to vision events ---
    try:
        _bus.subscribe("VISION_DETECTED", _on_vision_detected)
        print("[BRAIN] Subscribed to VISION_DETECTED", flush=True)
    except Exception:
        pass
except Exception as e:
    print(f"[BRAIN] Failed to subscribe to COMMAND_RECEIVED: {e}", flush=True)

# --- Phase-2: Start Cognitive Loop daemon ---
try:
    from core.cognition.cognitive_loop import start_cognitive_loop
    start_cognitive_loop()
    print("[BRAIN] Cognitive loop daemon started", flush=True)
except Exception as e:
    print(f"[BRAIN] Cognitive loop start failed (non-fatal): {e}", flush=True)

# --- Phase-3: Start Awareness Engine daemon ---
# The Awareness Engine monitors GoalQueue + WorldModel and emits proactive
# GOAL_TRIGGERED events on the Event Bus, closing the cognition feedback loop.
try:
    from core.awareness.awareness_loop import start_awareness_loop
    start_awareness_loop()
    print("[BRAIN] Awareness Engine started", flush=True)
except Exception as e:
    print(f"[BRAIN] Awareness loop start failed (non-fatal): {e}", flush=True)

# --- Phase-4: Start Self-Improvement daemon ---
# Monitors Intelligence Bus for reasoning traces to orchestrate learning loops
try:
    from core.self_improvement.self_improvement_engine import start_self_improvement_daemon
    start_self_improvement_daemon()
    print("[BRAIN] Self-Improvement Engine started", flush=True)
except Exception as e:
    print(f"[BRAIN] Self-Improvement daemon start failed (non-fatal): {e}", flush=True)

print("REALTIME MODE ACTIVE", flush=True)
print("VOICE FIXED", flush=True)
print("IDENTITY FIXED", flush=True)
print("MEMORY FIXED", flush=True)

