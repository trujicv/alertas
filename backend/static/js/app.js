// App.js - Lógica de la aplicación
class AlertApp {
    constructor() {
        this.emails = [];
        this.activities = [];
        this.config = null;
        this.currentFilter = 'todos';
        
        this.initializeEventListeners();
        this.setupWebSocketHandlers();
    }

    initializeEventListeners() {
        // Esperar a que el WebSocket se conecte
        window.addEventListener('ws:connected', () => {
            console.log('[App] WebSocket conectado, solicitando datos iniciales...');
            this.loadInitialData();
        });

        window.addEventListener('ws:disconnected', () => {
            console.log('[App] WebSocket desconectado');
            this.showNotification('Conexión perdida. Intentando reconectar...', 'warning');
        });

        // Botón de actualizar correos
        const refreshBtn = document.querySelector('.section-actions .btn-primary');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadEmails();
            });
        }

        // Filtros del buzón
        const filters = document.querySelectorAll('.mailbox-filters .filter');
        filters.forEach(filter => {
            filter.addEventListener('click', (e) => {
                filters.forEach(f => f.classList.remove('active'));
                e.target.classList.add('active');
                this.currentFilter = e.target.textContent.toLowerCase();
                this.filterEmails();
            });
        });

        // Botón guardar actividad
        const saveActivityBtn = document.getElementById('save-activity');
        if (saveActivityBtn) {
            saveActivityBtn.addEventListener('click', () => {
                this.saveActivity();
            });
        }

        // Formularios de configuración
        this.setupConfigForms();

        // Búsqueda de correos
        const searchBox = document.querySelector('.search-box');
        if (searchBox) {
            searchBox.addEventListener('input', (e) => {
                this.searchEmails(e.target.value);
            });
        }
    }

    setupWebSocketHandlers() {
        // Recibir nuevo correo en tiempo real
        window.addEventListener('ws:new_email', (event) => {
            console.log('[App] Nuevo correo recibido:', event.detail);
            this.handleNewEmail(event.detail);
        });

        // Recibir lista de correos
        window.addEventListener('ws:email_list', (event) => {
            console.log('[App] Lista de correos recibida:', event.detail);
            this.emails = event.detail.emails || event.detail || [];
            this.renderEmails();
            this.updateStats();
        });

        // Recibir lista de actividades
        window.addEventListener('ws:activities_list', (event) => {
            console.log('[App] Lista de actividades recibida:', event.detail);
            this.activities = event.detail.activities || event.detail || [];
            this.renderActivities();
            this.updateStats();
        });

        // Recibir configuración
        window.addEventListener('ws:config_data', (event) => {
            console.log('[App] Configuración recibida:', event.detail);
            this.config = event.detail;
            this.populateConfigForms();
        });

        // Confirmación de actividad agregada
        window.addEventListener('ws:activity_added', (event) => {
            console.log('[App] Actividad agregada:', event.detail);
            this.activities.push(event.detail);
            this.renderActivities();
            this.updateStats();
            this.showNotification('Actividad agregada correctamente', 'success');
            this.closeModal();
        });

        // Confirmación de actividad eliminada
        window.addEventListener('ws:activity_deleted', (event) => {
            console.log('[App] Actividad eliminada:', event.detail);
            const index = this.activities.findIndex(a => a.id === event.detail.activity_id);
            if (index > -1) {
                this.activities.splice(index, 1);
                this.renderActivities();
                this.updateStats();
            }
            this.showNotification('Actividad eliminada correctamente', 'success');
        });

        // Confirmación de configuración actualizada
        window.addEventListener('ws:config_updated', (event) => {
            console.log('[App] Configuración actualizada:', event.detail);
            this.config = event.detail;
            this.showNotification('Configuración guardada correctamente', 'success');
        });

        // Manejo de errores
        window.addEventListener('ws:error', (event) => {
            console.error('[App] Error del servidor:', event.detail);
            this.showNotification(event.detail.message || 'Error en el servidor', 'error');
        });
    }

    loadInitialData() {
        // Solicitar datos iniciales al servidor
        wsClient.sendMessage('get_emails');
        wsClient.sendMessage('get_activities');
        wsClient.sendMessage('get_config');
    }

    loadEmails() {
        wsClient.sendMessage('get_emails');
        this.showNotification('Actualizando correos...', 'info');
    }

    handleNewEmail(emailData) {
        // Agregar correo a la lista
        this.emails.unshift(emailData);
        
        // Actualizar UI
        this.renderEmails();
        this.updateStats();
        
        // Mostrar notificación
        this.showNotification(`Nuevo correo de ${emailData.from}`, 'info');
        
        // Reproducir sonido (opcional)
        this.playNotificationSound();
    }

    renderEmails() {
        // Renderizar lista completa en buzón
        const emailList = document.querySelector('.email-list');
        if (emailList && this.emails.length > 0) {
            emailList.innerHTML = this.emails.map(email => this.createEmailItem(email)).join('');
            
            // Agregar event listeners a los items
            emailList.querySelectorAll('.email-item').forEach((item, index) => {
                item.addEventListener('click', () => this.openEmail(this.emails[index]));
            });
        }

        // Renderizar últimos 3 correos en inicio
        const recentEmailsList = document.querySelector('.email-preview-list');
        if (recentEmailsList) {
            const recentEmails = this.emails.slice(0, 3);
            recentEmailsList.innerHTML = recentEmails.map(email => this.createEmailPreview(email)).join('');
        }
    }

    createEmailItem(email) {
        const unreadClass = email.unread ? 'unread' : '';
        const tagHtml = email.important ? '<span class="tag important">Importante</span>' : '';
        
        return `
            <div class="email-item ${unreadClass}" data-id="${email.id}">
                <div class="email-avatar">${this.getInitials(email.from)}</div>
                <div class="email-info">
                    <div class="email-row">
                        <strong>${this.extractName(email.from)}</strong>
                        <span>${this.formatDate(email.date)}</span>
                    </div>
                    <p class="subject">${email.subject}</p>
                    <p class="snippet">${this.getSnippet(email.body)}</p>
                </div>
                ${tagHtml}
            </div>
        `;
    }

    createEmailPreview(email) {
        const unreadClass = email.unread ? 'unread' : '';
        
        return `
            <div class="email-preview ${unreadClass}">
                <div class="email-avatar">${this.getInitials(email.from)}</div>
                <div class="email-content">
                    <div class="email-meta">
                        <strong>${this.extractName(email.from)}</strong>
                        <span>${this.formatDate(email.date)}</span>
                    </div>
                    <p class="email-subject">${email.subject}</p>
                    <p class="email-text">${this.getSnippet(email.body)}</p>
                </div>
            </div>
        `;
    }

    filterEmails() {
        let filtered = [...this.emails];
        
        if (this.currentFilter === 'no leídos') {
            filtered = filtered.filter(e => e.unread);
        } else if (this.currentFilter === 'importantes') {
            filtered = filtered.filter(e => e.important);
        }
        
        // Renderizar correos filtrados
        const emailList = document.querySelector('.email-list');
        if (emailList) {
            emailList.innerHTML = filtered.map(email => this.createEmailItem(email)).join('');
        }
    }

    searchEmails(query) {
        if (!query.trim()) {
            this.renderEmails();
            return;
        }

        const filtered = this.emails.filter(email => 
            email.subject.toLowerCase().includes(query.toLowerCase()) ||
            email.from.toLowerCase().includes(query.toLowerCase()) ||
            email.body.toLowerCase().includes(query.toLowerCase())
        );

        const emailList = document.querySelector('.email-list');
        if (emailList) {
            emailList.innerHTML = filtered.map(email => this.createEmailItem(email)).join('');
        }
    }

    openEmail(email) {
        // Marcar como leído
        if (email.unread) {
            wsClient.sendMessage('mark_read', { email_id: email.id });
            email.unread = false;
            this.renderEmails();
            this.updateStats();
        }
        
        // Mostrar modal o vista detallada (por implementar)
        console.log('[App] Abrir email:', email);
    }

    renderActivities() {
        const activityList = document.querySelector('.activity-list');
        if (activityList && this.activities.length > 0) {
            activityList.innerHTML = this.activities.map(activity => this.createActivityCard(activity)).join('');
            
            // Agregar botones de eliminar
            activityList.querySelectorAll('.activity-card').forEach((card, index) => {
                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'btn-icon btn-delete-activity';
                deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
                deleteBtn.style.cssText = 'position: absolute; top: 0.5rem; right: 0.5rem;';
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.deleteActivity(this.activities[index].id);
                });
                card.style.position = 'relative';
                card.appendChild(deleteBtn);
            });
        }
    }

    createActivityCard(activity) {
        const date = new Date(activity.scheduled_date);
        const day = date.getDate();
        const month = date.toLocaleString('es', { month: 'short' }).toUpperCase();
        
        return `
            <div class="activity-card" data-id="${activity.id}">
                <div class="activity-date">
                    <span class="day">${day}</span>
                    <span class="month">${month}</span>
                </div>
                <div class="activity-info">
                    <h4>${activity.title}</h4>
                    <p>${activity.description || 'Sin descripción'}</p>
                </div>
            </div>
        `;
    }

    saveActivity() {
        const title = document.getElementById('activity-title').value.trim();
        const description = document.getElementById('activity-desc').value.trim();
        const datetime = document.getElementById('activity-datetime').value;

        if (!title || !datetime) {
            this.showNotification('Por favor completa el título y la fecha', 'warning');
            return;
        }

        wsClient.sendMessage('add_activity', {
            title: title,
            description: description,
            scheduled_date: datetime
        });

        // Limpiar formulario
        document.getElementById('activity-title').value = '';
        document.getElementById('activity-desc').value = '';
        document.getElementById('activity-datetime').value = '';
    }

    deleteActivity(activityId) {
        if (confirm('¿Estás seguro de eliminar esta actividad?')) {
            wsClient.sendMessage('delete_activity', { activity_id: activityId });
        }
    }

    setupConfigForms() {
        // Formulario de configuración de email
        const emailForm = document.querySelector('.config-section:nth-child(1)');
        if (emailForm) {
            const saveBtn = document.createElement('button');
            saveBtn.className = 'btn-primary';
            saveBtn.innerHTML = '<i class="fas fa-save"></i> Guardar Configuración';
            saveBtn.style.marginTop = '1rem';
            saveBtn.addEventListener('click', () => this.saveEmailConfig());
            emailForm.querySelector('.form-fields').appendChild(saveBtn);
        }

        // Formulario de configuración del monitor
        const monitorForm = document.querySelector('.config-section:nth-child(2)');
        if (monitorForm) {
            const saveBtn = document.createElement('button');
            saveBtn.className = 'btn-primary';
            saveBtn.innerHTML = '<i class="fas fa-save"></i> Guardar Configuración';
            saveBtn.style.marginTop = '1rem';
            saveBtn.addEventListener('click', () => this.saveMonitorConfig());
            monitorForm.querySelector('.form-fields').appendChild(saveBtn);
        }
    }

    populateConfigForms() {
        if (!this.config) return;

        // Email config
        const emailConfig = this.config.email || {};
        this.setFieldValue('email-server', emailConfig.server);
        this.setFieldValue('email-port', emailConfig.port);
        this.setFieldValue('email-address', emailConfig.address);
        this.setFieldValue('email-password', emailConfig.password);
        this.setFieldValue('email-ssl', emailConfig.ssl);

        // Monitor config
        const monitorConfig = this.config.monitor || {};
        this.setFieldValue('check-interval', monitorConfig.check_interval);
        this.setFieldValue('idle-timeout', monitorConfig.idle_timeout);

        // Logging config
        const loggingConfig = this.config.logging || {};
        this.setFieldValue('log-level', loggingConfig.level);
    }

    saveEmailConfig() {
        const config = {
            server: this.getFieldValue('email-server'),
            port: parseInt(this.getFieldValue('email-port')),
            address: this.getFieldValue('email-address'),
            password: this.getFieldValue('email-password'),
            ssl: this.getFieldValue('email-ssl', 'checkbox')
        };

        wsClient.sendMessage('update_config', { email: config });
    }

    saveMonitorConfig() {
        const config = {
            check_interval: parseInt(this.getFieldValue('check-interval')),
            idle_timeout: parseInt(this.getFieldValue('idle-timeout'))
        };

        wsClient.sendMessage('update_config', { monitor: config });
    }

    updateStats() {
        // Actualizar contador de notificaciones
        const notifCount = this.emails.filter(e => e.unread).length;
        const notifStatBox = document.querySelector('.stat-box:nth-child(1) h3');
        if (notifStatBox) {
            notifStatBox.textContent = notifCount;
        }

        // Actualizar contador de actividades
        const activityStatBox = document.querySelector('.stat-box:nth-child(2) h3');
        if (activityStatBox) {
            activityStatBox.textContent = this.activities.length;
        }
    }

    // Utilidades
    getInitials(email) {
        const name = this.extractName(email);
        const parts = name.split(' ');
        if (parts.length >= 2) {
            return (parts[0][0] + parts[1][0]).toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    }

    extractName(email) {
        const match = email.match(/^([^<]+)/);
        return match ? match[1].trim() : email;
    }

    getSnippet(text, maxLength = 80) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays === 0) {
            return date.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' });
        } else if (diffDays === 1) {
            return 'Ayer';
        } else if (diffDays <= 7) {
            return `${diffDays} días`;
        } else {
            return date.toLocaleDateString('es');
        }
    }

    setFieldValue(id, value) {
        const field = document.getElementById(id);
        if (field) {
            if (field.type === 'checkbox') {
                field.checked = value;
            } else {
                field.value = value || '';
            }
        }
    }

    getFieldValue(id, type = 'text') {
        const field = document.getElementById(id);
        if (field) {
            return type === 'checkbox' ? field.checked : field.value;
        }
        return null;
    }

    closeModal() {
        const modal = document.getElementById('modal-activity');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    showNotification(message, type = 'info') {
        // Crear notificación toast (implementación simple)
        console.log(`[Notification ${type}]:`, message);
        
        // Podrías implementar un toast visual aquí
        // Por ahora solo lo mostramos en consola
    }

    playNotificationSound() {
        // Reproducir sonido de notificación (opcional)
        // const audio = new Audio('/static/sounds/notification.mp3');
        // audio.play().catch(e => console.log('No se pudo reproducir sonido'));
    }
}

// Inicializar la aplicación
const app = new AlertApp();
