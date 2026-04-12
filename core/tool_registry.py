"""
Tool Registry for GENESIS + JARVIS.
Allows brain to dynamically select and use tools.
Requirement 13: Tool Usage by AI.
"""

import asyncio
import logging
import threading
from typing import Dict, List, Any, Callable, Optional, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class ToolType(Enum):
    FILE_OPERATION = "file_operation"
    VISION_QUERY = "vision_query"
    MEMORY_QUERY = "memory_query"
    WEB_SEARCH = "web_search"
    COMPUTATION = "computation"
    SENSOR_READ = "sensor_read"
    ACTUATOR_CONTROL = "actuator_control"
    SYSTEM_COMMAND = "system_command"


@dataclass
class ToolParameter:
    """Parameter specification for a tool."""
    name: str
    param_type: Type
    required: bool = True
    description: str = ""
    default: Any = None


@dataclass
class Tool:
    """Represents a tool available to the AI."""
    tool_id: str
    name: str
    description: str
    tool_type: ToolType
    callable: Callable
    parameters: List[ToolParameter] = field(default_factory=list)
    return_type: Type = str
    timeout: float = 10.0
    enabled: bool = True
    usage_count: int = 0
    last_used: Optional[datetime] = None
    success_rate: float = 1.0
    registered_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters."""
        try:
            if asyncio.iscoroutinefunction(self.callable):
                result = await asyncio.wait_for(
                    self.callable(**kwargs),
                    timeout=self.timeout
                )
            else:
                result = self.callable(**kwargs)
            
            self.usage_count += 1
            self.last_used = datetime.now()
            return result
        
        except asyncio.TimeoutError:
            raise TimeoutError(f"Tool {self.tool_id} execution timeout")
        except Exception as e:
            raise Exception(f"Tool {self.tool_id} execution failed: {e}")
    
    def to_dict(self) -> Dict:
        """Convert tool to dictionary for LLM context."""
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "type": self.tool_type.value,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.param_type.__name__,
                    "required": p.required,
                    "description": p.description
                }
                for p in self.parameters
            ],
            "return_type": self.return_type.__name__,
            "enabled": self.enabled
        }


class ToolRegistry:
    """
    Registry for all available tools.
    Manages tool discovery, execution, and monitoring.
    """
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.tools: Dict[str, Tool] = {}
        self.tool_categories: Dict[str, List[str]] = {}
        self._execution_history: List[Dict[str, Any]] = []
        self._max_history = 50
    
    def register_tool(
        self,
        tool_id: str,
        name: str,
        description: str,
        tool_type: ToolType,
        callable_func: Callable,
        parameters: List[ToolParameter] = None,
        return_type: Type = str,
        timeout: float = 10.0,
        metadata: Dict = None
    ) -> Tool:
        """Register a new tool."""
        
        tool = Tool(
            tool_id=tool_id,
            name=name,
            description=description,
            tool_type=tool_type,
            callable=callable_func,
            parameters=parameters or [],
            return_type=return_type,
            timeout=timeout,
            metadata=metadata or {}
        )
        
        self.tools[tool_id] = tool
        
        if tool_type.value not in self.tool_categories:
            self.tool_categories[tool_type.value] = []
        self.tool_categories[tool_type.value].append(tool_id)
        
        self.logger.info(f"Tool registered: {tool_id} ({tool_type.value})")
        return tool
    
    def get_tool(self, tool_id: str) -> Optional[Tool]:
        """Get a tool by ID."""
        return self.tools.get(tool_id)
    
    def get_tools_by_type(self, tool_type: ToolType) -> List[Tool]:
        """Get all tools of a specific type."""
        tool_ids = self.tool_categories.get(tool_type.value, [])
        return [self.tools[tid] for tid in tool_ids if tid in self.tools]
    
    def list_available_tools(self, enabled_only: bool = True) -> List[Dict]:
        """List available tools for LLM context."""
        tools = [t for t in self.tools.values()]
        
        if enabled_only:
            tools = [t for t in tools if t.enabled]
        
        return [t.to_dict() for t in tools]
    
    async def execute_tool(self, tool_id: str, **kwargs) -> Any:
        """Execute a tool with security validation."""
        tool = self.get_tool(tool_id)
        if not tool:
            raise ValueError(f"Tool {tool_id} not found")
        
        if not tool.enabled:
            raise ValueError(f"Tool {tool_id} is disabled")

        # --- Security checks (merged from tool_manager.py) ---
        try:
            import security.permissions as sec_perms
            import security.safe_mode as safe_mode

            # Permission mapping by tool type
            perm_map = {
                ToolType.SYSTEM_COMMAND: "allow_shell",
                ToolType.FILE_OPERATION: "allow_file",
                ToolType.WEB_SEARCH: "allow_browser",
            }

            required_perm = perm_map.get(tool.tool_type)
            if required_perm and not sec_perms.check_permission(required_perm):
                raise PermissionError(f"Tool {tool_id} blocked: '{required_perm}' permission denied")

            # Safe-mode command validation for shell-type tools
            if tool.tool_type == ToolType.SYSTEM_COMMAND:
                cmd_arg = kwargs.get("cmd", kwargs.get("command", ""))
                if cmd_arg and not safe_mode.validate_shell_command(str(cmd_arg)):
                    raise PermissionError(f"Safe Mode blocked dangerous command: {cmd_arg}")
        except ImportError:
            pass  # Security modules not available — allow execution
        # --- End security checks ---
        
        execution_record = {
            "tool_id": tool_id,
            "timestamp": datetime.now().isoformat(),
            "parameters": kwargs,
            "status": "executing"
        }
        
        try:
            result = await tool.execute(**kwargs)
            execution_record["status"] = "success"
            execution_record["result"] = result
            self._execution_history.append(execution_record)
            
            self.logger.debug(f"Tool executed successfully: {tool_id}")
            return result
        
        except Exception as e:
            execution_record["status"] = "failed"
            execution_record["error"] = str(e)
            self._execution_history.append(execution_record)
            
            self.logger.error(f"Tool execution failed: {tool_id}: {e}")
            raise
        
        finally:
            if len(self._execution_history) > self._max_history:
                self._execution_history.pop(0)
    
    def disable_tool(self, tool_id: str):
        """Disable a tool."""
        tool = self.get_tool(tool_id)
        if tool:
            tool.enabled = False
            self.logger.info(f"Tool disabled: {tool_id}")
    
    def enable_tool(self, tool_id: str):
        """Enable a tool."""
        tool = self.get_tool(tool_id)
        if tool:
            tool.enabled = True
            self.logger.info(f"Tool enabled: {tool_id}")
    
    def get_tool_stats(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a tool."""
        tool = self.get_tool(tool_id)
        if not tool:
            return None
        
        return {
            "tool_id": tool_id,
            "name": tool.name,
            "usage_count": tool.usage_count,
            "success_rate": tool.success_rate,
            "last_used": tool.last_used.isoformat() if tool.last_used else None,
            "registered_at": tool.registered_at.isoformat()
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all tools."""
        return {
            "total_tools": len(self.tools),
            "enabled_tools": sum(1 for t in self.tools.values() if t.enabled),
            "total_executions": len(self._execution_history),
            "by_type": {
                tt: len(self.get_tools_by_type(tt))
                for tt in ToolType
            },
            "tools": {
                tid: self.get_tool_stats(tid)
                for tid in self.tools
            }
        }
    
    def get_execution_history(self, limit: int = 100) -> List[Dict]:
        """Get tool execution history."""
        return self._execution_history[-limit:]
        
    async def execute_tool_chain(self, tool_chain: List[str]) -> List[Any]:
        results = []
        prev_output = None
        for tool_id in tool_chain:
            kwargs = {}
            if prev_output is not None:
                kwargs['prev_output'] = prev_output
            res = await self.execute_tool(tool_id, **kwargs)
            results.append(res)
            prev_output = res
        return results

def execute_tool_chain(tool_chain: List[str]) -> List[Any]:
    import asyncio
    registry = get_tool_registry()
    async def run_chain():
        return await registry.execute_tool_chain(tool_chain)
        
    try:
        loop = asyncio.get_running_loop()
        future = asyncio.run_coroutine_threadsafe(run_chain(), loop)
        return future.result(timeout=len(tool_chain)*10)
    except RuntimeError:
        return asyncio.run(run_chain())


_global_tool_registry: ToolRegistry = None
_registry_lock = threading.Lock()


def get_tool_registry() -> ToolRegistry:
    """Get or create the global tool registry. Thread-safe singleton."""
    global _global_tool_registry
    if _global_tool_registry is None:
        with _registry_lock:
            if _global_tool_registry is None:
                _global_tool_registry = ToolRegistry()
    return _global_tool_registry


def set_tool_registry(registry: ToolRegistry):
    """Set the global tool registry."""
    global _global_tool_registry
    with _registry_lock:
        _global_tool_registry = registry
