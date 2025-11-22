#!/bin/bash
# Script para iniciar el servicio

SERVICE_NAME="alertas-ph"

echo "Iniciando servicio $SERVICE_NAME..."
sudo systemctl start $SERVICE_NAME

# Esperar un momento
sleep 2

# Mostrar estado
sudo systemctl status $SERVICE_NAME --no-pager

echo ""
echo "Para ver los logs en tiempo real:"
echo "  sudo journalctl -u $SERVICE_NAME -f"