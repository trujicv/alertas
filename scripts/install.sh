#!/bin/bash
# Script de instalación del Sistema de Alertas de Email

set -e

echo "===================================="
echo "Instalación Sistema de Alertas"
echo "===================================="
echo ""

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: Este script debe ejecutarse como root (sudo)"
    exit 1
fi

# Variables
INSTALL_DIR="/opt/alertas"
SERVICE_NAME="alertas-ph"
SERVICE_USER="www-data"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Obtener el directorio actual (donde está el script)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Crear directorio de instalación
echo "[1/7] Creando directorio de instalación..."
mkdir -p $INSTALL_DIR

# Copiar archivos desde el directorio del proyecto
echo "Copiando archivos desde $PROJECT_DIR..."
cp -r "$PROJECT_DIR"/* $INSTALL_DIR/
cd $INSTALL_DIR

# Instalar dependencias del sistema
echo "[2/7] Instalando dependencias del sistema..."
apt-get update
apt-get install -y python3 python3-pip python3-venv

# Crear entorno virtual
echo "[3/7] Creando entorno virtual de Python..."
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias de Python
echo "[4/7] Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r $INSTALL_DIR/backend/requirements.txt

# Crear directorios necesarios
echo "[5/7] Creando estructura de directorios..."
mkdir -p $INSTALL_DIR/backend/data/logs
mkdir -p $INSTALL_DIR/backend/static/js
mkdir -p $INSTALL_DIR/backend/static/css

# Configurar permisos
echo "[6/7] Configurando permisos..."
chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
chmod -R 755 $INSTALL_DIR
chmod 644 $INSTALL_DIR/backend/data/config.json

# Instalar servicio systemd
echo "[7/7] Instalando servicio systemd..."
cp $INSTALL_DIR/alertas-ph.service $SERVICE_FILE
systemctl daemon-reload
systemctl enable $SERVICE_NAME

echo ""
echo "===================================="
echo "Instalación completada exitosamente"
echo "===================================="
echo ""
echo "Comandos disponibles:"
echo "  sudo systemctl start $SERVICE_NAME    - Iniciar servicio"
echo "  sudo systemctl stop $SERVICE_NAME     - Detener servicio"
echo "  sudo systemctl restart $SERVICE_NAME  - Reiniciar servicio"
echo "  sudo systemctl status $SERVICE_NAME   - Ver estado"
echo "  sudo journalctl -u $SERVICE_NAME -f   - Ver logs en tiempo real"
echo ""
echo "Interfaz web disponible en: http://$(hostname -I | awk '{print $1}'):8080"
echo "WebSocket disponible en: ws://$(hostname -I | awk '{print $1}'):8765"
echo ""
echo "IMPORTANTE: Configure el email desde la interfaz web antes de usar el sistema."
echo ""