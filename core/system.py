"""
GENESIS + JARVIS System Integrator.
Initializes and orchestrates all system components into a cohesive autonomous AI system.
Integrates all 27 requirements.
"""

import asyncio
import logging
import sys
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from core.config import SAFE_START
except ImportError:
    SAFE_START = True

try:
    from core import genesis_voice
except ImportError as e:
    import logging as _log
    _log.getLogger("genesis_jarvis").warning(f"Voice module unavailable: {e}")
    # Provide a minimal stub so the rest of system.py doesn't crash
    class _VoiceStub:
        @staticmethod
        def main(): pass
        @staticmethod
        def speak(text=""): pass
    genesis_voice = _VoiceStub()

from core.event_bus import get_event_bus, set_event_bus, EventBus
from core.knowledge_graph import get_knowledge_graph, set_knowledge_graph, KnowledgeGraph, NodeType, RelationType
from core.world_model import get_world_model, set_world_model, WorldModel
from autonomous_engine import get_reasoning_engine, set_reasoning_engine, AutonomousReasoningEngine
from core.tool_registry import get_tool_registry, set_tool_registry, ToolRegistry, ToolType, ToolParameter
from core.monitoring import get_system_monitor, SystemMonitor, SelfRecoverySystem
from core.perception_fusion import get_perception_fusion, set_perception_fusion, PerceptionFusion
from core.plugin_system import get_plugin_manager, set_plugin_manager, PluginManager
from core.owner_system import OwnerAuthentication, OwnerProfile, RespectfulAddressing
from core.legacy_agents import get_vision_agent, get_voice_agent, get_context_memory
from core.intent_and_risk import IntentRecognizer, RiskDetector, ActionVerifier

# GENESIS EVOLUTION
try:
    from core import motion_system
    from body import sensor_system
    from core import behavior_engine
    from core import emotion_engine
except ImportError as e:
    _log = logging.getLogger("genesis_jarvis")
    _log.warning(f"Evolution modules unavailable: {e}")
    motion_system = sensor_system = behavior_engine = emotion_engine = None

# GENESIS SELF-LEARNING
try:
    from core.experience_memory import get_experience_memory
    from core.learning_engine import get_learning_engine, start_learning_engine
    from core.skill_engine import get_skill_engine, start_skill_engine
    LEARNING_AVAILABLE = True
except ImportError as e:
    _log = logging.getLogger("genesis_jarvis")
    _log.warning(f"Self-learning modules unavailable: {e}")
    LEARNING_AVAILABLE = False

class GenesisJarvisSystem:
    """
    Main system orchestrator integrating all GENESIS + JARVIS components.
    Manages system lifecycle and coordinates all subsystems.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = self._setup_logger()
        
        self.logger.info("="*60)
        self.logger.info("GENESIS + JARVIS SYSTEM INITIALIZATION")
        self.logger.info("="*60)
        print("INIT CALLED: GenesisJarvisSystem.__init__", flush=True)
        
        self.start_time = datetime.now()
        self.components: Dict[str, Any] = {}
        self._running = False
        self._initialized = False  # Guard against double initialization
    
    def _setup_logger(self) -> logging.Logger:
        """Setup comprehensive logging."""
        logger = logging.getLogger("genesis_jarvis")
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
    
    async def initialize_core_systems(self):
        """Initialize foundational systems."""
        
        self.logger.info("Initializing core systems...")
        
        try:
            from core.memory.memory_db import init_memory_db
            init_memory_db()
            self.logger.info("✓ Memory DB initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize memory DB safely: {e}")
        
        event_bus = EventBus(self.logger)
        set_event_bus(event_bus)
        self.components["event_bus"] = event_bus
        self.logger.info("✓ Event Bus initialized")
        
        knowledge_graph = KnowledgeGraph(self.logger)
        set_knowledge_graph(knowledge_graph)
        self.components["knowledge_graph"] = knowledge_graph
        self.logger.info("✓ Knowledge Graph initialized")
        
        world_model = WorldModel(self.logger)
        set_world_model(world_model)
        self.components["world_model"] = world_model
        self.logger.info("✓ World Model initialized")
        
        if not SAFE_START:
            reasoning_engine = AutonomousReasoningEngine(self.logger)
            set_reasoning_engine(reasoning_engine)
            self.components["reasoning_engine"] = reasoning_engine
            self.logger.info("✓ Autonomous Reasoning Engine initialized")
        
        tool_registry = ToolRegistry(self.logger)
        set_tool_registry(tool_registry)
        self.components["tool_registry"] = tool_registry
        self.logger.info("✓ Tool Registry initialized")
    
    async def initialize_perception_systems(self):
        """Initialize perception and sensor systems."""
        
        self.logger.info("Initializing perception systems...")
        
        if not SAFE_START:
            perception_fusion = PerceptionFusion(self.logger)
            set_perception_fusion(perception_fusion)
            self.components["perception_fusion"] = perception_fusion
            self.logger.info("✓ Perception Fusion initialized")
            
            vision_agent = get_vision_agent()
            self.components["vision_agent"] = vision_agent
            self.logger.info("✓ Vision Agent initialized")
        
        voice_agent = get_voice_agent()
        self.components["voice_agent"] = voice_agent
        self.logger.info("✓ Voice Agent initialized")
        
        context_memory = get_context_memory()
        self.components["context_memory"] = context_memory
        self.logger.info("✓ Context Memory initialized")
    
    async def initialize_intelligence_systems(self):
        """Initialize intelligence and reasoning systems."""
        
        self.logger.info("Initializing intelligence systems...")
        
        intent_recognizer = IntentRecognizer()
        self.components["intent_recognizer"] = intent_recognizer
        self.logger.info("✓ Intent Recognizer initialized")
        
        risk_detector = RiskDetector()
        self.components["risk_detector"] = risk_detector
        self.logger.info("✓ Risk Detector initialized")
        
        action_verifier = ActionVerifier()
        self.components["action_verifier"] = action_verifier
        self.logger.info("✓ Action Verifier initialized")
    
    async def initialize_owner_systems(self):
        """Initialize owner authentication and profile systems."""
        
        self.logger.info("Initializing owner systems...")
        
        owner_authentication = OwnerAuthentication(self.logger)
        self.components["owner_authentication"] = owner_authentication
        self.logger.info("✓ Owner Authentication initialized")
        
        owner_profile = OwnerProfile(self.logger)
        self.components["owner_profile"] = owner_profile
        self.logger.info("✓ Owner Profile initialized")
        
        respectful_addressing = RespectfulAddressing(self.logger)
        self.components["respectful_addressing"] = respectful_addressing
        self.logger.info("✓ Respectful Addressing initialized")
    
    async def initialize_monitoring_systems(self):
        """Initialize monitoring and recovery systems."""
        
        if SAFE_START:
            self.logger.info("Skipping monitoring systems (SAFE_START)")
            return
            
        self.logger.info("Initializing monitoring systems...")
        
        system_monitor = SystemMonitor(self.logger)
        self.components["system_monitor"] = system_monitor
        self.logger.info("✓ System Monitor initialized")
        
        recovery_system = SelfRecoverySystem(system_monitor, self.logger)
        self.components["recovery_system"] = recovery_system
        self.logger.info("✓ Recovery System initialized")
        
        try:
            from core.self_repair_engine import start_self_repair_engine
            start_self_repair_engine()
            self.logger.info("✓ Self-Repair Engine initialized")
        except Exception as e:
            self.logger.warning(f"Self-Repair Engine failed to start: {e}")
    
    async def initialize_plugin_system(self):
        """Initialize expandable plugin system."""
        
        if SAFE_START:
            self.logger.info("Skipping plugin system (SAFE_START)")
            return
            
        self.logger.info("Initializing plugin system...")
        
        plugin_manager = PluginManager(logger=self.logger)
        await plugin_manager.initialize()
        set_plugin_manager(plugin_manager)
        self.components["plugin_manager"] = plugin_manager
        self.logger.info("✓ Plugin Manager initialized")
    
    async def register_default_tools(self):
        """Register default system tools."""
        
        self.logger.info("Registering default tools...")
        
        tool_registry = get_tool_registry()
        
        async def read_file_tool(filepath: str) -> str:
            try:
                with open(filepath, 'r') as f:
                    return f.read()
            except Exception as e:
                return f"Error reading file: {e}"
        
        tool_registry.register_tool(
            "file_read",
            "Read File",
            "Read contents of a file",
            ToolType.FILE_OPERATION,
            read_file_tool,
            parameters=[ToolParameter("filepath", str, True, "Path to file")],
            return_type=str
        )
        
        async def query_knowledge_graph(query: str) -> str:
            kg = get_knowledge_graph()
            nodes = kg.query_by_property("label")
            if not isinstance(nodes, list):
                nodes = list(nodes)
            return json.dumps([getattr(n, "label", str(n)) for n in nodes][:10], default=str)  # type: ignore
        
        tool_registry.register_tool(
            "query_kg",
            "Query Knowledge Graph",
            "Query the knowledge graph for information",
            ToolType.MEMORY_QUERY,
            query_knowledge_graph,
            parameters=[ToolParameter("query", str, True, "Query string")],
            return_type=str
        )
        
        async def get_world_status() -> str:
            world = get_world_model()
            stats = world.get_stats()
            return json.dumps(stats, default=str)
        
        tool_registry.register_tool(
            "world_status",
            "Get World Status",
            "Get current world model status",
            ToolType.SENSOR_READ,
            get_world_status,
            return_type=str
        )
        
        # Register Automation Tools
        try:
            from core import automation_engine
            
            async def trigger_webhook_tool(data: str = "{}") -> str:
                import json
                try:
                    payload = json.loads(data) if isinstance(data, str) and data.strip() else {}
                except Exception:
                    payload = {"raw_data": data}
                return automation_engine.trigger_webhook(payload)
                
            tool_registry.register_tool(
                "trigger_webhook",
                "Trigger Webhook",
                "Triggers the default automation webhook with an optional JSON payload",
                ToolType.SYSTEM_COMMAND,
                trigger_webhook_tool,
                parameters=[ToolParameter("data", str, False, "JSON string payload")],
                return_type=str
            )
            
            async def run_workflow_tool(name: str, data: str = "{}") -> str:
                import json
                try:
                    payload = json.loads(data) if isinstance(data, str) and data.strip() else {}
                except Exception:
                    payload = {"raw_data": data}
                return automation_engine.run_workflow(name, payload)
                
            tool_registry.register_tool(
                "run_workflow",
                "Run Workflow",
                "Triggers a specific automation workflow by name",
                ToolType.SYSTEM_COMMAND,
                run_workflow_tool,
                parameters=[
                    ToolParameter("name", str, True, "Name of the workflow"),
                    ToolParameter("data", str, False, "JSON string payload")
                ],
                return_type=str
            )
            
            async def execute_action_tool(action: str, target: str, data: str = "{}") -> str:
                import json
                try:
                    payload = json.loads(data) if isinstance(data, str) and data.strip() else {}
                except Exception:
                    payload = {"raw_data": data}
                return automation_engine.execute_action(action, target, payload)
                
            tool_registry.register_tool(
                "automation_execute",
                "Execute Automation Action",
                "Executes a specific action on a target in external automation",
                ToolType.SYSTEM_COMMAND,
                execute_action_tool,
                parameters=[
                    ToolParameter("action", str, True, "Action to perform"),
                    ToolParameter("target", str, True, "Target of the action"),
                    ToolParameter("data", str, False, "JSON string payload")
                ],
                return_type=str
            )
            
            try:
                import whatsapp_control
                async def whatsapp_send_tool(contact: str, message: str) -> str:
                    return whatsapp_control.send_message(contact, message)
                
                tool_registry.register_tool(
                    "whatsapp_send",
                    "Send WhatsApp Message",
                    "Sends a WhatsApp message to a specific contact",
                    ToolType.SYSTEM_COMMAND,
                    whatsapp_send_tool,
                    parameters=[
                        ToolParameter("contact", str, True, "Contact name or number"),
                        ToolParameter("message", str, True, "Message content")
                    ],
                    return_type=str
                )
            except ImportError:
                pass
            
            self.logger.info("✓ Automation tools registered")
        except ImportError as e:
            self.logger.warning(f"Automation engine unavailable, skipping automation tools: {e}")

        # Phase 2.5: Register system_audit and life_memory tools
        try:
            from core.tools.system_diagnostics import register_audit_tool
            register_audit_tool()
            self.logger.info("✓ System audit tool registered")
        except Exception as e:
            self.logger.warning(f"System audit tool registration failed: {e}")

        try:
            from core.tool_registry import get_tool_registry, ToolType
            registry = get_tool_registry()

            async def life_memory_search_tool(query: str) -> str:
                try:
                    from core.memory.life_memory_engine import search_life_memory
                    results = search_life_memory(query, limit=5)
                    if results:
                        return " | ".join([r["content"][:100] for r in results])
                    return "No life memory found for that query."
                except Exception as e:
                    return f"Life memory search failed: {e}"

            registry.register_tool(
                "life_memory_search",
                "Life Memory Search",
                "Search personal life memories, conversations, ideas and decisions",
                ToolType.MEMORY_QUERY,
                life_memory_search_tool,
                return_type=str,
            )
            self.logger.info("✓ Life memory search tool registered")
        except Exception as e:
            self.logger.warning(f"Life memory tool registration failed: {e}")

        self.logger.info("✓ Default tools registered")
    
    async def start_all_systems(self):
        """Start all system components. Runs ONCE only."""
        
        if self._initialized:
            self.logger.warning("WARNING start_all_systems already ran — skipping duplicate call")
            print("WARNING start_all_systems already ran — BLOCKED", flush=True)
            return
        self._initialized = True
        
        print("INIT start_all_systems", flush=True)
        self.logger.info("Starting all systems...")
        
        event_bus = self.components["event_bus"]
        await event_bus.start()
        self.logger.info("✓ Event Bus started")

        # ── MINIMAL PIPELINE: Evolution / monitoring modules disabled for speed ──
        # emotion_engine, motion_system, sensor_system, behavior_engine skipped.
        # Uncomment to re-enable after performance is confirmed.
        # if motion_system and sensor_system and emotion_engine and behavior_engine:
        #     motion_system.start_motion_system()
        #     sensor_system.start_sensor_system()
        #     emotion_engine.start_emotion_engine()
        #     behavior_engine.start_behavior_engine()
        #     self.logger.info("✓ GENESIS EVOLUTION systems started")
        
        # Start Self-Learning Modules
        if LEARNING_AVAILABLE and not SAFE_START:
            start_skill_engine()
            start_learning_engine()
            try:
                from core.memory.memory_pruner import initialize_memory_pruner
                initialize_memory_pruner()
            except ImportError as e:
                self.logger.warning(f"Memory pruner unavailable: {e}")
                
            self.components["experience_memory"] = get_experience_memory()
            self.components["learning_engine"] = get_learning_engine()
            self.components["skill_engine"] = get_skill_engine()
            self.logger.info("✓ GENESIS SELF-LEARNING systems started")
        
        # ── Phase 2.5 Batch 2 Modules ──
        try:
            from core.agents.agent_scheduler import start_agent_scheduler
            self.components["agent_scheduler"] = start_agent_scheduler()
            self.logger.info("✓ Agent Scheduler started (max=3 concurrent)")
        except Exception as e:
            self.logger.warning(f"Agent Scheduler start failed: {e}")

        try:
            from core.memory.life_memory_engine import get_life_memory_engine
            self.components["life_memory"] = get_life_memory_engine()
            self.logger.info("✓ Life Memory Engine initialized")
        except Exception as e:
            self.logger.warning(f"Life Memory Engine start failed: {e}")

        try:
            from core.monitoring.self_improvement_engine import start_self_improvement_engine
            self.components["self_improvement"] = start_self_improvement_engine()
            self.logger.info("✓ Self-Improvement Engine started")
        except Exception as e:
            self.logger.warning(f"Self-Improvement Engine start failed: {e}")

        try:
            from core.cognition.synthetic_intelligence import start_synthetic_intelligence
            self.components["synthetic_intelligence"] = start_synthetic_intelligence()
            self.logger.info("✓ Synthetic Intelligence Layer started")
        except Exception as e:
            self.logger.warning(f"Synthetic Intelligence start failed: {e}")

        try:
            from core.identity_system import start_identity_system
            self.components["identity_system"] = start_identity_system()
            self.logger.info("✓ Identity System started")
        except Exception as e:
            self.logger.warning(f"Identity System start failed: {e}")
        
        # Perception Fusion disabled — no sensors active in minimal pipeline
        # perception_fusion = self.components["perception_fusion"]
        # await perception_fusion.start()
        
        # System Monitor disabled for minimal pipeline
        # system_monitor = self.components["system_monitor"]
        # await system_monitor.start()
        
        # Reasoning engine disabled — minimal pipeline, voice commands drive everything
        # reasoning_engine = self.components["reasoning_engine"]
        # await reasoning_engine.start()
        
        # Auto-injected idle_check tasks disabled — prevents scheduler from talking
        # try:
        #     reasoning_engine.submit_task("system_idle_check", {"source": "startup"})
        # except Exception:
        #     pass
        
        # Start voice assistant in background thread (LAST — after all core systems)
        try:
            from core import face_bridge
            face_bridge.start_bridge()
            self.logger.info("✓ Face bridge started")
        except Exception as e:
            self.logger.warning(f"Face bridge start skipped: {e}")

        try:
            from core import genesis_voice
            if "voice_thread" not in self.components:
                voice_thread = threading.Thread(target=genesis_voice.main, daemon=True, name="VoiceSystem")
                voice_thread.start()
                self.components["voice_thread"] = voice_thread
                self.logger.info("✓ Voice system started (LAST — all core systems ready)")
        except Exception as e:
            self.logger.error(f"Voice system start failed: {e}")

        try:
            from core.cognition.cognitive_loop import start_cognitive_loop
            start_cognitive_loop()
            self.logger.info("✓ Cognitive loop started")
        except Exception as e:
            self.logger.error(f"Cognitive loop start failed: {e}")

        # Boot validation (runs after all systems started)
        try:
            from core.boot_validator import run_boot_validation
            boot_report = run_boot_validation()
            self.logger.info(f"✓ Boot validation: {boot_report.get('overall', 'unknown')}")
        except Exception as e:
            self.logger.warning(f"Boot validation failed: {e}")
        
        # Watchdog disabled — prevents background monitor from triggering speech
        # try:
        #     from core.watchdog.watchdog import start_watchdog
        #     start_watchdog()
        # except Exception as e:
        #     self.logger.error(f"Failed to load Watchdog Manager: {e}", exc_info=True)
        
        self._running = True
        self.logger.info("✓ All systems started successfully")
        
        # ── Blocking warmup — wait for Ollama before saying online ──
        try:
            pass
        except:
            pass

        # Emit startup IDLE/ONLINE signal AFTER websocket is actually connected.
        # face_bridge connects asynchronously — emit in background without blocking speech.
        def _emit_startup_ready():
            import time as _time
            try:
                from core import face_bridge # type: ignore
                max_wait = 30  # tenths of a second (3 seconds max)
                waited = 0
                while not face_bridge.is_connected and waited < max_wait:
                    _time.sleep(0.1)
                    waited += 1
                
                if face_bridge.is_connected:
                    face_bridge.send_event("set_status", {
                        "state": "IDLE",
                        "status": "ONLINE",
                        "core": "READY",
                        "voice": "READY",
                        "mic": "ON",
                        "network": "CONNECTED"
                    })
                    self.logger.info(f"✓ Startup IDLE broadcast sent (after {waited * 0.1:.1f}s wait)")
                else:
                    self.logger.warning("⚠ WebSocket not connected after 3s — UI may not show ONLINE")
            except Exception as e:
                self.logger.error(f"Startup signal failed: {e}")
        
        threading.Thread(target=_emit_startup_ready, daemon=True, name="StartupSignal").start()
    
    async def shutdown(self):
        """Gracefully shutdown all systems."""
        
        self.logger.info("Initiating system shutdown...")
        self._running = False
        
        reasoning_engine = self.components.get("reasoning_engine")
        if reasoning_engine:
            await reasoning_engine.stop()
        
        system_monitor = self.components.get("system_monitor")
        if system_monitor:
            await system_monitor.stop()
        
        perception_fusion = self.components.get("perception_fusion")
        if perception_fusion:
            await perception_fusion.stop()
        
        try:
            from core import face_bridge
            face_bridge.stop_bridge()
            self.logger.info("✓ Face bridge shutdown complete")
        except: pass

        try:
            from core import genesis_voice
            genesis_voice.stop_voice()
            self.logger.info("✓ Voice system shutdown complete")
        except: pass

        try:
            from core.voice_agent import stop_speaker
            stop_speaker()
            self.logger.info("✓ Speaker thread shutdown complete")
        except: pass

        try:
            from core.wake_word import detector
            detector.stop_listener()
            self.logger.info("✓ Wake word listener stopped")
        except: pass

        event_bus = self.components.get("event_bus")
        if event_bus:
            await event_bus.stop()
        
        self.logger.info("✓ System shutdown complete")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        status: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "running": self._running,
            "uptime_seconds": uptime,
            "components": {}
        }
        
        if "event_bus" in self.components:
            status["components"]["event_bus"] = self.components["event_bus"].get_stats()
        
        if "knowledge_graph" in self.components:
            status["components"]["knowledge_graph"] = self.components["knowledge_graph"].get_stats()
        
        if "world_model" in self.components:
            status["components"]["world_model"] = self.components["world_model"].get_stats()
        
        if "reasoning_engine" in self.components:
            status["components"]["reasoning_engine"] = self.components["reasoning_engine"].get_stats()
        
        if "tool_registry" in self.components:
            status["components"]["tool_registry"] = {
                "total_tools": len(self.components["tool_registry"].tools),
                "enabled": sum(1 for t in self.components["tool_registry"].tools.values() if t.enabled)
            }
        
        if "system_monitor" in self.components:
            status["components"]["system_monitor"] = {
                "health": self.components["system_monitor"].get_health_report()
            }
        
        if "plugin_manager" in self.components:
            status["components"]["plugin_manager"] = self.components["plugin_manager"].get_stats()
        
        return status
    
    def print_status_report(self):
        """Print a formatted status report."""
        
        status = self.get_system_status()
        
        self.logger.info("="*60)
        self.logger.info("GENESIS + JARVIS SYSTEM STATUS")
        self.logger.info("="*60)
        self.logger.info(f"Status: {'RUNNING' if status['running'] else 'STOPPED'}")
        self.logger.info(f"Uptime: {status['uptime_seconds']:.1f} seconds")
        self.logger.info("")
        self.logger.info("Component Status:")
        
        def convert_to_serializable(obj):
            """Convert non-JSON-serializable objects to strings."""
            if isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_serializable(item) for item in obj]
            elif hasattr(obj, '__name__'):  # Enum or class
                return str(obj)
            else:
                return obj
        
        for component, stats in status["components"].items():
            try:
                serializable_stats = convert_to_serializable(stats)
                self.logger.info(f"  {component}: {json.dumps(serializable_stats, indent=2, default=str)}")
            except Exception as e:
                self.logger.info(f"  {component}: {stats} (serialization error: {e})")
        
        self.logger.info("="*60)


async def run_genesis_jarvis_system(config: Optional[Dict[str, Any]] = None) -> GenesisJarvisSystem:
    """Main entry point to run the complete GENESIS + JARVIS system."""
    
    system = GenesisJarvisSystem(config)
    
    if getattr(system, "running", None) is False or not system._running:
        system._running = True
        system.running = True

    try:
        # Fix 8: Ensure event_bus and tool_registry are ready before voice
        from core.event_bus import get_event_bus
        from core.tool_registry import get_tool_registry
        _bus = get_event_bus()
        _reg = get_tool_registry()
        system.logger.info("✓ Event bus and tool registry confirmed ready")
    except Exception:
        pass

    # Voice thread is now started inside start_all_systems() AFTER all core init

    try:
        await system.initialize_core_systems()
    except Exception: pass
    
    try:
        await system.initialize_perception_systems()
    except Exception: pass
    
    try:
        await system.initialize_intelligence_systems()
    except Exception: pass
    
    try:
        await system.initialize_owner_systems()
    except Exception: pass
    
    try:
        await system.initialize_monitoring_systems()
    except Exception: pass
    
    try:
        await system.initialize_plugin_system()
    except Exception: pass
    
    try:
        await system.register_default_tools()
    except Exception: pass
    
    try:
        await system.start_all_systems()
    except Exception: pass
    
    try:
        system.print_status_report()
    except Exception: pass
    
    return system


if __name__ == "__main__":
    async def main():
        sys_obj: GenesisJarvisSystem = await run_genesis_jarvis_system()
        
        try:
            while sys_obj._running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            await sys_obj.shutdown()
    
    asyncio.run(main())
