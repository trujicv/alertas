"""
Cargador de configuración del sistema de alertas.
Proporciona acceso centralizado a todos los parámetros de configuración.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class ConfigLoader:
    """Gestor de configuración singleton para la aplicación."""
    
    _instance: Optional['ConfigLoader'] = None
    _config_path: Path = Path(__file__).parent.parent / "data" / "config.json"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    
    def __init__(self):
        if self._initialized:
            return
        self._config: Dict[str, Any] = {}
        self._load_config()
        self._initialized = True

    
    def _load_config(self) -> None:
        """Carga la configuración desde el archivo JSON."""
        try:
            if not self._config_path.exists():
                raise FileNotFoundError(f"Archivo de configuración no encontrado: {self._config_path}")
            
            with open(self._config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            
            self._validate_config()
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al parsear el archivo de configuración: {e}")
        except Exception as e:
            raise RuntimeError(f"Error al cargar la configuración: {e}")
        
    
    def _validate_config(self) -> None:
        """Valida que la configuración tenga la estructura requerida."""
        required_keys = ['master_credentials', 'email', 'websocket', 'logging', 'monitor']
        for key in required_keys:
            if key not in self._config:
                raise ValueError(f"Clave requerida '{key}' no encontrada en la configuración")
            
    
    def save_config(self) -> None:
        """Guarda la configuración actual en el archivo JSON."""
        try:
            self._config['last_updated'] = datetime.now().isoformat()
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise RuntimeError(f"Error al guardar la configuración: {e}")
        
    
    def reload(self) -> None:
        """Recarga la configuración desde el archivo."""
        self._load_config()
    

    # Propiedades de acceso a la configuración
    @property
    def master_username(self) -> str:
        """Obtiene el usuario maestro."""
        return self._config['master_credentials']['username']
    
    @property
    def master_password(self) -> str:
        """Obtiene la contraseña maestra."""
        return self._config['master_credentials']['password']
    
    @property
    def email_server(self) -> str:
        """Obtiene el servidor IMAP."""
        return self._config['email']['server']
    
    @property
    def email_port(self) -> int:
        """Obtiene el puerto IMAP."""
        return self._config['email']['port']
    
    @property
    def email_address(self) -> str:
        """Obtiene la dirección de correo."""
        return self._config['email']['address']
    
    @property
    def email_password(self) -> str:
        """Obtiene la contraseña del correo."""
        return self._config['email']['password']
    
    @property
    def email_ssl(self) -> bool:
        """Indica si se usa SSL para IMAP."""
        return self._config['email']['ssl']
    
    @property
    def websocket_host(self) -> str:
        """Obtiene el host del servidor WebSocket."""
        return self._config['websocket']['host']
    
    @property
    def websocket_port(self) -> int:
        """Obtiene el puerto del servidor WebSocket."""
        return self._config['websocket']['port']
    
    @property
    def log_level(self) -> str:
        """Obtiene el nivel de logging."""
        return self._config['logging']['level']
    
    @property
    def log_max_size_mb(self) -> int:
        """Obtiene el tamaño máximo de archivos de log."""
        return self._config['logging']['max_file_size_mb']
    
    @property
    def log_backup_count(self) -> int:
        """Obtiene el número de backups de logs."""
        return self._config['logging']['backup_count']
    
    @property
    def monitor_check_interval(self) -> int:
        """Obtiene el intervalo de chequeo en segundos."""
        return self._config['monitor']['check_interval']
    
    @property
    def monitor_idle_timeout(self) -> int:
        """Obtiene el timeout de idle en segundos."""
        return self._config['monitor']['idle_timeout']
    

    def update_email_config(self, server: str, port: int, address: str, 
                           password: str, ssl: bool) -> None:
        """
        Actualiza la configuración de email y guarda los cambios.
        
        Args:
            server: Servidor IMAP
            port: Puerto IMAP
            address: Dirección de correo
            password: Contraseña del correo
            ssl: Usar SSL
        """
        self._config['email']['server'] = server
        self._config['email']['port'] = port
        self._config['email']['address'] = address
        self._config['email']['password'] = password
        self._config['email']['ssl'] = ssl
        self.save_config()
    

    def verify_master_credentials(self, username: str, password: str) -> bool:
        """
        Verifica las credenciales maestras.
        
        Args:
            username: Usuario a verificar
            password: Contraseña a verificar
            
        Returns:
            True si las credenciales son correctas
        """
        return (username == self.master_username and 
                password == self.master_password)
    

    def is_email_configured(self) -> bool:
        """Verifica si el email está configurado."""
        return (bool(self.email_address) and 
                bool(self.email_password) and 
                bool(self.email_server))
    
    
    def get_all_config(self) -> Dict[str, Any]:
        """Obtiene toda la configuración (útil para debugging)."""
        return self._config.copy()


# Instancia global singleton
config = ConfigLoader()
