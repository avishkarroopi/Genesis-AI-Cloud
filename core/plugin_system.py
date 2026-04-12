"""
Expandable Plugin System for GENESIS + JARVIS.
Allows dynamic installation and management of system extensions.
Requirement 26: Expandable Plugin System.
"""

import asyncio
import logging
import importlib
import sys
from typing import Dict, Any, Optional, List, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import inspect
import json


class PluginStatus(Enum):
    INSTALLED = "installed"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    UNINSTALLED = "uninstalled"


@dataclass
class PluginManifest:
    """Plugin metadata and configuration."""
    plugin_id: str
    name: str
    version: str
    author: str
    description: str
    module_path: str
    main_class: str
    dependencies: List[str] = field(default_factory=list)
    provided_hooks: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    min_version: str = "1.0.0"
    max_version: str = "999.0.0"
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "dependencies": self.dependencies,
            "provided_hooks": self.provided_hooks
        }


class PluginBase:
    """Base class for all plugins."""
    
    def __init__(self, manifest: PluginManifest, logger: logging.Logger = None):
        self.manifest = manifest
        self.logger = logger or logging.getLogger(f"plugin.{manifest.plugin_id}")
        self.enabled = False
    
    async def initialize(self):
        """Initialize plugin. Override in subclass."""
        pass
    
    async def shutdown(self):
        """Shutdown plugin. Override in subclass."""
        pass
    
    async def enable(self):
        """Enable plugin."""
        self.enabled = True
        self.logger.info(f"Plugin enabled: {self.manifest.plugin_id}")
    
    async def disable(self):
        """Disable plugin."""
        self.enabled = False
        self.logger.info(f"Plugin disabled: {self.manifest.plugin_id}")


class PluginManager:
    """
    Manages plugin lifecycle: installation, loading, enabling, disabling.
    Requirement 26: Expandable Plugin System.
    """
    
    def __init__(self, plugins_dir: str = "./plugins", logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.plugins_dir = plugins_dir
        self.event_bus = None
        
        self.plugins: Dict[str, PluginBase] = {}
        self.manifests: Dict[str, PluginManifest] = {}
        self.plugin_status: Dict[str, PluginStatus] = {}
        self.plugin_hooks: Dict[str, List[Callable]] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize plugin manager."""
        try:
            from core.event_bus import get_event_bus
            self.event_bus = get_event_bus()
        except Exception as e:
            self.logger.warning(f"Event bus not available during plugin manager init: {e}")
        
        self._initialized = True
        self.logger.info("Plugin manager initialized")
    
    async def load_plugin(self, manifest: PluginManifest) -> Optional[PluginBase]:
        """
        Load a plugin from manifest.
        Dynamically imports and instantiates the plugin.
        """
        
        try:
            if manifest.plugin_id in self.plugins:
                self.logger.warning(f"Plugin {manifest.plugin_id} already loaded")
                return self.plugins[manifest.plugin_id]
            
            sys.path.insert(0, self.plugins_dir)
            
            module = importlib.import_module(manifest.module_path)
            
            plugin_class = getattr(module, manifest.main_class)
            if not issubclass(plugin_class, PluginBase):
                raise TypeError(f"Plugin class must inherit from PluginBase")
            
            plugin_instance = plugin_class(manifest, self.logger)
            
            await plugin_instance.initialize()
            
            self.plugins[manifest.plugin_id] = plugin_instance
            self.manifests[manifest.plugin_id] = manifest
            self.plugin_status[manifest.plugin_id] = PluginStatus.LOADED
            
            self.logger.info(f"Plugin loaded: {manifest.plugin_id} v{manifest.version}")
            
            if self.event_bus:
                await self.event_bus.publish(
                    "plugin_loaded",
                    "plugin_manager",
                    {"plugin_id": manifest.plugin_id, "version": manifest.version}
                )
            
            return plugin_instance
        
        except Exception as e:
            self.logger.error(f"Failed to load plugin {manifest.plugin_id}: {e}", exc_info=True)
            self.plugin_status[manifest.plugin_id] = PluginStatus.ERROR
            return None
    
    async def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin."""
        
        try:
            if plugin_id not in self.plugins:
                self.logger.warning(f"Plugin {plugin_id} not found")
                return False
            
            plugin = self.plugins[plugin_id]
            
            await plugin.shutdown()
            
            del self.plugins[plugin_id]
            self.plugin_status[plugin_id] = PluginStatus.UNINSTALLED
            
            self.logger.info(f"Plugin unloaded: {plugin_id}")
            
            if self.event_bus:
                await self.event_bus.publish(
                    "plugin_unloaded",
                    "plugin_manager",
                    {"plugin_id": plugin_id}
                )
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False
    
    async def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a plugin."""
        
        if plugin_id not in self.plugins:
            self.logger.warning(f"Plugin {plugin_id} not found")
            return False
        
        try:
            plugin = self.plugins[plugin_id]
            await plugin.enable()
            self.plugin_status[plugin_id] = PluginStatus.ENABLED
            
            if self.event_bus:
                await self.event_bus.publish(
                    "plugin_enabled",
                    "plugin_manager",
                    {"plugin_id": plugin_id}
                )
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to enable plugin {plugin_id}: {e}")
            return False
    
    async def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin."""
        
        if plugin_id not in self.plugins:
            self.logger.warning(f"Plugin {plugin_id} not found")
            return False
        
        try:
            plugin = self.plugins[plugin_id]
            await plugin.disable()
            self.plugin_status[plugin_id] = PluginStatus.DISABLED
            
            if self.event_bus:
                await self.event_bus.publish(
                    "plugin_disabled",
                    "plugin_manager",
                    {"plugin_id": plugin_id}
                )
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to disable plugin {plugin_id}: {e}")
            return False
    
    def register_hook(self, hook_name: str, callback: Callable):
        """Register a hook handler."""
        if hook_name not in self.plugin_hooks:
            self.plugin_hooks[hook_name] = []
        
        self.plugin_hooks[hook_name].append(callback)
        self.logger.debug(f"Hook registered: {hook_name}")
    
    async def trigger_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Trigger all handlers for a hook."""
        
        if hook_name not in self.plugin_hooks:
            return []
        
        results = []
        
        for handler in self.plugin_hooks[hook_name]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(*args, **kwargs)
                else:
                    result = handler(*args, **kwargs)
                
                results.append(result)
            
            except Exception as e:
                self.logger.error(f"Hook handler error for {hook_name}: {e}")
        
        return results
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginBase]:
        """Get a loaded plugin."""
        return self.plugins.get(plugin_id)
    
    def list_plugins(self, status_filter: PluginStatus = None) -> List[Dict]:
        """List all plugins."""
        plugins = []
        
        for plugin_id, manifest in self.manifests.items():
            status = self.plugin_status.get(plugin_id, PluginStatus.UNINSTALLED)
            
            if status_filter and status != status_filter:
                continue
            
            plugins.append({
                "plugin_id": plugin_id,
                "manifest": manifest.to_dict(),
                "status": status.value
            })
        
        return plugins
    
    def get_plugin_info(self, plugin_id: str) -> Optional[Dict]:
        """Get detailed info about a plugin."""
        
        if plugin_id not in self.manifests:
            return None
        
        manifest = self.manifests[plugin_id]
        plugin = self.plugins.get(plugin_id)
        status = self.plugin_status.get(plugin_id, PluginStatus.UNINSTALLED)
        
        return {
            "manifest": manifest.to_dict(),
            "status": status.value,
            "enabled": plugin.enabled if plugin else False,
            "loaded": plugin_id in self.plugins
        }
    
    async def reload_plugin(self, plugin_id: str) -> bool:
        """Reload a plugin."""
        
        if plugin_id not in self.manifests:
            return False
        
        was_enabled = (
            self.plugin_status.get(plugin_id) == PluginStatus.ENABLED
        )
        
        await self.unload_plugin(plugin_id)
        manifest = self.manifests[plugin_id]
        
        plugin = await self.load_plugin(manifest)
        
        if plugin and was_enabled:
            await self.enable_plugin(plugin_id)
        
        return plugin is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get plugin manager statistics."""
        return {
            "total_plugins": len(self.manifests),
            "loaded_plugins": len(self.plugins),
            "enabled_plugins": sum(
                1 for s in self.plugin_status.values()
                if s == PluginStatus.ENABLED
            ),
            "by_status": {
                status.value: sum(1 for s in self.plugin_status.values() if s == status)
                for status in PluginStatus
            },
            "registered_hooks": len(self.plugin_hooks)
        }


_global_plugin_manager: PluginManager = None


def get_plugin_manager() -> PluginManager:
    """Get or create the global plugin manager."""
    global _global_plugin_manager
    if _global_plugin_manager is None:
        _global_plugin_manager = PluginManager()
    return _global_plugin_manager


def set_plugin_manager(manager: PluginManager):
    """Set the global plugin manager."""
    global _global_plugin_manager
    _global_plugin_manager = manager
