"""
Sistema de Monitoreo y Métricas para Producción
Fase 5: Optimización y Producción
"""

import time
import psutil
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from functools import wraps
import asyncio
import json

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """Métricas del sistema."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    active_connections: int
    uptime_seconds: float

@dataclass
class ApplicationMetrics:
    """Métricas de la aplicación."""
    timestamp: datetime
    total_requests: int
    requests_per_second: float
    average_response_time: float
    error_rate: float
    active_sessions: int
    total_analyses: int
    successful_analyses: int
    failed_analyses: int

class PerformanceMonitor:
    """Monitor de rendimiento del sistema."""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.response_times = []
        self.error_count = 0
        self.active_sessions = 0
        self.total_analyses = 0
        self.successful_analyses = 0
        self.failed_analyses = 0
        
        logger.info("PerformanceMonitor initialized")
    
    def get_system_metrics(self) -> SystemMetrics:
        """Obtener métricas del sistema."""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memoria
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            
            # Conexiones de red
            connections = len(psutil.net_connections())
            
            # Uptime
            uptime_seconds = time.time() - self.start_time
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                disk_free_gb=disk_free_gb,
                active_connections=connections,
                uptime_seconds=uptime_seconds
            )
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return None
    
    def get_application_metrics(self) -> ApplicationMetrics:
        """Obtener métricas de la aplicación."""
        try:
            uptime_seconds = time.time() - self.start_time
            requests_per_second = self.request_count / uptime_seconds if uptime_seconds > 0 else 0
            
            average_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
            
            error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
            
            return ApplicationMetrics(
                timestamp=datetime.now(),
                total_requests=self.request_count,
                requests_per_second=requests_per_second,
                average_response_time=average_response_time,
                error_rate=error_rate,
                active_sessions=self.active_sessions,
                total_analyses=self.total_analyses,
                successful_analyses=self.successful_analyses,
                failed_analyses=self.failed_analyses
            )
            
        except Exception as e:
            logger.error(f"Error getting application metrics: {e}")
            return None
    
    def record_request(self, response_time: float, success: bool = True):
        """Registrar una petición."""
        self.request_count += 1
        self.response_times.append(response_time)
        
        # Mantener solo los últimos 1000 tiempos de respuesta
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
        
        if not success:
            self.error_count += 1
    
    def record_analysis(self, success: bool = True):
        """Registrar un análisis."""
        self.total_analyses += 1
        if success:
            self.successful_analyses += 1
        else:
            self.failed_analyses += 1
    
    def update_active_sessions(self, count: int):
        """Actualizar número de sesiones activas."""
        self.active_sessions = count
    
    def get_health_status(self) -> Dict[str, Any]:
        """Obtener estado de salud del sistema."""
        try:
            system_metrics = self.get_system_metrics()
            app_metrics = self.get_application_metrics()
            
            if not system_metrics or not app_metrics:
                return {"status": "unhealthy", "reason": "metrics_unavailable"}
            
            # Verificar condiciones de salud
            health_issues = []
            
            # CPU alto
            if system_metrics.cpu_percent > 90:
                health_issues.append("high_cpu")
            
            # Memoria alta
            if system_metrics.memory_percent > 90:
                health_issues.append("high_memory")
            
            # Disco lleno
            if system_metrics.disk_usage_percent > 90:
                health_issues.append("high_disk_usage")
            
            # Tasa de error alta
            if app_metrics.error_rate > 10:
                health_issues.append("high_error_rate")
            
            # Tiempo de respuesta alto
            if app_metrics.average_response_time > 5.0:
                health_issues.append("slow_response")
            
            status = "healthy" if not health_issues else "degraded"
            
            return {
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": system_metrics.uptime_seconds,
                "issues": health_issues,
                "metrics": {
                    "system": {
                        "cpu_percent": system_metrics.cpu_percent,
                        "memory_percent": system_metrics.memory_percent,
                        "disk_usage_percent": system_metrics.disk_usage_percent
                    },
                    "application": {
                        "total_requests": app_metrics.total_requests,
                        "requests_per_second": app_metrics.requests_per_second,
                        "average_response_time": app_metrics.average_response_time,
                        "error_rate": app_metrics.error_rate,
                        "active_sessions": app_metrics.active_sessions
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {"status": "unhealthy", "reason": str(e)}

# Instancia global del monitor
performance_monitor = PerformanceMonitor()

def monitor_performance(func):
    """Decorator para monitorear rendimiento de funciones."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        success = True
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            logger.error(f"Error in {func.__name__}: {e}")
            raise
        finally:
            response_time = time.time() - start_time
            performance_monitor.record_request(response_time, success)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        success = True
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            logger.error(f"Error in {func.__name__}: {e}")
            raise
        finally:
            response_time = time.time() - start_time
            performance_monitor.record_request(response_time, success)
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

class AlertManager:
    """Gestor de alertas del sistema."""
    
    def __init__(self):
        self.alerts = []
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_usage_percent": 90.0,
            "error_rate": 5.0,
            "response_time": 3.0
        }
        
        logger.info("AlertManager initialized")
    
    def check_alerts(self, metrics: Dict[str, Any]) -> list:
        """Verificar alertas basadas en métricas."""
        alerts = []
        
        try:
            system_metrics = metrics.get("system", {})
            app_metrics = metrics.get("application", {})
            
            # Alerta de CPU
            if system_metrics.get("cpu_percent", 0) > self.alert_thresholds["cpu_percent"]:
                alerts.append({
                    "type": "cpu_high",
                    "severity": "warning",
                    "message": f"CPU usage is {system_metrics['cpu_percent']:.1f}%",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Alerta de memoria
            if system_metrics.get("memory_percent", 0) > self.alert_thresholds["memory_percent"]:
                alerts.append({
                    "type": "memory_high",
                    "severity": "warning",
                    "message": f"Memory usage is {system_metrics['memory_percent']:.1f}%",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Alerta de disco
            if system_metrics.get("disk_usage_percent", 0) > self.alert_thresholds["disk_usage_percent"]:
                alerts.append({
                    "type": "disk_high",
                    "severity": "critical",
                    "message": f"Disk usage is {system_metrics['disk_usage_percent']:.1f}%",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Alerta de tasa de error
            if app_metrics.get("error_rate", 0) > self.alert_thresholds["error_rate"]:
                alerts.append({
                    "type": "error_rate_high",
                    "severity": "warning",
                    "message": f"Error rate is {app_metrics['error_rate']:.1f}%",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Alerta de tiempo de respuesta
            if app_metrics.get("average_response_time", 0) > self.alert_thresholds["response_time"]:
                alerts.append({
                    "type": "response_time_high",
                    "severity": "warning",
                    "message": f"Average response time is {app_metrics['average_response_time']:.2f}s",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Agregar alertas a la lista
            self.alerts.extend(alerts)
            
            # Mantener solo las últimas 100 alertas
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
            return []
    
    def get_recent_alerts(self, hours: int = 24) -> list:
        """Obtener alertas recientes."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
        ]

# Instancia global del gestor de alertas
alert_manager = AlertManager()
