#!/bin/bash
# Script para detener el servicio

SERVICE_NAME="alertas-ph"

echo "Deteniendo servicio $SERVICE_NAME..."
sudo systemctl stop $SERVICE_NAME

# Esperar un momento
sleep 2

# Mostrar estado
sudo systemctl status $SERVICE_NAME --no-pager

echo ""
echo "Servicio detenido."