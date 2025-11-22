# Sistema de Alertas de Email

Sistema de monitoreo de correo electrónico en tiempo real con interfaz web y notificaciones WebSocket.

## Características

- ✉️ Monitoreo IMAP en tiempo real
- 🔔 Notificaciones en tiempo real vía WebSocket
- 📊 Interfaz web moderna y responsive
- 📅 Calendario de actividades
- ⚙️ Configuración desde la interfaz web
- 🔒 Credenciales maestras para acceso
- 📝 Sistema de logs rotativo

## Requisitos

- Ubuntu 20.04+ (u otra distribución Linux con systemd)
- Python 3.8+
- Acceso root (sudo)

## Instalación en Ubuntu

### 1. Clonar o subir el proyecto al servidor

```bash
# Opción A: Clonar desde Git
git clone <tu-repositorio> /tmp/alertas
cd /tmp/alertas

# Opción B: Subir archivos mediante SCP
scp -r alertas/ usuario@servidor:/tmp/alertas
ssh usuario@servidor
cd /tmp/alertas
```

### 2. Ejecutar instalación

```bash
# Dar permisos de ejecución a los scripts
chmod +x scripts/*.sh

# Ejecutar instalador (requiere sudo)
sudo ./scripts/install.sh
```

El instalador realizará:
- Instalación de dependencias del sistema
- Creación del entorno virtual Python
- Instalación de dependencias Python
- Configuración de directorios y permisos
- Registro del servicio systemd

### 3. Configurar el servicio

La aplicación se instala en `/opt/alertas` y se configura como servicio systemd.

## Gestión del Servicio

### Iniciar el servicio
```bash
sudo systemctl start alertas-ph
# o usar el script
./scripts/start_service.sh
```

### Detener el servicio
```bash
sudo systemctl stop alertas-ph
# o usar el script
./scripts/stop_service.sh
```

### Reiniciar el servicio
```bash
sudo systemctl restart alertas-ph
```

### Ver estado
```bash
sudo systemctl status alertas-ph
# o usar el script
./scripts/status_service.sh
```

### Ver logs en tiempo real
```bash
sudo journalctl -u alertas-ph -f
```

### Ver logs históricos
```bash
# Últimas 100 líneas
sudo journalctl -u alertas-ph -n 100

# Logs desde hoy
sudo journalctl -u alertas-ph --since today

# Logs de las últimas 2 horas
sudo journalctl -u alertas-ph --since "2 hours ago"
```

## Acceso a la Interfaz Web

Una vez iniciado el servicio:

- **Interfaz Web**: `http://<ip-del-servidor>:8080`
- **WebSocket**: `ws://<ip-del-servidor>:8765`

Ejemplo:
- `http://192.168.1.100:8080`

## Configuración Inicial

### 1. Acceder a la interfaz web

Abrir navegador y navegar a `http://<ip-del-servidor>:8080`

### 2. Configurar credenciales de email

1. Ir a la pestaña **Configuración**
2. En la sección "Configuración de Email", completar:
   - **Servidor IMAP**: `imap.gmail.com` (para Gmail)
   - **Puerto**: `993`
   - **Dirección de email**: tu correo
   - **Contraseña**: contraseña de aplicación (ver abajo)
   - **Usar SSL**: ✓ Activado

3. Hacer clic en **Guardar Configuración**

### Obtener contraseña de aplicación de Gmail

1. Ir a: https://myaccount.google.com/security
2. Activar "Verificación en 2 pasos"
3. Ir a "Contraseñas de aplicaciones"
4. Generar una contraseña para "Correo"
5. Usar esa contraseña en la configuración

### 3. Verificar funcionamiento

Después de configurar:
- Envía un correo de prueba a la cuenta configurada
- Deberías ver una notificación en la interfaz web
- El correo aparecerá en la pestaña "Buzón"

## Estructura del Proyecto

```
alertas/
├── backend/
│   ├── data/
│   │   ├── config.json          # Configuración
│   │   ├── emails.json          # Correos guardados
│   │   ├── schedule.json        # Actividades
│   │   └── logs/                # Logs de la aplicación
│   ├── src/
│   │   ├── config_loader.py     # Cargador de configuración
│   │   ├── email_monitor.py     # Monitor IMAP
│   │   ├── websocket_server.py  # Servidor WebSocket
│   │   ├── http_server.py       # Servidor HTTP
│   │   ├── storage_manager.py   # Persistencia
│   │   ├── schedule_manager.py  # Gestor de actividades
│   │   └── main.py              # Orquestador principal
│   ├── static/
│   │   ├── index.html           # Interfaz web
│   │   ├── css/styles.css       # Estilos
│   │   └── js/
│   │       ├── websocket-client.js  # Cliente WebSocket
│   │       └── app.js               # Lógica de la app
│   ├── requirements.txt         # Dependencias Python
│   └── run.py                   # Punto de entrada
├── scripts/
│   ├── install.sh               # Instalador
│   ├── setup_venv.sh            # Configurar venv
│   ├── start_service.sh         # Iniciar servicio
│   ├── stop_service.sh          # Detener servicio
│   └── status_service.sh        # Ver estado
├── alertas-ph.service           # Archivo systemd
└── README.md                    # Este archivo
```

## Archivos de Configuración

### config.json

Ubicación: `/opt/alertas/backend/data/config.json`

```json
{
  "master_credentials": {
    "username": "admin",
    "password": "changeme123"
  },
  "email": {
    "server": "imap.gmail.com",
    "port": 993,
    "address": "",
    "password": "",
    "ssl": true
  },
  "websocket": {
    "host": "0.0.0.0",
    "port": 8765
  },
  "logging": {
    "level": "INFO",
    "max_file_size_mb": 10,
    "backup_count": 5
  },
  "monitor": {
    "check_interval": 30,
    "idle_timeout": 300
  }
}
```

**IMPORTANTE**: Cambiar `master_credentials` después de la instalación.

## Firewall

Si usas firewall (ufw, iptables), abre los puertos necesarios:

```bash
# Permitir puerto HTTP (interfaz web)
sudo ufw allow 8080/tcp

# Permitir puerto WebSocket
sudo ufw allow 8765/tcp

# Recargar firewall
sudo ufw reload
```

## Troubleshooting

### El servicio no inicia

```bash
# Ver logs detallados
sudo journalctl -u alertas-ph -n 50

# Verificar archivo de configuración
cat /opt/alertas/backend/data/config.json

# Probar ejecución manual
cd /opt/alertas
source venv/bin/activate
python backend/run.py
```

### No se conecta al servidor IMAP

- Verificar credenciales en config.json
- Para Gmail, verificar que la contraseña de aplicación sea correcta
- Verificar que el servidor y puerto sean correctos
- Ver logs: `sudo journalctl -u alertas-ph -f`

### La interfaz web no carga

```bash
# Verificar que el servicio está corriendo
sudo systemctl status alertas-ph

# Verificar que el puerto 8080 está escuchando
sudo netstat -tlnp | grep 8080

# Ver logs del servidor HTTP
sudo journalctl -u alertas-ph | grep "HTTP"
```

### WebSocket no conecta

```bash
# Verificar que el puerto 8765 está escuchando
sudo netstat -tlnp | grep 8765

# Ver logs de WebSocket
sudo journalctl -u alertas-ph | grep "WebSocket"
```

## Desarrollo Local

Para ejecutar localmente sin instalar como servicio:

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r backend/requirements.txt

# Ejecutar
python backend/run.py
```

## Actualización del Sistema

Para actualizar a una nueva versión:

```bash
# 1. Detener el servicio
sudo systemctl stop alertas-ph

# 2. Backup de configuración
sudo cp /opt/alertas/backend/data/config.json ~/config.json.backup
sudo cp /opt/alertas/backend/data/emails.json ~/emails.json.backup

# 3. Actualizar archivos
cd /tmp
# (descargar nueva versión)
sudo cp -r nueva-version/* /opt/alertas/

# 4. Restaurar configuración
sudo cp ~/config.json.backup /opt/alertas/backend/data/config.json

# 5. Actualizar dependencias
cd /opt/alertas
source venv/bin/activate
pip install -r backend/requirements.txt

# 6. Reiniciar servicio
sudo systemctl start alertas-ph
```

## Desinstalación

```bash
# Detener y deshabilitar servicio
sudo systemctl stop alertas-ph
sudo systemctl disable alertas-ph

# Eliminar archivo de servicio
sudo rm /etc/systemd/system/alertas-ph.service
sudo systemctl daemon-reload

# Eliminar archivos
sudo rm -rf /opt/alertas

# (Opcional) Eliminar usuario si fue creado específicamente
# sudo userdel alertas-user
```

## Soporte

Para reportar problemas o solicitar funcionalidades:
- Revisar logs: `sudo journalctl -u alertas-ph -f`
- Verificar configuración: `/opt/alertas/backend/data/config.json`
- Contactar al administrador del sistema

## Licencia

[Tu licencia aquí]
