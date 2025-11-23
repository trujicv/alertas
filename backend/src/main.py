"""
Punto de entrada principal de la aplicación.
Orquesta todos los componentes del sistema de alertas.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from config_loader import config
from email_monitor import EmailMonitor
from websocket_server import WebSocketServer
from storage_manager import storage
from schedule_manager import scheduler
from http_server import HTTPServer
from test_imap_server import TestIMAPServer


class AlertApplication:
    """Aplicación principal del sistema de alertas."""
    
    def __init__(self):
        """Inicializa la aplicación."""
        self.logger: Optional[logging.Logger] = None
        self.http_server: Optional[HTTPServer] = None
        self.websocket_server: Optional[WebSocketServer] = None
        self.email_monitor: Optional[EmailMonitor] = None
        self.test_imap_server: Optional[TestIMAPServer] = None
        self._shutdown_event = asyncio.Event()
        
        # Configurar logging
        self._setup_logging()
        
        self.logger.info("=" * 60)
        self.logger.info("Sistema de Alertas de Email - Iniciando")
        self.logger.info("=" * 60)
    
    def _setup_logging(self) -> None:
        """Configura el sistema de logging."""
        # Crear directorio de logs
        log_dir = Path(__file__).parent.parent / "data" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        app_log = log_dir / "app.log"
        error_log = log_dir / "errors.log"
        
        # Configurar formato
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        formatter = logging.Formatter(log_format, date_format)
        
        # Logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, config.log_level))
        
        # Handler para app.log (todos los niveles)
        app_handler = RotatingFileHandler(
            app_log,
            maxBytes=config.log_max_size_mb * 1024 * 1024,
            backupCount=config.log_backup_count,
            encoding='utf-8'
        )
        app_handler.setLevel(logging.DEBUG)
        app_handler.setFormatter(formatter)
        
        # Handler para errors.log (solo errores)
        error_handler = RotatingFileHandler(
            error_log,
            maxBytes=config.log_max_size_mb * 1024 * 1024,
            backupCount=config.log_backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Agregar handlers
        root_logger.addHandler(app_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(console_handler)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Logging configurado: nivel={config.log_level}")
    
    def _on_new_email(self, email_data: dict) -> None:
        """
        Callback llamado cuando llega un nuevo email.
        
        Args:
            email_data: Datos del email
        """
        try:
            # Guardar el email
            storage.save_email(email_data)
            
            # Guardar UID procesado
            storage.save_processed_uid(email_data.get('id'))
            
            # Transmitir por WebSocket
            self.websocket_server.broadcast_new_email(email_data)
            
            self.logger.info(
                f"🔔 Nuevo email: '{email_data.get('subject', 'Sin asunto')}' "
                f"de {email_data.get('from', 'Desconocido')}"
            )
            
        except Exception as e:
            self.logger.error(f"Error procesando nuevo email: {e}", exc_info=True)
    
    def _setup_signal_handlers(self) -> None:
        """Configura los manejadores de señales para shutdown limpio."""
        def signal_handler(signum, frame):
            self.logger.info(f"Señal recibida: {signum}")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def startup(self) -> None:
        """Inicia todos los componentes de la aplicación."""
        try:
            self.logger.info("Iniciando componentes...")
            
            # Verificar configuración
            if not config.is_email_configured():
                self.logger.warning(
                    "ADVERTENCIA: Configuración de email incompleta. "
                    "Configure desde la interfaz web."
                )
            
            # Inicializar gestor de actividades
            self.logger.info("Gestor de actividades disponible")
            activities = scheduler.get_all_activities()
            self.logger.info(f"Actividades registradas: {len(activities)}")
            
            # Iniciar servidor IMAP de prueba si se usa localhost
            email_server = config.email.get('server', 'localhost')
            email_port = config.email.get('port', 1143)
            
            if email_server in ['localhost', '127.0.0.1']:
                self.logger.info(f"Iniciando servidor IMAP de prueba en {email_server}:{email_port}...")
                self.test_imap_server = TestIMAPServer(host=email_server, port=email_port)
                self.test_imap_server.start()
                self.logger.info("✓ Servidor IMAP de prueba iniciado")
                self.logger.info("  Usuario: test@alertas.local | Contraseña: test123")
            
            # Inicializar servidor HTTP
            self.logger.info("Inicializando servidor HTTP...")
            self.http_server = HTTPServer(host='0.0.0.0', port=8080)
            await self.http_server.start()
            
            # Inicializar servidor WebSocket
            self.logger.info("Inicializando servidor WebSocket...")
            self.websocket_server = WebSocketServer()
            
            # Inicializar monitor de email
            self.logger.info("Inicializando monitor de email...")
            self.email_monitor = EmailMonitor(on_new_email_callback=self._on_new_email)
            
            # Restaurar UIDs procesados desde storage
            processed_uids = storage.get_processed_uids()
            self.email_monitor.set_processed_uids(processed_uids)
            self.logger.info(f"Restaurados {len(processed_uids)} UIDs procesados")
            
            # Iniciar monitor de email si está configurado
            if config.is_email_configured():
                self.email_monitor.start()
                self.logger.info("Monitor de email iniciado")
            else:
                self.logger.warning("Monitor de email NO iniciado - configuración incompleta")
            
            self.logger.info("✓ Todos los componentes iniciados correctamente")
            self.logger.info(f"WebSocket escuchando en ws://{config.websocket_host}:{config.websocket_port}")
            
            # Iniciar servidor WebSocket (bloqueante)
            await self.websocket_server.start()
            
        except Exception as e:
            self.logger.error(f"Error durante startup: {e}", exc_info=True)
            raise
    
    async def shutdown(self) -> None:
        """Detiene todos los componentes de manera ordenada."""
        if self._shutdown_event.is_set():
            return
        
        self._shutdown_event.set()
        self.logger.info("Iniciando shutdown...")
        
        try:
            # Detener servidor IMAP de prueba
            if self.test_imap_server:
                self.logger.info("Deteniendo servidor IMAP de prueba...")
                self.test_imap_server.stop()
            
            # Detener monitor de email
            if self.email_monitor:
                self.logger.info("Deteniendo monitor de email...")
                self.email_monitor.stop()
            
            # Guardar UIDs procesados
            if self.email_monitor:
                processed_uids = self.email_monitor.get_processed_uids()
                for uid in processed_uids:
                    storage.save_processed_uid(uid)
                self.logger.info(f"Guardados {len(processed_uids)} UIDs procesados")
            
            # Detener servidor WebSocket
            if self.websocket_server:
                self.logger.info("Deteniendo servidor WebSocket...")
                await self.websocket_server.stop()
            
            # Detener servidor HTTP
            if self.http_server:
                self.logger.info("Deteniendo servidor HTTP...")
                await self.http_server.stop()
            
            self.logger.info("✓ Shutdown completado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error durante shutdown: {e}", exc_info=True)
    
    async def run(self) -> None:
        """Ejecuta la aplicación."""
        try:
            # Configurar manejadores de señales
            self._setup_signal_handlers()
            
            # Iniciar aplicación
            await self.startup()
            
        except KeyboardInterrupt:
            self.logger.info("Interrupción de teclado detectada")
        except Exception as e:
            self.logger.error(f"Error fatal en la aplicación: {e}", exc_info=True)
            raise
        finally:
            await self.shutdown()


async def main() -> None:
    """Función principal."""
    app = AlertApplication()
    try:
        await app.run()
    except Exception as e:
        logging.error(f"Error en main: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✓ Aplicación detenida")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Error fatal: {e}")
        sys.exit(1)
