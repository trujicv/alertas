"""
Sistema de Alertas de Email
Módulo principal del backend
"""

from .config_loader import config, ConfigLoader
from .email_monitor import EmailMonitor
from .websocket_server import WebSocketServer
from .storage_manager import storage, StorageManager
from .schedule_manager import scheduler, ScheduleManager

__version__ = "1.0.0"
__all__ = [
    "config",
    "ConfigLoader",
    "EmailMonitor",
    "WebSocketServer",
    "storage",
    "StorageManager",
    "scheduler",
    "ScheduleManager",
]
