"""
Servidor WebSocket para comunicación en tiempo real.
Transmite eventos de email a clientes conectados.
"""

import asyncio
import websockets
import json
import logging
from typing import Set, Dict, Any, Optional
from websockets.server import WebSocketServerProtocol

from config_loader import config


class WebSocketServer:
    """Servidor WebSocket para notificaciones en tiempo real."""
    
    def __init__(self):
        """Inicializa el servidor WebSocket."""
        self.logger = logging.getLogger(__name__)
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server: Optional[websockets.WebSocketServer] = None
        self._host = config.websocket_host
        self._port = config.websocket_port
        self._running = False
    
    async def start(self) -> None:
        """Inicia el servidor WebSocket."""
        try:
            self.server = await websockets.serve(
                self._handle_client,
                self._host,
                self._port
            )
            self._running = True
            self.logger.info(f"Servidor WebSocket iniciado en ws://{self._host}:{self._port}")
            
            # Mantener el servidor corriendo
            await asyncio.Future()
            
        except Exception as e:
            self.logger.error(f"Error al iniciar servidor WebSocket: {e}")
            raise
    
    async def stop(self) -> None:
        """Detiene el servidor WebSocket."""
        if not self._running:
            return
        
        self._running = False
        
        # Cerrar todas las conexiones de clientes
        if self.clients:
            await asyncio.gather(
                *[client.close() for client in self.clients],
                return_exceptions=True
            )
        
        # Cerrar el servidor
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        self.logger.info("Servidor WebSocket detenido")
    
    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """
        Maneja la conexión de un cliente WebSocket.
        
        Args:
            websocket: Conexión del cliente
            path: Ruta de la conexión
        """
        # Registrar cliente
        self.clients.add(websocket)
        client_addr = websocket.remote_address
        self.logger.info(f"Cliente conectado: {client_addr} (Total: {len(self.clients)})")
        
        try:
            # Enviar mensaje de bienvenida
            await self._send_to_client(websocket, {
                'type': 'connected',
                'message': 'Conectado al servidor de alertas',
                'clients_connected': len(self.clients)
            })
            
            # Mantener la conexión abierta y escuchar mensajes
            async for message in websocket:
                await self._handle_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Cliente desconectado: {client_addr}")
        except Exception as e:
            self.logger.error(f"Error manejando cliente {client_addr}: {e}")
        finally:
            # Desregistrar cliente
            self.clients.discard(websocket)
            self.logger.info(f"Cliente removido: {client_addr} (Total: {len(self.clients)})")
    
    async def _handle_message(self, websocket: WebSocketServerProtocol, message: str) -> None:
        """
        Procesa un mensaje recibido de un cliente.
        
        Args:
            websocket: Conexión del cliente
            message: Mensaje recibido
        """
        try:
            data = json.loads(message)
            msg_type = data.get('type', 'unknown')
            msg_data = data.get('data', {})
            
            self.logger.debug(f"Mensaje recibido de {websocket.remote_address}: {msg_type}")
            
            # Procesar según el tipo de mensaje
            if msg_type == 'ping':
                await self._send_to_client(websocket, {'type': 'pong'})
            
            elif msg_type == 'status':
                await self._send_to_client(websocket, {
                    'type': 'status_response',
                    'clients_connected': len(self.clients),
                    'server_running': self._running
                })
            
            elif msg_type == 'get_emails':
                await self._handle_get_emails(websocket)
            
            elif msg_type == 'get_activities':
                await self._handle_get_activities(websocket)
            
            elif msg_type == 'get_config':
                await self._handle_get_config(websocket)
            
            elif msg_type == 'mark_read':
                await self._handle_mark_read(websocket, msg_data)
            
            elif msg_type == 'add_activity':
                await self._handle_add_activity(websocket, msg_data)
            
            elif msg_type == 'delete_activity':
                await self._handle_delete_activity(websocket, msg_data)
            
            elif msg_type == 'update_config':
                await self._handle_update_config(websocket, msg_data)
            
            else:
                self.logger.warning(f"Tipo de mensaje desconocido: {msg_type}")
                await self._send_to_client(websocket, {
                    'type': 'error',
                    'message': f'Tipo de mensaje desconocido: {msg_type}'
                })
                
        except json.JSONDecodeError:
            self.logger.warning(f"Mensaje no JSON recibido: {message[:100]}")
        except Exception as e:
            self.logger.error(f"Error procesando mensaje: {e}")
            await self._send_to_client(websocket, {
                'type': 'error',
                'message': str(e)
            })
    
    async def _send_to_client(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]) -> bool:
        """
        Envía un mensaje a un cliente específico.
        
        Args:
            websocket: Conexión del cliente
            data: Datos a enviar
            
        Returns:
            True si fue exitoso
        """
        try:
            message = json.dumps(data, ensure_ascii=False)
            await websocket.send(message)
            return True
        except Exception as e:
            self.logger.error(f"Error enviando mensaje a cliente: {e}")
            return False
    
    async def _handle_get_emails(self, websocket: WebSocketServerProtocol) -> None:
        """Envía la lista de correos al cliente."""
        from storage_manager import storage
        
        emails = storage.get_all_emails()
        await self._send_to_client(websocket, {
            'type': 'email_list',
            'data': {'emails': emails}
        })
        self.logger.info(f"Enviados {len(emails)} correos al cliente")
    
    async def _handle_get_activities(self, websocket: WebSocketServerProtocol) -> None:
        """Envía la lista de actividades al cliente."""
        from schedule_manager import scheduler
        
        activities = scheduler.get_all_activities()
        await self._send_to_client(websocket, {
            'type': 'activities_list',
            'data': {'activities': activities}
        })
        self.logger.info(f"Enviadas {len(activities)} actividades al cliente")
    
    async def _handle_get_config(self, websocket: WebSocketServerProtocol) -> None:
        """Envía la configuración actual al cliente."""
        from config_loader import config
        
        config_data = {
            'email': {
                'server': config.email_server,
                'port': config.email_port,
                'address': config.email_address,
                'ssl': config.email_ssl
                # No enviamos la contraseña por seguridad
            },
            'websocket': {
                'host': config.websocket_host,
                'port': config.websocket_port
            },
            'logging': {
                'level': config.log_level
            },
            'monitor': {
                'check_interval': config.monitor_check_interval,
                'idle_timeout': config.monitor_idle_timeout
            }
        }
        
        await self._send_to_client(websocket, {
            'type': 'config_data',
            'data': config_data
        })
        self.logger.info("Configuración enviada al cliente")
    
    async def _handle_mark_read(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]) -> None:
        """Marca un correo como leído."""
        from storage_manager import storage
        
        email_id = data.get('email_id')
        if not email_id:
            await self._send_to_client(websocket, {
                'type': 'error',
                'message': 'email_id requerido'
            })
            return
        
        # Leer datos actuales
        emails_data = storage._read_json(storage.emails_file)
        emails = emails_data.get('emails', [])
        
        # Actualizar el correo
        updated = False
        for email in emails:
            if email.get('id') == email_id:
                email['unread'] = False
                updated = True
                break
        
        if updated:
            # Guardar cambios
            emails_data['emails'] = emails
            storage._write_json(storage.emails_file, emails_data)
            
            await self._send_to_client(websocket, {
                'type': 'email_marked_read',
                'data': {'email_id': email_id}
            })
            self.logger.info(f"Correo {email_id} marcado como leído")
        else:
            await self._send_to_client(websocket, {
                'type': 'error',
                'message': f'Correo {email_id} no encontrado'
            })
    
    async def _handle_add_activity(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]) -> None:
        """Agrega una nueva actividad."""
        from schedule_manager import scheduler
        
        title = data.get('title')
        description = data.get('description', '')
        scheduled_date = data.get('scheduled_date')
        
        if not title or not scheduled_date:
            await self._send_to_client(websocket, {
                'type': 'error',
                'message': 'title y scheduled_date son requeridos'
            })
            return
        
        try:
            activity = scheduler.add_activity(title, description, scheduled_date)
            
            # Notificar al cliente que lo agregó
            await self._send_to_client(websocket, {
                'type': 'activity_added',
                'data': activity
            })
            
            # Broadcast a todos los clientes
            await self.broadcast({
                'type': 'activity_added',
                'data': activity
            })
            
            self.logger.info(f"Actividad agregada: {title}")
        except Exception as e:
            await self._send_to_client(websocket, {
                'type': 'error',
                'message': f'Error al agregar actividad: {str(e)}'
            })
    
    async def _handle_delete_activity(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]) -> None:
        """Elimina una actividad."""
        from schedule_manager import scheduler
        
        activity_id = data.get('activity_id')
        if not activity_id:
            await self._send_to_client(websocket, {
                'type': 'error',
                'message': 'activity_id requerido'
            })
            return
        
        try:
            scheduler.remove_activity(activity_id)
            
            # Notificar al cliente que lo eliminó
            await self._send_to_client(websocket, {
                'type': 'activity_deleted',
                'data': {'activity_id': activity_id}
            })
            
            # Broadcast a todos los clientes
            await self.broadcast({
                'type': 'activity_deleted',
                'data': {'activity_id': activity_id}
            })
            
            self.logger.info(f"Actividad eliminada: {activity_id}")
        except Exception as e:
            await self._send_to_client(websocket, {
                'type': 'error',
                'message': f'Error al eliminar actividad: {str(e)}'
            })
    
    async def _handle_update_config(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]) -> None:
        """Actualiza la configuración."""
        from config_loader import config
        
        try:
            # Actualizar configuración de email si está presente
            if 'email' in data:
                email_config = data['email']
                # Obtener valores actuales como fallback
                current = config.get_all_config()['email']
                config.update_email_config(
                    server=email_config.get('server', current['server']),
                    port=email_config.get('port', current['port']),
                    address=email_config.get('address', current['address']),
                    password=email_config.get('password', current['password']),
                    ssl=email_config.get('ssl', current['ssl'])
                )
            
            # Actualizar otras configuraciones directamente en el archivo
            if 'monitor' in data or 'logging' in data:
                config_data = config.get_all_config()
                
                if 'monitor' in data:
                    config_data['monitor'].update(data['monitor'])
                
                if 'logging' in data:
                    config_data['logging'].update(data['logging'])
                
                # Actualizar el diccionario interno y guardar
                config._config = config_data
                config.save_config()
            
            # Notificar éxito
            await self._send_to_client(websocket, {
                'type': 'config_updated',
                'message': 'Configuración actualizada correctamente'
            })
            
            self.logger.info("Configuración actualizada por cliente")
            
        except Exception as e:
            await self._send_to_client(websocket, {
                'type': 'error',
                'message': f'Error al actualizar configuración: {str(e)}'
            })
    
    async def broadcast(self, data: Dict[str, Any]) -> int:
        """
        Envía un mensaje a todos los clientes conectados.
        
        Args:
            data: Datos a transmitir
            
        Returns:
            Número de clientes que recibieron el mensaje
        """
        if not self.clients:
            self.logger.debug("No hay clientes conectados para broadcast")
            return 0
        
        message = json.dumps(data, ensure_ascii=False)
        success_count = 0
        failed_clients = []
        
        # Enviar a todos los clientes
        for client in self.clients.copy():
            try:
                await client.send(message)
                success_count += 1
            except websockets.exceptions.ConnectionClosed:
                failed_clients.append(client)
            except Exception as e:
                self.logger.error(f"Error en broadcast a {client.remote_address}: {e}")
                failed_clients.append(client)
        
        # Limpiar clientes fallidos
        for client in failed_clients:
            self.clients.discard(client)
        
        self.logger.info(f"Broadcast enviado a {success_count}/{len(self.clients) + len(failed_clients)} clientes")
        return success_count
    
    def broadcast_sync(self, data: Dict[str, Any]) -> None:
        """
        Versión síncrona de broadcast para llamar desde threads no-async.
        
        Args:
            data: Datos a transmitir
        """
        try:
            # Obtener el event loop actual o crear uno nuevo
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Si el loop está corriendo, usar run_coroutine_threadsafe
                    asyncio.run_coroutine_threadsafe(self.broadcast(data), loop)
                else:
                    # Si no está corriendo, ejecutar directamente
                    loop.run_until_complete(self.broadcast(data))
            except RuntimeError:
                # No hay event loop, crear tarea para el loop principal
                asyncio.create_task(self.broadcast(data))
                
        except Exception as e:
            self.logger.error(f"Error en broadcast_sync: {e}")
    
    def broadcast_new_email(self, email_data: Dict[str, Any]) -> None:
        """
        Transmite un nuevo email a todos los clientes.
        Esta es la función que se pasará como callback al EmailMonitor.
        
        Args:
            email_data: Datos del email
        """
        message = {
            'type': 'new_email',
            'data': email_data,
            'timestamp': email_data.get('timestamp')
        }
        self.broadcast_sync(message)
        self.logger.info(f"Nuevo email transmitido: {email_data.get('subject', 'Sin asunto')}")
    
    @property
    def is_running(self) -> bool:
        """Indica si el servidor está corriendo."""
        return self._running
    
    @property
    def connected_clients(self) -> int:
        """Número de clientes conectados."""
        return len(self.clients)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del servidor."""
        return {
            'running': self._running,
            'host': self._host,
            'port': self._port,
            'connected_clients': len(self.clients)
        }
