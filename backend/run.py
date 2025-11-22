"""
Script de inicio de la aplicación.
Punto de entrada simple que invoca el main.
"""

import sys
import argparse
from pathlib import Path

# Agregar src al path para imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.main import main
import asyncio


def parse_arguments():
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description='Sistema de Alertas de Email',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python run.py                    # Iniciar normalmente
  python run.py --version          # Mostrar versión
  
Para detener el servicio: Ctrl+C
        """
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Sistema de Alertas v1.0.0'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Ejecutar en modo debug (más logs)'
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    
    print("=" * 60)
    print("Sistema de Alertas de Email v1.0.0")
    print("=" * 60)
    print()
    
    if args.debug:
        print("Modo DEBUG activado")
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✓ Aplicación detenida por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error fatal: {e}")
        sys.exit(1)
