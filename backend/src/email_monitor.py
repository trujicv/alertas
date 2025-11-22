"""
Monitor de correo electrónico IMAP.
Detecta nuevos emails y notifica a través de callbacks.
"""

import imaplib
import email as email_module
from email.header import decode_header
from email.message import Message as EmailMessage
from typing import Callable, Dict, Any, List, Optional, Set
import threading
import time
import logging
from datetime import datetime

from config_loader import config


class EmailMonitor:
    """Monitor de correo electrónico que detecta nuevos mensajes."""
    
    def __init__(self, on_new_email_callback: Callable[[Dict[str, Any]], None]):
        """
        Inicializa el monitor de email.
        
        Args:
            on_new_email_callback: Función a llamar cuando llega un nuevo email
        """
        self.on_new_email = on_new_email_callback
        self.logger = logging.getLogger(__name__)
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._imap: Optional[imaplib.IMAP4_SSL] = None
        self._processed_uids: Set[str] = set()
        self._check_interval = config.monitor_check_interval
        self._idle_timeout = config.monitor_idle_timeout
    
    def start(self) -> None:
        """Inicia el monitoreo de emails en un thread separado."""
        if self._running:
            self.logger.warning("El monitor ya está en ejecución")
            return
        
        if not config.is_email_configured():
            raise ValueError("La configuración de email no está completa")
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        self.logger.info("Monitor de email iniciado")
    
    def stop(self) -> None:
        """Detiene el monitoreo de emails."""
        if not self._running:
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        
        self._disconnect()
        self.logger.info("Monitor de email detenido")
    
    def _connect(self) -> bool:
        """
        Conecta al servidor IMAP.
        
        Returns:
            True si la conexión fue exitosa
        """
        try:
            if config.email_ssl:
                self._imap = imaplib.IMAP4_SSL(config.email_server, config.email_port)
            else:
                self._imap = imaplib.IMAP4(config.email_server, config.email_port)
            
            self._imap.login(config.email_address, config.email_password)
            self._imap.select('INBOX')
            
            self.logger.info(f"Conectado a {config.email_server}:{config.email_port}")
            return True
            
        except imaplib.IMAP4.error as e:
            self.logger.error(f"Error de autenticación IMAP: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error al conectar al servidor IMAP: {e}")
            return False
    
    def _disconnect(self) -> None:
        """Desconecta del servidor IMAP."""
        if self._imap:
            try:
                self._imap.close()
                self._imap.logout()
            except Exception as e:
                self.logger.debug(f"Error al desconectar IMAP: {e}")
            finally:
                self._imap = None
    
    def _monitor_loop(self) -> None:
        """Loop principal de monitoreo."""
        while self._running:
            try:
                # Conectar si no está conectado
                if not self._imap:
                    if not self._connect():
                        self.logger.error("No se pudo conectar. Reintentando en 30s...")
                        time.sleep(30)
                        continue
                
                # Buscar nuevos emails
                new_emails = self._fetch_new_emails()
                
                # Procesar cada nuevo email
                for email_data in new_emails:
                    try:
                        self.on_new_email(email_data)
                    except Exception as e:
                        self.logger.error(f"Error en callback de nuevo email: {e}")
                
                # Esperar antes del próximo chequeo
                time.sleep(self._check_interval)
                
            except imaplib.IMAP4.abort as e:
                self.logger.warning(f"Conexión IMAP interrumpida: {e}")
                self._disconnect()
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"Error en loop de monitoreo: {e}")
                self._disconnect()
                time.sleep(10)
    
    def _fetch_new_emails(self) -> List[Dict[str, Any]]:
        """
        Busca nuevos emails no procesados.
        
        Returns:
            Lista de emails nuevos parseados
        """
        try:
            # Buscar todos los emails no leídos
            status, messages = self._imap.search(None, 'UNSEEN')
            
            if status != 'OK':
                self.logger.warning("No se pudieron buscar emails")
                return []
            
            email_ids = messages[0].split()
            new_emails = []
            
            for email_id in email_ids:
                email_id_str = email_id.decode()
                
                # Verificar si ya fue procesado
                if email_id_str in self._processed_uids:
                    continue
                
                # Obtener el email
                email_data = self._fetch_email(email_id)
                if email_data:
                    new_emails.append(email_data)
                    self._processed_uids.add(email_id_str)
            
            if new_emails:
                self.logger.info(f"Detectados {len(new_emails)} nuevo(s) email(s)")
            
            return new_emails
            
        except Exception as e:
            self.logger.error(f"Error al buscar emails: {e}")
            return []
    
    def _fetch_email(self, email_id: bytes) -> Optional[Dict[str, Any]]:
        """
        Obtiene y parsea un email específico.
        
        Args:
            email_id: ID del email a obtener
            
        Returns:
            Diccionario con los datos del email o None si falla
        """
        try:
            status, msg_data = self._imap.fetch(email_id, '(RFC822)')
            
            if status != 'OK':
                return None
            
            # Parsear el email
            email_body = msg_data[0][1]
            email_message = email_module.message_from_bytes(email_body)
            
            # Extraer datos principales
            subject = self._decode_header_value(email_message.get('Subject', 'Sin asunto'))
            from_addr = self._decode_header_value(email_message.get('From', 'Desconocido'))
            to_addr = self._decode_header_value(email_message.get('To', ''))
            date_str = email_message.get('Date', '')
            
            # Extraer cuerpo del mensaje
            body = self._get_email_body(email_message)
            
            email_data = {
                'id': email_id.decode(),
                'subject': subject,
                'from': from_addr,
                'to': to_addr,
                'date': date_str,
                'body': body,
                'timestamp': datetime.now().isoformat(),
                'unread': True
            }
            
            self.logger.debug(f"Email parseado: {subject} de {from_addr}")
            return email_data
            
        except Exception as e:
            self.logger.error(f"Error al obtener email {email_id}: {e}")
            return None
    
    def _decode_header_value(self, header_value: str) -> str:
        """
        Decodifica un valor de header de email.
        
        Args:
            header_value: Valor del header a decodificar
            
        Returns:
            String decodificado
        """
        if not header_value:
            return ''
        
        try:
            decoded_parts = decode_header(header_value)
            decoded_str = ''
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_str += part.decode(encoding or 'utf-8', errors='ignore')
                else:
                    decoded_str += part
            
            return decoded_str
        except Exception as e:
            self.logger.warning(f"Error al decodificar header: {e}")
            return str(header_value)
    
    def _get_email_body(self, email_message: EmailMessage) -> str:
        """
        Extrae el cuerpo del mensaje de email.
        
        Args:
            email_message: Mensaje de email parseado
            
        Returns:
            Cuerpo del mensaje como string
        """
        body = ''
        
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get('Content-Disposition', ''))
                    
                    # Buscar parte de texto
                    if content_type == 'text/plain' and 'attachment' not in content_disposition:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            body = payload.decode(charset, errors='ignore')
                            break
            else:
                payload = email_message.get_payload(decode=True)
                if payload:
                    charset = email_message.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='ignore')
            
            # Limitar tamaño del cuerpo
            if len(body) > 5000:
                body = body[:5000] + '...'
            
            return body.strip()
            
        except Exception as e:
            self.logger.warning(f"Error al extraer cuerpo del email: {e}")
            return ''
    
    def set_processed_uids(self, uids: Set[str]) -> None:
        """
        Establece los UIDs ya procesados (útil para restaurar estado).
        
        Args:
            uids: Set de UIDs procesados
        """
        self._processed_uids = uids.copy()
        self.logger.info(f"Cargados {len(uids)} UIDs procesados")
    
    def get_processed_uids(self) -> Set[str]:
        """Obtiene los UIDs procesados."""
        return self._processed_uids.copy()
    
    @property
    def is_running(self) -> bool:
        """Indica si el monitor está en ejecución."""
        return self._running
    
    @property
    def is_connected(self) -> bool:
        """Indica si está conectado al servidor IMAP."""
        return self._imap is not None
