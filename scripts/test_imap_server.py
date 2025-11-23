#!/usr/bin/env python3
"""
Servidor IMAP de prueba con 3 correos iniciales.
Usar para testing sin configurar un servidor real.

Uso:
    python scripts/test_imap_server.py
"""

import socket
import threading
import json
from pathlib import Path


# Configuración del servidor de prueba
TEST_SERVER_HOST = 'localhost'
TEST_SERVER_PORT = 1143  # Puerto no privilegiado para testing
TEST_USERNAME = 'test@alertas.local'
TEST_PASSWORD = 'test123'


# Correos de prueba
TEST_EMAILS = [
    {
        'uid': '1',
        'from': 'Juan Pérez <juan.perez@empresa.com>',
        'to': TEST_USERNAME,
        'subject': 'Reunión importante - Q4 2025',
        'date': 'Fri, 22 Nov 2025 10:30:00 -0500',
        'body': 'Hola equipo,\n\nTenemos una reunión importante el próximo viernes para revisar los resultados del cuarto trimestre.\n\nSaludos,\nJuan'
    },
    {
        'uid': '2',
        'from': 'Sistema Automático <noreply@alertas.com>',
        'to': TEST_USERNAME,
        'subject': 'Reporte diario del sistema',
        'date': 'Fri, 22 Nov 2025 08:00:00 -0500',
        'body': 'Reporte automático:\n- Usuarios activos: 125\n- Correos procesados: 487\n- Estado: Operacional'
    },
    {
        'uid': '3',
        'from': 'María González <maria.gonzalez@cliente.com>',
        'to': TEST_USERNAME,
        'subject': 'Consulta sobre facturación',
        'date': 'Thu, 21 Nov 2025 16:45:00 -0500',
        'body': 'Buenos días,\n\nNecesito información sobre el estado de mi factura #2025-1234.\n\n¿Podrían ayudarme?\n\nGracias,\nMaría'
    }
]


class IMAPClientHandler:
    """Maneja una conexión de cliente IMAP."""
    
    def __init__(self, client_socket, address):
        self.socket = client_socket
        self.address = address
        self.logged_in = False
        self.selected = False
        print(f"→ Cliente conectado desde {address}")
    
    def send(self, message):
        """Envía un mensaje al cliente."""
        try:
            self.socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"Error enviando mensaje: {e}")
    
    def recv(self):
        """Recibe datos del cliente."""
        try:
            data = self.socket.recv(4096)
            return data.decode('utf-8', errors='ignore').strip()
        except Exception as e:
            print(f"Error recibiendo datos: {e}")
            return ""
    
    def build_rfc822(self, email_data):
        """Construye un mensaje RFC822."""
        msg = f"""From: {email_data['from']}
To: {email_data['to']}
Subject: {email_data['subject']}
Date: {email_data['date']}
Content-Type: text/plain; charset=utf-8

{email_data['body']}"""
        return msg
    
    def handle(self):
        """Maneja la conexión del cliente."""
        # Enviar greeting
        self.send("* OK IMAP4rev1 Test Server Ready\r\n")
        
        try:
            while True:
                command = self.recv()
                if not command:
                    break
                
                print(f"← {self.address}: {command[:50]}")
                
                parts = command.split()
                if len(parts) < 2:
                    continue
                
                tag = parts[0]
                cmd = parts[1].upper()
                
                # Procesar comandos
                if cmd == "CAPABILITY":
                    self.send(f"* CAPABILITY IMAP4rev1 AUTH=PLAIN\r\n")
                    self.send(f"{tag} OK CAPABILITY completed\r\n")
                
                elif cmd == "LOGIN":
                    if len(parts) >= 4:
                        username = parts[2].strip('"')
                        password = parts[3].strip('"')
                        if username == TEST_USERNAME and password == TEST_PASSWORD:
                            self.logged_in = True
                            self.send(f"{tag} OK LOGIN completed\r\n")
                            print(f"✓ Cliente autenticado: {username}")
                        else:
                            self.send(f"{tag} NO [AUTHENTICATIONFAILED] Invalid credentials\r\n")
                    else:
                        self.send(f"{tag} BAD LOGIN requires username and password\r\n")
                
                elif cmd == "SELECT":
                    if self.logged_in:
                        self.selected = True
                        self.send(f"* {len(TEST_EMAILS)} EXISTS\r\n")
                        self.send(f"* {len(TEST_EMAILS)} RECENT\r\n")
                        self.send(f"* OK [UNSEEN {len(TEST_EMAILS)}]\r\n")
                        self.send(f"{tag} OK [READ-WRITE] SELECT completed\r\n")
                    else:
                        self.send(f"{tag} NO Not authenticated\r\n")
                
                elif cmd == "SEARCH":
                    if self.logged_in and self.selected:
                        # Devolver todos los UIDs
                        uids = " ".join([str(i+1) for i in range(len(TEST_EMAILS))])
                        self.send(f"* SEARCH {uids}\r\n")
                        self.send(f"{tag} OK SEARCH completed\r\n")
                    else:
                        self.send(f"{tag} NO Not authenticated or no mailbox selected\r\n")
                
                elif cmd == "FETCH":
                    if self.logged_in and self.selected:
                        try:
                            uid = int(parts[2]) - 1
                            if 0 <= uid < len(TEST_EMAILS):
                                email_data = TEST_EMAILS[uid]
                                rfc822 = self.build_rfc822(email_data)
                                self.send(f"* {parts[2]} FETCH (RFC822 {{{len(rfc822)}}}\r\n{rfc822})\r\n")
                                self.send(f"{tag} OK FETCH completed\r\n")
                            else:
                                self.send(f"{tag} NO Message not found\r\n")
                        except (ValueError, IndexError):
                            self.send(f"{tag} BAD Invalid UID\r\n")
                    else:
                        self.send(f"{tag} NO Not authenticated or no mailbox selected\r\n")
                
                elif cmd == "LOGOUT":
                    self.send(f"* BYE Logging out\r\n")
                    self.send(f"{tag} OK LOGOUT completed\r\n")
                    break
                
                else:
                    self.send(f"{tag} BAD Command not recognized: {cmd}\r\n")
        
        except Exception as e:
            print(f"Error manejando cliente: {e}")
        finally:
            self.socket.close()
            print(f"✗ Cliente desconectado: {self.address}")


def update_config_file():
    """Actualiza el archivo config.json con las credenciales de prueba."""
    config_path = Path(__file__).parent.parent / "backend" / "data" / "config.json"
    
    if not config_path.exists():
        print(f"⚠ Advertencia: No se encontró {config_path}")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Actualizar configuración de email
        config['email']['server'] = TEST_SERVER_HOST
        config['email']['port'] = TEST_SERVER_PORT
        config['email']['address'] = TEST_USERNAME
        config['email']['password'] = TEST_PASSWORD
        config['email']['ssl'] = False
        
        # Guardar
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Configuración actualizada en {config_path}")
        return True
    except Exception as e:
        print(f"✗ Error al actualizar configuración: {e}")
        return False


def run_server():
    """Ejecuta el servidor IMAP de prueba."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((TEST_SERVER_HOST, TEST_SERVER_PORT))
        server_socket.listen(5)
        
        print(f"✓ Servidor IMAP de prueba iniciado en {TEST_SERVER_HOST}:{TEST_SERVER_PORT}")
        print(f"  Usuario: {TEST_USERNAME}")
        print(f"  Contraseña: {TEST_PASSWORD}")
        print(f"  Correos disponibles: {len(TEST_EMAILS)}")
        print()
        print("Servidor corriendo. Presiona Ctrl+C para detener.")
        print("-" * 60)
        
        while True:
            client_socket, address = server_socket.accept()
            handler = IMAPClientHandler(client_socket, address)
            # Manejar cada cliente en un thread separado
            client_thread = threading.Thread(target=handler.handle)
            client_thread.daemon = True
            client_thread.start()
    
    except KeyboardInterrupt:
        print("\n\n✓ Servidor detenido por el usuario")
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        server_socket.close()


def main():
    """Función principal."""
    print("=" * 60)
    print("Servidor IMAP de Prueba - Sistema de Alertas")
    print("=" * 60)
    print()
    
    # Actualizar configuración
    if update_config_file():
        print()
    
    # Iniciar servidor
    run_server()


if __name__ == "__main__":
    main()
