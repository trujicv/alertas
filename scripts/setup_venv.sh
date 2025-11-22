#!/bin/bash
# Script para configurar el entorno virtual de Python

set -e

echo "Configurando entorno virtual..."

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo "Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "Instalando dependencias..."
pip install -r backend/requirements.txt

echo "✓ Entorno virtual configurado correctamente"
echo ""
echo "Para activar el entorno virtual manualmente:"
echo "  source venv/bin/activate"
echo ""
echo "Para ejecutar la aplicación:"
echo "  python backend/run.py"