#!/bin/bash
# Script para ver el estado del servicio

SERVICE_NAME="alertas-ph"

echo "===================================="
echo "Estado del Servicio $SERVICE_NAME"
echo "===================================="
echo ""

sudo systemctl status $SERVICE_NAME --no-pager

echo ""
echo "===================================="
echo "Últimos logs"
echo "===================================="
echo ""

sudo journalctl -u $SERVICE_NAME -n 20 --no-pager

echo ""
echo "Para ver logs en tiempo real:"
echo "  sudo journalctl -u $SERVICE_NAME -f"