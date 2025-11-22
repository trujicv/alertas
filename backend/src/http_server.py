"""
Servidor HTTP simple para servir la interfaz web.
"""

import asyncio
import logging
from pathlib import Path
from aiohttp import web
from typing import Optional


class HTTPServer:
    """Servidor HTTP para la interfaz web."""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        """
        Inicializa el servidor HTTP.
        
        Args:
            host: Host donde escuchar
            port: Puerto donde escuchar
        """
        self.logger = logging.getLogger(__name__)
        self.host = host
        self.port = port
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.static_dir = Path(__file__).parent.parent / "static"
    
    async def start(self) -> None:
        """Inicia el servidor HTTP."""
        try:
            self.app = web.Application()
            
            # Ruta raíz - servir index.html
            self.app.router.add_get('/', self._handle_index)
            
            # Rutas para archivos estáticos (solo si existen)
            css_dir = self.static_dir / 'css'
            if css_dir.exists():
                self.app.router.add_static('/css', css_dir, name='css')
            
            js_dir = self.static_dir / 'js'
            if js_dir.exists():
                self.app.router.add_static('/js', js_dir, name='js')
            
            fonts_dir = self.static_dir / 'fonts'
            if fonts_dir.exists():
                self.app.router.add_static('/fonts', fonts_dir, name='fonts', show_index=False)
            
            images_dir = self.static_dir / 'images'
            if images_dir.exists():
                self.app.router.add_static('/images', images_dir, name='images', show_index=False)
            
            # Iniciar servidor
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()
            
            self.logger.info(f"Servidor HTTP iniciado en http://{self.host}:{self.port}")
            
        except Exception as e:
            self.logger.error(f"Error al iniciar servidor HTTP: {e}")
            raise
    
    async def stop(self) -> None:
        """Detiene el servidor HTTP."""
        try:
            if self.site:
                await self.site.stop()
            
            if self.runner:
                await self.runner.cleanup()
            
            self.logger.info("Servidor HTTP detenido")
            
        except Exception as e:
            self.logger.error(f"Error al detener servidor HTTP: {e}")
    
    async def _handle_index(self, request: web.Request) -> web.Response:
        """Maneja la solicitud de la página principal."""
        try:
            index_file = self.static_dir / "index.html"
            
            if not index_file.exists():
                return web.Response(text="index.html no encontrado", status=404)
            
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return web.Response(text=content, content_type='text/html')
            
        except Exception as e:
            self.logger.error(f"Error sirviendo index.html: {e}")
            return web.Response(text="Error interno del servidor", status=500)
