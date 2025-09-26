/**
 * Sistema Básico de Verificación Arquitectónica
 * JavaScript principal para manejo de frontend
 */

// Sistema de logging detallado para F12
class FrontendLogger {
    constructor() {
        this.logLevel = 'DEBUG';
        this.sessionId = Math.random().toString(36).substr(2, 9);
        console.log(`🔧 FRONTEND LOGGER INICIADO - Sesión: ${this.sessionId}`);
    }

    debug(message, data = null) {
        const timestamp = new Date().toISOString();
        console.debug(`[${timestamp}] 🔍 DEBUG:`, message, data || '');
    }

    info(message, data = null) {
        const timestamp = new Date().toISOString();
        console.info(`[${timestamp}] ℹ️  INFO:`, message, data || '');
    }

    warn(message, data = null) {
        const timestamp = new Date().toISOString();
        console.warn(`[${timestamp}] ⚠️  WARN:`, message, data || '');
    }

    error(message, data = null) {
        const timestamp = new Date().toISOString();
        console.error(`[${timestamp}] ❌ ERROR:`, message, data || '');
    }

    api(method, url, data = null) {
        const timestamp = new Date().toISOString();
        console.group(`[${timestamp}] 🌐 API ${method.toUpperCase()}: ${url}`);
        if (data) console.log('📤 Enviando:', data);
        console.groupEnd();
    }

    apiResponse(status, data, duration) {
        const timestamp = new Date().toISOString();
        const icon = status >= 200 && status < 300 ? '✅' : '❌';
        console.group(`[${timestamp}] ${icon} RESPUESTA ${status} (${duration}ms)`);
        console.log('📥 Recibido:', data);
        console.groupEnd();
    }
}

const flog = new FrontendLogger();

class BasicoApp {
    constructor() {
        this.baseURL = '/basico';
        this.sessionId = null;
        this.uploadedFiles = {};
        this.projectConfig = {};
        
        flog.info('🚀 BasicoApp inicializado');
        
        // Configuración de zonas y grados
        this.zoneGrades = {
            'nz1': [1, 2, 3, 4, 5, 6],
            'nz2': [], // No tiene grados
            'nz3': [1, 2],
            'nz4': [], // No tiene grados
            'nz5': [1, 2, 3],
            'nz6': [], // No tiene grados
            'nz7': [1, 2, 3],
            'nz8': [1, 2, 3, 4, 5, 6],
            'nz9': [1, 2, 3, 4, 5]
        };
        
        this.init();
    }

    init() {
        this.setupFileUploads();
        this.setupFormHandlers();
        this.createSession();
    }

    async createSession() {
        try {
            const formData = new FormData();
            formData.append('project_name', `Proyecto ${new Date().toLocaleString()}`);
            
            const response = await fetch(`${this.baseURL}/session/create`, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                this.sessionId = data.session_id;
                console.log('Sesión creada:', this.sessionId);
            } else {
                throw new Error('Error creando sesión');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al crear sesión', 'danger');
        }
    }

    setupFileUploads() {
        const uploadAreas = document.querySelectorAll('.file-upload-area');
        
        uploadAreas.forEach(area => {
            const input = area.querySelector('input[type="file"]');
            const category = area.dataset.category;
            
            // Click para abrir selector
            area.addEventListener('click', () => input.click());
            
            // Drag & Drop
            area.addEventListener('dragover', (e) => {
                e.preventDefault();
                area.classList.add('dragover');
            });
            
            area.addEventListener('dragleave', () => {
                area.classList.remove('dragover');
            });
            
            area.addEventListener('drop', (e) => {
                e.preventDefault();
                area.classList.remove('dragover');
                this.handleFiles(e.dataTransfer.files, category);
            });
            
            // Input change
            input.addEventListener('change', (e) => {
                this.handleFiles(e.target.files, category);
            });
        });
    }

    handleFiles(files, category) {
        if (!files.length) return;
        
        // Validar PDFs
        const validFiles = Array.from(files).filter(file => {
            if (file.type !== 'application/pdf') {
                this.showAlert(`${file.name} no es un PDF válido`, 'warning');
                return false;
            }
            return true;
        });
        
        if (!validFiles.length) return;
        
        // Inicializar categoría si no existe
        if (!this.uploadedFiles[category]) {
            this.uploadedFiles[category] = [];
        }
        
        // Añadir archivos
        validFiles.forEach(file => {
            const fileId = `${category}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            this.uploadedFiles[category].push({
                id: fileId,
                file: file,
                name: file.name,
                size: file.size
            });
        });
        
        this.updateFileDisplay(category);
        this.checkPhase1Complete();
    }

    updateFileDisplay(category) {
        const container = document.querySelector(`[data-category="${category}"]`).closest('.card-body').querySelector('.uploaded-files');
        const files = this.uploadedFiles[category] || [];
        
        container.innerHTML = files.map(fileObj => `
            <div class="uploaded-file" data-file-id="${fileObj.id}">
                <i class="fas fa-file-pdf text-danger"></i>
                <span class="file-name">${fileObj.name}</span>
                <small class="text-muted">(${this.formatFileSize(fileObj.size)})</small>
                <button class="file-remove-btn" onclick="app.removeFile('${category}', '${fileObj.id}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');
    }

    removeFile(category, fileId) {
        if (this.uploadedFiles[category]) {
            this.uploadedFiles[category] = this.uploadedFiles[category].filter(f => f.id !== fileId);
            this.updateFileDisplay(category);
            this.checkPhase1Complete();
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    checkPhase1Complete() {
        // Verificar si hay al menos memoria (obligatorio)
        const hasMemoria = this.uploadedFiles.memoria && this.uploadedFiles.memoria.length > 0;
        const continueBtn = document.getElementById('continueToConfig');
        
        continueBtn.disabled = !hasMemoria;
        
        if (hasMemoria) {
            continueBtn.classList.add('btn-success');
            continueBtn.classList.remove('btn-primary');
        } else {
            continueBtn.classList.add('btn-primary');
            continueBtn.classList.remove('btn-success');
        }
    }

    setupFormHandlers() {
        // Continuar a configuración
        document.getElementById('continueToConfig').addEventListener('click', () => {
            this.uploadFiles().then(() => {
                this.showPhase2();
            });
        });

        // Cambio de zona para actualizar grados
        document.getElementById('zonaSelect').addEventListener('change', (e) => {
            this.updateGradeOptions(e.target.value);
            this.updateNormativePreview();
        });

        // Cambio de uso
        document.getElementById('usoSelect').addEventListener('change', () => {
            this.updateNormativePreview();
        });

        // Cambio de grado
        document.getElementById('gradoSelect').addEventListener('change', () => {
            this.updateNormativePreview();
        });

        // Guardar configuración
        document.getElementById('saveConfig').addEventListener('click', () => {
            this.saveConfiguration();
        });
    }

    async uploadFiles() {
        if (!this.sessionId) {
            throw new Error('No hay sesión activa');
        }

        try {
            const formData = new FormData();
            
            // Añadir todos los archivos
            Object.keys(this.uploadedFiles).forEach(category => {
                this.uploadedFiles[category].forEach(fileObj => {
                    formData.append('files', fileObj.file);
                });
            });

            const response = await fetch(`${this.baseURL}/session/${this.sessionId}/upload`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Archivos subidos:', result);
                this.showAlert(`${result.total_files} archivos subidos correctamente`, 'success');
            } else {
                throw new Error('Error subiendo archivos');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al subir archivos', 'danger');
            throw error;
        }
    }

    showPhase2() {
        document.getElementById('phase1').classList.remove('active');
        document.getElementById('phase2Container').style.display = 'block';
        document.getElementById('phase2').classList.add('active');
        
        // Scroll to phase 2
        document.getElementById('phase2').scrollIntoView({ behavior: 'smooth' });
    }

    updateGradeOptions(zona) {
        const gradoSelect = document.getElementById('gradoSelect');
        const grades = this.zoneGrades[zona] || [];
        
        // Limpiar opciones
        gradoSelect.innerHTML = '<option value="">Seleccionar grado...</option>';
        
        if (grades.length === 0) {
            gradoSelect.innerHTML = '<option value="">Esta zona no tiene grados</option>';
            gradoSelect.disabled = true;
        } else {
            gradoSelect.disabled = false;
            grades.forEach(grade => {
                gradoSelect.innerHTML += `<option value="${grade}">Grado ${grade}</option>`;
            });
        }
        
        this.checkConfigComplete();
    }

    async updateNormativePreview() {
        const uso = document.getElementById('usoSelect').value;
        const zona = document.getElementById('zonaSelect').value;
        const grado = document.getElementById('gradoSelect').value;
        
        flog.info('updateNormativePreview iniciado');
        flog.debug('Valores extraídos del formulario', { uso, zona, grado });
        
        if (!uso || !zona) {
            flog.warn('Faltan uso o zona requeridos');
            document.getElementById('normativePreview').style.display = 'none';
            return;
        }

        const config = {
            uso_principal: uso,
            norma_zonal: zona,
            grado: grado || 'basico',
            superficie_construida: 150, // Valor por defecto
            plantas: 2 // Valor por defecto
        };

        flog.api('POST', `${this.baseURL}/normatives/preview`, config);

        try {
            const startTime = performance.now();
            
            const response = await fetch(`${this.baseURL}/normatives/preview`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            const duration = Math.round(performance.now() - startTime);

            if (response.ok) {
                const data = await response.json();
                flog.apiResponse(response.status, data, duration);
                flog.info(`Total normativas recibidas: ${data.total_normatives}`);
                
                // Log detallado de cada normativa con más información
                data.normatives.forEach((norm, index) => {
                    const status = norm.file_exists ? '✅ EXISTE' : '❌ NO EXISTE';
                    flog.debug(`Normativa ${index + 1}: ${norm.name}`, {
                        status: status,
                        justification: norm.justification,
                        priority: norm.priority,
                        file_exists: norm.file_exists
                    });
                });
                
                this.displayNormativePreview(data);
            } else {
                const errorText = await response.text();
                flog.apiResponse(response.status, errorText, duration);
                flog.error('Error en respuesta del servidor', {
                    status: response.status,
                    statusText: response.statusText,
                    error: errorText
                });
            }
        } catch (error) {
            flog.error('Error en fetch de normativas', error);
        }
        
        this.checkConfigComplete();
    }

    displayNormativePreview(data) {
        const preview = document.getElementById('normativePreview');
        const list = document.getElementById('normativeList');
        
        if (data.total_normatives > 0) {
            list.innerHTML = `
                <p><strong>Total de normativas aplicables: ${data.total_normatives}</strong></p>
                <ul class="list-unstyled">
                    ${data.normatives.map(norm => `
                        <li class="mb-2">
                            <i class="fas fa-${norm.file_exists ? 'check-circle text-success' : 'exclamation-triangle text-warning'} me-2"></i>
                            <strong>${norm.name}</strong>
                            <br><small class="text-muted">${norm.justification}</small>
                        </li>
                    `).join('')}
                </ul>
            `;
            preview.style.display = 'block';
        } else {
            preview.style.display = 'none';
        }
    }

    checkConfigComplete() {
        const uso = document.getElementById('usoSelect').value;
        const zona = document.getElementById('zonaSelect').value;
        const saveBtn = document.getElementById('saveConfig');
        
        saveBtn.disabled = !uso || !zona;
    }

    async saveConfiguration() {
        const config = {
            uso_principal: document.getElementById('usoSelect').value,
            norma_zonal: document.getElementById('zonaSelect').value,
            grado: document.getElementById('gradoSelect').value || 'basico'
        };

        this.projectConfig = config;
        
        try {
            // Ejecutar Fase 2 (análisis de memoria)
            const response = await fetch(`${this.baseURL}/analyze/fase2/${this.sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Fase 2 completada:', result);
                this.showPhase3(result);
            } else {
                const errorText = await response.text();
                console.error('Error en Fase 2:', errorText);
                this.showAlert('Error en análisis de memoria. Continuando...', 'warning');
                this.showPhase3({ error: 'Análisis parcial' });
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error en configuración. Continuando...', 'warning');
            this.showPhase3({ error: 'Configuración parcial' });
        }
    }

    showPhase3(fase2Result) {
        document.getElementById('phase2').classList.remove('active');
        document.getElementById('phase3Container').style.display = 'block';
        document.getElementById('phase3').classList.add('active');
        
        // Mostrar información de la sesión
        const sessionInfo = document.getElementById('sessionInfo');
        sessionInfo.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Información de la Sesión:</h6>
                    <ul class="list-unstyled">
                        <li><strong>ID:</strong> ${this.sessionId}</li>
                        <li><strong>Uso:</strong> ${this.projectConfig.uso_principal}</li>
                        <li><strong>Zona:</strong> ${this.projectConfig.norma_zonal.toUpperCase()}</li>
                        <li><strong>Grado:</strong> ${this.projectConfig.grado}</li>
                        <li><strong>Archivos subidos:</strong> ${this.getTotalFiles()}</li>
                    </ul>
                </div>
                <div class="col-md-6">
                    <h6>Estado del Análisis:</h6>
                    <ul class="list-unstyled">
                        <li><i class="fas fa-check text-success me-2"></i>Fase 1: Documentos subidos</li>
                        <li><i class="fas fa-check text-success me-2"></i>Fase 2: Configuración guardada</li>
                        <li><i class="fas fa-play text-info me-2"></i>Fase 3: Lista para ejecutar</li>
                    </ul>
                </div>
            </div>
        `;
        
        // Scroll to phase 3
        document.getElementById('phase3').scrollIntoView({ behavior: 'smooth' });
        
        this.showAlert('Configuración guardada correctamente', 'success');
    }

    async executePhase3() {
        flog.info('🚀 Iniciando ejecución de Fase 3');
        
        const button = document.getElementById('executePhase3');
        const originalText = button.innerHTML;
        
        // Deshabilitar botón y mostrar loading
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Ejecutando verificación...';
        
        try {
            flog.api('POST', `${this.baseURL}/analyze/fase3/${this.sessionId}`);
            
            const startTime = performance.now();
            const response = await fetch(`${this.baseURL}/analyze/fase3/${this.sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const duration = Math.round(performance.now() - startTime);
            
            if (response.ok) {
                const result = await response.json();
                flog.apiResponse(response.status, result, duration);
                flog.info('✅ Fase 3 completada exitosamente');
                
                this.displayPhase3Results(result);
                this.updatePhase3Status('completed');
                
                this.showAlert('Verificación normativa completada exitosamente', 'success');
            } else {
                const errorText = await response.text();
                flog.apiResponse(response.status, errorText, duration);
                flog.error('❌ Error en Fase 3', { status: response.status, error: errorText });
                
                this.showAlert('Error en verificación normativa: ' + errorText, 'danger');
            }
        } catch (error) {
            flog.error('❌ Error de conexión en Fase 3', error);
            this.showAlert('Error de conexión durante la verificación', 'danger');
        } finally {
            // Restaurar botón
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }

    displayPhase3Results(result) {
        const resultsContainer = document.getElementById('phase3Results');
        
        let html = `
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="fas fa-clipboard-check me-2"></i>
                        Resultados de la Verificación Normativa
                    </h5>
                </div>
                <div class="card-body">
        `;
        
        if (result.normative_verification) {
            const verificacion = result.normative_verification;
            
            html += `
                <div class="row mb-4">
                    <div class="col-md-6">
                        <div class="alert alert-info">
                            <h6><i class="fas fa-chart-pie me-2"></i>Puntuación General</h6>
                            <h4 class="mb-0">${verificacion.puntuacion_cumplimiento || 'N/A'}/100</h4>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="alert alert-${(verificacion.puntuacion_cumplimiento || 0) >= 75 ? 'success' : 'warning'}">
                            <h6><i class="fas fa-${(verificacion.puntuacion_cumplimiento || 0) >= 75 ? 'check-circle' : 'exclamation-triangle'} me-2"></i>Estado General</h6>
                            <h5 class="mb-0">${(verificacion.puntuacion_cumplimiento || 0) >= 75 ? 'Cumple' : 'Requiere atención'}</h5>
                        </div>
                    </div>
                </div>
            `;
            
            if (verificacion.incumplimientos_detectados && verificacion.incumplimientos_detectados.length > 0) {
                html += `
                    <div class="alert alert-warning">
                        <h6><i class="fas fa-exclamation-triangle me-2"></i>Incumplimientos Detectados</h6>
                        <ul class="mb-0">
                `;
                
                verificacion.incumplimientos_detectados.forEach(incumplimiento => {
                    html += `
                        <li>
                            <strong>${incumplimiento.normativa || 'Normativa no especificada'}:</strong> 
                            ${incumplimiento.descripcion_incumplimiento || 'Descripción no disponible'}
                            ${incumplimiento.ubicacion_en_proyecto ? `<br><small class="text-muted">Ubicación: ${incumplimiento.ubicacion_en_proyecto}</small>` : ''}
                        </li>
                    `;
                });
                
                html += `
                        </ul>
                    </div>
                `;
            } else {
                html += `
                    <div class="alert alert-success">
                        <h6><i class="fas fa-check-circle me-2"></i>¡Excelente!</h6>
                        <p class="mb-0">No se detectaron incumplimientos normativos.</p>
                    </div>
                `;
            }
            
            if (verificacion.elementos_faltantes_verificados && verificacion.elementos_faltantes_verificados.length > 0) {
                html += `
                    <div class="alert alert-info">
                        <h6><i class="fas fa-info-circle me-2"></i>Elementos Faltantes</h6>
                        <ul class="mb-0">
                `;
                
                verificacion.elementos_faltantes_verificados.forEach(elemento => {
                    html += `<li>${elemento.elemento || elemento} (de ${elemento.normativa_origen || 'normativa'})</li>`;
                });
                
                html += `
                        </ul>
                    </div>
                `;
            }
            
            if (verificacion.observaciones_especificas && verificacion.observaciones_especificas.length > 0) {
                html += `
                    <div class="alert alert-light">
                        <h6><i class="fas fa-comment me-2"></i>Observaciones Específicas</h6>
                        <ul class="mb-0">
                `;
                
                verificacion.observaciones_especificas.forEach(obs => {
                    html += `<li>${obs}</li>`;
                });
                
                html += `
                        </ul>
                    </div>
                `;
            }
        } else {
            html += `
                <div class="alert alert-warning">
                    <h6><i class="fas fa-exclamation-triangle me-2"></i>Resultados Parciales</h6>
                    <p class="mb-0">Los resultados de la verificación no están completamente disponibles.</p>
                </div>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
        
        resultsContainer.innerHTML = html;
        resultsContainer.style.display = 'block';
        
        // Scroll to results
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }

    updatePhase3Status(status) {
        const statusElement = document.querySelector('#sessionInfo ul li:last-child');
        if (statusElement) {
            const icon = status === 'completed' ? 'fas fa-check text-success' : 'fas fa-play text-info';
            const text = status === 'completed' ? 'Fase 3: Completada' : 'Fase 3: Lista para ejecutar';
            statusElement.innerHTML = `<i class="${icon} me-2"></i>${text}`;
        }
    }

    getTotalFiles() {
        return Object.values(this.uploadedFiles).reduce((total, files) => total + files.length, 0);
    }

    showAlert(message, type = 'info') {
        // Crear alerta Bootstrap
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 1050; max-width: 400px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Inicializar aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.app = new BasicoApp();
});

// Funciones globales para uso en HTML
function removeFile(category, fileId) {
    if (window.app) {
        window.app.removeFile(category, fileId);
    }
}
