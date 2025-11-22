// WebSocket Client - Capa de comunicación con el servidor
class WebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectInterval = 3000;
        this.reconnectTimer = null;
        this.isConnecting = false;
        this.messageHandlers = new Map();
        
        // Configuración del WebSocket desde config
        this.host = window.location.hostname || 'localhost';
        this.port = 8765;
        this.url = `ws://${this.host}:${this.port}`;
    }

    connect() {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
            return;
        }

        this.isConnecting = true;
        console.log(`[WebSocket] Conectando a ${this.url}...`);

        try {
            this.ws = new WebSocket(this.url);
            
            this.ws.onopen = () => this.handleOpen();
            this.ws.onmessage = (event) => this.handleMessage(event);
            this.ws.onerror = (error) => this.handleError(error);
            this.ws.onclose = (event) => this.handleClose(event);
        } catch (error) {
            console.error('[WebSocket] Error al crear conexión:', error);
            this.isConnecting = false;
            this.scheduleReconnect();
        }
    }

    handleOpen() {
        console.log('[WebSocket] Conectado exitosamente');
        this.isConnecting = false;
        
        // Limpiar timer de reconexión
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        // Actualizar estado visual
        this.updateConnectionStatus(true);
        
        // Disparar evento de conexión
        this.dispatchEvent('ws:connected');
    }

    handleMessage(event) {
        try {
            const message = JSON.parse(event.data);
            console.log('[WebSocket] Mensaje recibido:', message);

            // Disparar evento específico según el tipo de mensaje
            if (message.type) {
                this.dispatchEvent(`ws:${message.type}`, message.data || message);
            }

            // Llamar handlers registrados
            if (this.messageHandlers.has(message.type)) {
                const handlers = this.messageHandlers.get(message.type);
                handlers.forEach(handler => handler(message.data || message));
            }
        } catch (error) {
            console.error('[WebSocket] Error al procesar mensaje:', error);
        }
    }

    handleError(error) {
        console.error('[WebSocket] Error de conexión:', error);
        this.updateConnectionStatus(false);
    }

    handleClose(event) {
        console.log('[WebSocket] Conexión cerrada:', event.code, event.reason);
        this.isConnecting = false;
        this.updateConnectionStatus(false);
        
        // Disparar evento de desconexión
        this.dispatchEvent('ws:disconnected');
        
        // Intentar reconectar
        this.scheduleReconnect();
    }

    scheduleReconnect() {
        if (this.reconnectTimer) {
            return;
        }

        console.log(`[WebSocket] Reintentando conexión en ${this.reconnectInterval/1000}s...`);
        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
        }, this.reconnectInterval);
    }

    sendMessage(type, data = {}) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.warn('[WebSocket] No se puede enviar mensaje, no hay conexión');
            return false;
        }

        const message = {
            type: type,
            data: data,
            timestamp: new Date().toISOString()
        };

        try {
            this.ws.send(JSON.stringify(message));
            console.log('[WebSocket] Mensaje enviado:', message);
            return true;
        } catch (error) {
            console.error('[WebSocket] Error al enviar mensaje:', error);
            return false;
        }
    }

    on(messageType, handler) {
        if (!this.messageHandlers.has(messageType)) {
            this.messageHandlers.set(messageType, []);
        }
        this.messageHandlers.get(messageType).push(handler);
    }

    off(messageType, handler) {
        if (this.messageHandlers.has(messageType)) {
            const handlers = this.messageHandlers.get(messageType);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    dispatchEvent(eventName, detail = null) {
        const event = new CustomEvent(eventName, { detail });
        window.dispatchEvent(event);
    }

    updateConnectionStatus(isConnected) {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.header-status span:last-child');
        
        if (statusDot) {
            if (isConnected) {
                statusDot.style.background = 'var(--success)';
            } else {
                statusDot.style.background = 'var(--danger)';
            }
        }
        
        if (statusText) {
            statusText.textContent = isConnected ? 'Conectado' : 'Desconectado';
        }
    }

    disconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Crear instancia global
const wsClient = new WebSocketClient();

// Auto-conectar cuando se carga el script
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        wsClient.connect();
    });
} else {
    wsClient.connect();
}
