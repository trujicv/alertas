"""
Servidor IMAP de prueba integrado.
Se inicia automáticamente si no hay configuración de email.
"""

import socket
import threading
import logging
from typing import List, Dict, Any


class TestIMAPServer:
    """Servidor IMAP simple para pruebas."""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 1143):
        """
        Inicializa el servidor IMAP de prueba.
        
        Args:
            host: Host donde escuchar
            port: Puerto donde escuchar
        """
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)
        self.server_socket = None
        self.server_thread = None
        self.running = False
        
        # Credenciales de prueba
        self.username = 'test@alertas.local'
        self.password = 'test123'
        
        # Correos de prueba
        self.test_emails = [
            {
                'uid': '1',
                'from': 'Juan Pérez <juan.perez@empresa.com>',
                'to': self.username,
                'subject': 'Reunión importante - Q4 2025',
                'date': 'Fri, 22 Nov 2025 10:30:00 -0500',
                'body': 'Hola equipo,\n\nTenemos una reunión importante el próximo viernes.\n\nSaludos,\nJuan'
            },
            {
                'uid': '2',
                'from': 'Sistema <noreply@alertas.com>',
                'to': self.username,
                'subject': 'Reporte diario del sistema',
                'date': 'Fri, 22 Nov 2025 08:00:00 -0500',
                'body': 'Reporte automático:\n- Usuarios: 125\n- Correos: 487\n- Estado: OK'
            },
            {
                'uid': '3',
                'from': 'María González <maria@cliente.com>',
                'to': self.username,
                'subject': 'Consulta sobre facturación',
                'date': 'Thu, 21 Nov 2025 16:45:00 -0500',
                'body': 'Buenos días,\n\nNecesito información sobre mi factura.\n\nGracias,\nMaría'
            }
        ]
    
    def start(self) -> None:
        """Inicia el servidor en un thread separado."""
        if self.running:
            return
        
        self.running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        self.logger.info(f"Servidor IMAP de prueba iniciado en {self.host}:{self.port}")
        self.logger.info(f"Credenciales: {self.username} / {self.password}")
    
    def stop(self) -> None:
        """Detiene el servidor."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        self.logger.info("Servidor IMAP de prueba detenido")
    
    def _run_server(self) -> None:
        """Ejecuta el servidor."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)  # Timeout para poder verificar self.running
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Error aceptando cliente: {e}")
        except Exception as e:
            self.logger.error(f"Error en servidor IMAP: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def _handle_client(self, client_socket: socket.socket, address: tuple) -> None:
        """Maneja una conexión de cliente."""
        self.logger.debug(f"Cliente conectado desde {address}")
        logged_in = False
        selected = False
        
        try:
            # Greeting
            client_socket.send(b"* OK IMAP4rev1 Test Server Ready\r\n")
            
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break
                
                command = data.decode('utf-8', errors='ignore').strip()
                parts = command.split()
                
                if len(parts) < 2:
                    continue
                
                tag = parts[0]
                cmd = parts[1].upper()
                
                if cmd == "CAPABILITY":
                    client_socket.send(b"* CAPABILITY IMAP4rev1\r\n")
                    client_socket.send(f"{tag} OK CAPABILITY completed\r\n".encode())
                
                elif cmd == "LOGIN":
                    if len(parts) >= 4:
                        username = parts[2].strip('"')
                        password = parts[3].strip('"')
                        if username == self.username and password == self.password:
                            logged_in = True
                            client_socket.send(f"{tag} OK LOGIN completed\r\n".encode())
                        else:
                            client_socket.send(f"{tag} NO Invalid credentials\r\n".encode())
                
                elif cmd == "SELECT":
                    if logged_in:
                        selected = True
                        client_socket.send(f"* {len(self.test_emails)} EXISTS\r\n".encode())
                        client_socket.send(f"* {len(self.test_emails)} RECENT\r\n".encode())
                        client_socket.send(f"{tag} OK SELECT completed\r\n".encode())
                    else:
                        client_socket.send(f"{tag} NO Not authenticated\r\n".encode())
                
                elif cmd == "SEARCH":
                    if logged_in and selected:
                        uids = " ".join([str(i+1) for i in range(len(self.test_emails))])
                        client_socket.send(f"* SEARCH {uids}\r\n".encode())
                        client_socket.send(f"{tag} OK SEARCH completed\r\n".encode())
                
                elif cmd == "FETCH":
                    if logged_in and selected and len(parts) >= 3:
                        try:
                            uid = int(parts[2]) - 1
                            if 0 <= uid < len(self.test_emails):
                                email_data = self.test_emails[uid]
                                rfc822 = self._build_rfc822(email_data)
                                msg = f"* {parts[2]} FETCH (RFC822 {{{len(rfc822)}}}\r\n{rfc822})\r\n"
                                client_socket.send(msg.encode())
                                client_socket.send(f"{tag} OK FETCH completed\r\n".encode())
                        except (ValueError, IndexError):
                            client_socket.send(f"{tag} BAD Invalid UID\r\n".encode())
                
                elif cmd == "LOGOUT":
                    client_socket.send(b"* BYE Logging out\r\n")
                    client_socket.send(f"{tag} OK LOGOUT completed\r\n".encode())
                    break
                
                else:
                    client_socket.send(f"{tag} BAD Command not recognized\r\n".encode())
        
        except Exception as e:
            self.logger.error(f"Error manejando cliente: {e}")
        finally:
            client_socket.close()
            self.logger.debug(f"Cliente desconectado: {address}")
    
    def _build_rfc822(self, email_data: Dict[str, Any]) -> str:
        """Construye un mensaje RFC822."""
        return f"""From: {email_data['from']}
To: {email_data['to']}
Subject: {email_data['subject']}
Date: {email_data['date']}
Content-Type: text/plain; charset=utf-8

{email_data['body']}"""
    
    def get_credentials(self) -> tuple:
        """Retorna las credenciales de prueba."""
        return (self.username, self.password)
