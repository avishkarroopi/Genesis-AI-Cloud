"""
Monitoring, Diagnostics, and Self-Recovery System for GENESIS + JARVIS.
Detects and recovers from hardware failures, sensor failures, and AI errors.
Requirements: 9 (self-diagnostics), 10 (self-recovery), 24 (health dashboard).
"""

import asyncio
import logging
import psutil
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque, defaultdict

try:
    from core.config import SAFE_START
except ImportError:
    SAFE_START = True

from core.event_bus import get_event_bus, EventPriority


class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    RECOVERING = "recovering"
    OFFLINE = "offline"


class ComponentType(Enum):
    MEMORY = "memory"
    PROCESSOR = "processor"
    DISK = "disk"
    NETWORK = "network"
    SENSOR_CAMERA = "sensor_camera"
    SENSOR_MICROPHONE = "sensor_microphone"
    SENSOR_IMU = "sensor_imu"
    MOTOR = "motor"
    AI_ENGINE = "ai_engine"
    EVENT_BUS = "event_bus"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    WORLD_MODEL = "world_model"


@dataclass
class HealthMetric:
    """A health metric for a component."""
    component_type: ComponentType
    metric_name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    unit: str = ""
    status: HealthStatus = HealthStatus.HEALTHY
    
    def to_dict(self) -> Dict:
        return {
            "component": self.component_type.value,
            "metric": self.metric_name,
            "value": self.value,
            "unit": self.unit,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Failure:
    """Records a system failure."""
    failure_id: str
    component: ComponentType
    failure_type: str
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    severity: str = "warning"
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_strategy: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "failure_id": self.failure_id,
            "component": self.component.value,
            "type": self.failure_type,
            "description": self.description,
            "severity": self.severity,
            "recovery_attempted": self.recovery_attempted,
            "recovery_successful": self.recovery_successful,
            "timestamp": self.timestamp.isoformat()
        }


class RecoveryStrategy:
    """Base class for recovery strategies."""
    
    async def execute(self) -> bool:
        """Execute recovery. Returns True if successful."""
        raise NotImplementedError


class ModuleRestartStrategy(RecoveryStrategy):
    """Strategy: Restart a module."""
    
    def __init__(self, module_name: str, restart_func: Callable, logger: logging.Logger = None):
        self.module_name = module_name
        self.restart_func = restart_func
        self.logger = logger or logging.getLogger(__name__)
    
    async def execute(self) -> bool:
        """Restart the module."""
        try:
            if asyncio.iscoroutinefunction(self.restart_func):
                await self.restart_func()
            else:
                self.restart_func()
            
            await asyncio.sleep(1)
            self.logger.info(f"Module {self.module_name} restarted successfully")
            return True
        except Exception as e:
            self.logger.error(f"Module restart failed: {e}")
            return False


class ConfigReloadStrategy(RecoveryStrategy):
    """Strategy: Reload configuration."""
    
    def __init__(self, reload_func: Callable, logger: logging.Logger = None):
        self.reload_func = reload_func
        self.logger = logger or logging.getLogger(__name__)
    
    async def execute(self) -> bool:
        """Reload configuration."""
        try:
            if asyncio.iscoroutinefunction(self.reload_func):
                await self.reload_func()
            else:
                self.reload_func()
            
            self.logger.info("Configuration reloaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Configuration reload failed: {e}")
            return False


class SystemMonitor:
    """
    Monitors system health and detects failures.
    Requirement 9: Self-Diagnostics.
    """
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.event_bus = get_event_bus()
        
        self.health_metrics: deque = deque(maxlen=10000)
        self.failures: deque = deque(maxlen=1000)
        self.component_status: Dict[ComponentType, HealthStatus] = defaultdict(
            lambda: HealthStatus.HEALTHY
        )
        
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._monitor_frequency = 5.0
        
        self._thresholds = {
            "cpu_percent": 85.0,
            "memory_percent": 90.0,
            "disk_percent": 90.0,
            "response_time_ms": 500.0
        }
    
    async def start(self):
        """Start the monitor."""
        if SAFE_START:
            return
            
        self._running = True
        self.logger.info("System monitor started")
        self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                await self._check_system_resources()
                await self._check_component_health()
                await asyncio.sleep(self._monitor_frequency)
            
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}", exc_info=True)
                await asyncio.sleep(2.0)
    
    async def _check_system_resources(self):
        """Check CPU, memory, and disk."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = [
                HealthMetric(
                    ComponentType.PROCESSOR, "cpu_usage", cpu_percent, unit="%",
                    status=self._get_status(cpu_percent, self._thresholds["cpu_percent"])
                ),
                HealthMetric(
                    ComponentType.MEMORY, "memory_usage", memory.percent, unit="%",
                    status=self._get_status(memory.percent, self._thresholds["memory_percent"])
                ),
                HealthMetric(
                    ComponentType.DISK, "disk_usage", disk.percent, unit="%",
                    status=self._get_status(disk.percent, self._thresholds["disk_percent"])
                )
            ]
            
            for metric in metrics:
                self.health_metrics.append(metric)
                self.component_status[metric.component_type] = metric.status
                
                if metric.status in (HealthStatus.CRITICAL, HealthStatus.WARNING):
                    # Never crash the voice pipeline for normal CPU spikes (local AI uses 100% CPU).
                    # Only send warnings, never trigger a full `system_failure`.
                    await self.event_bus.publish(
                        "health_warning",
                        "system_monitor",
                        {"metric": metric.to_dict()},
                        priority=EventPriority.HIGH
                    )
        
        except Exception as e:
            self.logger.error(f"Resource check error: {e}")
    
    async def _check_component_health(self):
        """Check health of system components."""
        try:
            component_checks = {
                ComponentType.NETWORK: self._check_network,
                ComponentType.EVENT_BUS: self._check_event_bus,
            }
            
            for component_type, check_func in component_checks.items():
                try:
                    status = await self._call_async(check_func)
                    self.component_status[component_type] = status
                except Exception as e:
                    self.logger.error(f"Health check error for {component_type.value}: {e}")
        
        except Exception as e:
            self.logger.error(f"Component health check error: {e}")
    
    async def _check_network(self) -> HealthStatus:
        """Check network availability."""
        try:
            psutil.net_if_stats()
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.CRITICAL
    
    async def _check_event_bus(self) -> HealthStatus:
        """Check event bus health."""
        try:
            from core.event_bus import get_event_bus
            bus = get_event_bus()
            stats = bus.get_stats()
            
            if stats["running"]:
                return HealthStatus.HEALTHY
            else:
                return HealthStatus.CRITICAL
        except Exception:
            return HealthStatus.CRITICAL
    
    def _get_status(self, value: float, threshold: float) -> HealthStatus:
        """Get health status based on value and threshold."""
        if value >= threshold:
            return HealthStatus.CRITICAL
        elif value >= threshold * 0.85:  # Only warn at high utilization (85% of threshold)
            return HealthStatus.WARNING
        return HealthStatus.HEALTHY
    
    async def _report_failure(self, component: ComponentType, failure_type: str,
                             description: str, severity: str = "warning"):
        """Report a failure without instantly resetting the entire system."""
        failure_id = f"failure_{component.value}_{datetime.now().timestamp()}"
        failure = Failure(
            failure_id=failure_id,
            component=component,
            failure_type=failure_type,
            description=description,
            severity=severity
        )
        
        self.failures.append(failure)
        
        # NEVER send EventPriority.CRITICAL from the background monitor.
        # It forces the entire speech pipeline back to IDLE inappropriately.
        await self.event_bus.publish(
            "system_failure",
            "system_monitor",
            failure.to_dict(),
            priority=EventPriority.HIGH
        )
        
        self.logger.warning(f"Failure reported: {failure_id}")
    
    async def _call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Call function, handling both sync and async."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    async def stop(self):
        """Stop the monitor."""
        self._running = False
        if self._monitor_task:
            await self._monitor_task
        self.logger.info("System monitor stopped")
    
    def get_overall_health(self) -> HealthStatus:
        """Get overall system health."""
        statuses = list(self.component_status.values())
        
        if not statuses:
            return HealthStatus.HEALTHY
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        
        return HealthStatus.HEALTHY
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": self.get_overall_health().value,
            "component_status": {
                c.value: self.component_status[c].value
                for c in self.component_status
            },
            "recent_metrics": [m.to_dict() for m in list(self.health_metrics)[-10:]],
            "failures": [f.to_dict() for f in list(self.failures)[-10:]]
        }


class SelfRecoverySystem:
    """
    Detects and recovers from failures.
    Requirement 10: Self-Recovery.
    """
    
    def __init__(self, monitor: SystemMonitor, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.event_bus = get_event_bus()
        self.monitor = monitor
        
        self.recovery_strategies: Dict[str, List[RecoveryStrategy]] = defaultdict(list)
        self._recovery_in_progress: set = set()
    
    def register_recovery_strategy(self, component_name: str, strategy: RecoveryStrategy):
        """Register a recovery strategy for a component."""
        self.recovery_strategies[component_name].append(strategy)
        self.logger.info(f"Recovery strategy registered for {component_name}")
    
    async def attempt_recovery(self, failure: Failure) -> bool:
        """Attempt to recover from a failure."""
        component_name = failure.component.value
        
        if component_name in self._recovery_in_progress:
            self.logger.warning(f"Recovery already in progress for {component_name}")
            return False
        
        self._recovery_in_progress.add(component_name)
        
        try:
            strategies = self.recovery_strategies.get(component_name, [])
            
            if not strategies:
                self.logger.warning(f"No recovery strategies for {component_name}")
                failure.recovery_attempted = False
                return False
            
            failure.recovery_attempted = True
            
            for strategy in strategies:
                try:
                    self.logger.info(f"Attempting recovery for {component_name}")
                    
                    success = await strategy.execute()
                    
                    if success:
                        failure.recovery_successful = True
                        failure.recovery_strategy = str(strategy.__class__.__name__)
                        
                        await self.event_bus.publish(
                            "recovery_successful",
                            "recovery_system",
                            {
                                "component": component_name,
                                "strategy": str(strategy.__class__.__name__)
                            },
                            priority=EventPriority.HIGH
                        )
                        
                        self.logger.info(f"Recovery successful for {component_name}")
                        return True
                
                except Exception as e:
                    self.logger.error(f"Recovery strategy failed: {e}")
            
            await self.event_bus.publish(
                "recovery_failed",
                "recovery_system",
                {
                    "component": component_name,
                    "failure_id": failure.failure_id
                },
                priority=EventPriority.CRITICAL
            )
            
            self.logger.warning(f"All recovery strategies failed for {component_name}")
            return False
        
        finally:
            self._recovery_in_progress.discard(component_name)


_global_system_monitor: SystemMonitor = None


def get_system_monitor() -> SystemMonitor:
    """Get or create the global system monitor."""
    global _global_system_monitor
    if _global_system_monitor is None:
        _global_system_monitor = SystemMonitor()
    return _global_system_monitor
