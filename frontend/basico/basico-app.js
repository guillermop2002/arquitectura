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
        // Inicializar logger primero
        this.flog = new FrontendLogger();
        window.flog = this.flog; // Hacer disponible globalmente

        this.baseURL = '/basico';
        this.sessionId = null;
        this.uploadedFiles = {};
        this.projectConfig = {};

        this.flog.info('🚀 BasicoApp inicializado');
        
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
        this.flog.info('🚀 Inicializando BasicoApp...');
        try {
            this.setupFileUploads();
            this.setupFormHandlers();
            this.createSession();
            this.flog.info('✅ BasicoApp inicializada correctamente');
        } catch (error) {
            this.flog.error('❌ Error en inicialización:', error);
            throw error;
        }
    }

    async createSession() {
        try {
            flog.info('🔧 Iniciando creación de sesión');
            const formData = new FormData();
            formData.append('project_name', `Proyecto ${new Date().toLocaleString()}`);
            
            flog.api('POST', `${this.baseURL}/session/create`, formData);
            
            const startTime = Date.now();
            const response = await fetch(`${this.baseURL}/session/create`, {
                method: 'POST',
                body: formData
            });
            const duration = Date.now() - startTime;
            
            if (response.ok) {
                const data = await response.json();
                this.sessionId = data.session_id;
                flog.apiResponse(response.status, data, duration);
                flog.info(`✅ Sesión creada: ${this.sessionId}`);
                console.log('Sesión creada:', this.sessionId);
            } else {
                const errorText = await response.text();
                flog.apiResponse(response.status, errorText, duration);
                flog.error(`❌ Error creando sesión: ${response.status} - ${errorText}`);
                throw new Error(`Error creando sesión: ${response.status} - ${errorText}`);
            }
        } catch (error) {
            flog.error(`❌ Error en createSession: ${error.message}`);
            console.error('Error:', error);
            this.showAlert('Error al crear sesión', 'danger');
        }
    }

    setupFileUploads() {
        this.flog.info('🔧 Configurando file uploads...');
        const uploadAreas = document.querySelectorAll('.file-upload-area');
        this.flog.info(`📁 Encontradas ${uploadAreas.length} áreas de upload`);

        uploadAreas.forEach((area, index) => {
            const input = area.querySelector('input[type="file"]');
            const category = area.dataset.category;

            this.flog.debug(`📂 Configurando área ${index + 1}: categoría '${category}'`);

            if (!input) {
                this.flog.error(`❌ No se encontró input en área ${category}`);
                return;
            }

            // Click para abrir selector
            area.addEventListener('click', (e) => {
                this.flog.debug(`🖱️ Click en área ${category}`);
                e.stopPropagation();
                input.click();
            });

            // Drag & Drop
            area.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                area.classList.add('dragover');
                this.flog.debug(`🔄 Dragover en ${category}`);
            });

            area.addEventListener('dragleave', (e) => {
                e.preventDefault();
                e.stopPropagation();
                area.classList.remove('dragover');
                this.flog.debug(`↩️ Dragleave en ${category}`);
            });

            area.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                area.classList.remove('dragover');
                this.flog.info(`📥 Drop en ${category} con ${e.dataTransfer.files.length} archivos`);
                this.handleFiles(e.dataTransfer.files, category);
            });

            // Input change
            input.addEventListener('change', (e) => {
                this.flog.info(`📁 Input change en ${category} con ${e.target.files.length} archivos`);
                this.handleFiles(e.target.files, category);
            });

            this.flog.debug(`✅ Área ${category} configurada correctamente`);
        });

        this.flog.info('✅ File uploads configurados');
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

        // Iniciar análisis completo
        document.getElementById('startCompleteAnalysis').addEventListener('click', () => {
            this.startCompleteAnalysis();
        });
    }

    async uploadFiles() {
        if (!this.sessionId) {
            throw new Error('No hay sesión activa');
        }

        try {
            const formData = new FormData();
            let totalFiles = 0;
            
            // Añadir todos los archivos
            Object.keys(this.uploadedFiles).forEach(category => {
                this.uploadedFiles[category].forEach(fileObj => {
                    formData.append('files', fileObj.file);
                    totalFiles++;
                    flog.debug(`📄 Archivo: ${fileObj.file.name} (${fileObj.file.size} bytes)`);
                });
            });

            flog.info(`📊 Total de archivos a subir: ${totalFiles}`);
            flog.api('POST', `${this.baseURL}/session/${this.sessionId}/upload`, formData);

            const startTime = Date.now();
            const response = await fetch(`${this.baseURL}/session/${this.sessionId}/upload`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                flog.apiResponse(response.status, result, Date.now() - startTime);
                flog.info(`✅ Archivos subidos: ${result.total_files} archivos`);
                console.log('Archivos subidos:', result);
                this.showAlert(`${result.total_files} archivos subidos correctamente`, 'success');
            } else {
                const errorText = await response.text();
                flog.apiResponse(response.status, errorText, Date.now() - startTime);
                flog.error(`❌ Error subiendo archivos: ${response.status} - ${errorText}`);
                throw new Error(`Error subiendo archivos: ${response.status} - ${errorText}`);
            }
        } catch (error) {
            flog.error(`❌ Error en uploadFiles: ${error.message}`);
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
        const analyzeBtn = document.getElementById('startCompleteAnalysis');

        analyzeBtn.disabled = !uso || !zona;
    }

    async startCompleteAnalysis() {
        const config = {
            uso_principal: document.getElementById('usoSelect').value,
            norma_zonal: document.getElementById('zonaSelect').value,
            grado: document.getElementById('gradoSelect').value || 'basico'
        };

        flog.info(`🚀 Iniciando análisis completo: ${JSON.stringify(config)}`);
        this.projectConfig = config;
        
        // Mostrar spinner de análisis
        this.showAnalysisSpinner();

        try {
            // ANÁLISIS COMPLETO: Ejecutar todas las fases de una vez
            flog.api('POST', `${this.baseURL}/analyze/complete/${this.sessionId}`, config);

            const startTime = Date.now();
            const response = await fetch(`${this.baseURL}/analyze/complete/${this.sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config),
                timeout: 600000  // 10 minutos timeout
            });
            const duration = Date.now() - startTime;

            if (response.ok) {
                const result = await response.json();
                flog.apiResponse(response.status, result, duration);
                flog.info(`✅ Análisis completo terminado en ${duration/1000}s`);
                this.showCompleteResults(result);
            } else {
                const errorText = await response.text();
                flog.apiResponse(response.status, errorText, duration);
                flog.error(`❌ Error en análisis completo: ${response.status} - ${errorText}`);
                this.showAlert(`Error en análisis: ${response.status} - ${errorText}`, 'danger');
                this.hideAnalysisSpinner();
            }
        } catch (error) {
            flog.error(`❌ Error en análisis completo: ${error.message}`);
            this.showAlert(`Error en análisis: ${error.message}`, 'danger');
            this.hideAnalysisSpinner();
        }
    }

    showAnalysisSpinner() {
        // Ocultar fase 2 y mostrar spinner
        document.getElementById('phase2').classList.remove('active');
        document.getElementById('phase3Container').style.display = 'block';
        document.getElementById('phase3').classList.add('active');

        const resultsContainer = document.getElementById('resultsContainer');
        resultsContainer.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                    <span class="visually-hidden">Analizando...</span>
                </div>
                <h4>Analizando proyecto...</h4>
                <p class="text-muted">Este proceso puede tardar unos minutos. Por favor, espera.</p>
                <div class="progress mt-3" style="height: 10px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated"
                         role="progressbar" style="width: 100%"></div>
                </div>
                <small class="text-muted mt-2 d-block">
                    Ejecutando verificación de documentación, análisis de memoria y verificación normativa...
                </small>
            </div>
        `;

        // Scroll to results
        document.getElementById('phase3').scrollIntoView({ behavior: 'smooth' });
    }

    hideAnalysisSpinner() {
        // Solo ocultar el spinner, mantener el contenedor
        const resultsContainer = document.getElementById('resultsContainer');
        resultsContainer.innerHTML = '<div class="alert alert-danger">Error en el análisis. Por favor, inténtalo de nuevo.</div>';
    }

    showCompleteResults(results) {
        flog.info('📊 Mostrando resultados completos', results);

        const resultsContainer = document.getElementById('resultsContainer');

        // Extraer información de incumplimientos y anexo I
        const incumplimientos = this.extractIncumplimientos(results);
        const anexoI = this.extractAnexoI(results);
        const puntuacionFinal = results.final_score || 0;

        resultsContainer.innerHTML = `
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h5 class="mb-0">
                                <i class="fas fa-clipboard-check me-2"></i>
                                Resultados del Análisis Completo
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="row mb-4">
                                <div class="col-md-4">
                                    <h6>Información del Proyecto:</h6>
                                    <ul class="list-unstyled">
                                        <li><strong>Uso:</strong> ${this.projectConfig.uso_principal}</li>
                                        <li><strong>Zona:</strong> ${this.projectConfig.norma_zonal.toUpperCase()}</li>
                                        <li><strong>Archivos analizados:</strong> ${this.getTotalFiles()}</li>
                                    </ul>
                                </div>
                                <div class="col-md-4">
                                    <div class="text-center">
                                        <div class="display-4 ${puntuacionFinal >= 80 ? 'text-success' : puntuacionFinal >= 60 ? 'text-warning' : 'text-danger'}">
                                            ${puntuacionFinal}%
                                        </div>
                                        <p class="text-muted">Puntuación Final</p>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="text-center">
                                        <div class="display-6 ${anexoI.completitud >= 80 ? 'text-success' : anexoI.completitud >= 60 ? 'text-warning' : 'text-danger'}">
                                            ${anexoI.completitud}%
                                        </div>
                                        <p class="text-muted">Completitud Anexo I</p>
                                    </div>
                                </div>
                            </div>

                            ${this.renderAnexoI(anexoI)}
                            ${this.renderIncumplimientos(incumplimientos)}
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.showAlert('Análisis completado correctamente', 'success');
    }

    extractAnexoI(results) {
        const anexoI = {
            completitud: 0,
            elementos_faltantes: [],
            elementos_presentes: []
        };

        // Extraer de fase1
        if (results.fase1 && results.fase1.combined_results) {
            anexoI.completitud = results.fase1.combined_results.completion_percentage || 0;

            if (results.fase1.combined_results.missing_elements) {
                anexoI.elementos_faltantes = results.fase1.combined_results.missing_elements;
            }

            if (results.fase1.combined_results.present_elements) {
                anexoI.elementos_presentes = results.fase1.combined_results.present_elements;
            }
        }

        return anexoI;
    }

    renderAnexoI(anexoI) {
        if (!anexoI.elementos_faltantes || anexoI.elementos_faltantes.length === 0) {
            return `
                <div class="alert alert-success mb-4">
                    <h6><i class="fas fa-check-circle me-2"></i>Documentación Completa (Anexo I)</h6>
                    <p class="mb-0">Todos los elementos requeridos del Anexo I están presentes en el proyecto.</p>
                </div>
            `;
        }

        return `
            <div class="alert alert-warning mb-4">
                <h6><i class="fas fa-exclamation-triangle me-2"></i>Elementos Faltantes del Anexo I (${anexoI.elementos_faltantes.length})</h6>
            </div>
            <div class="table-responsive mb-4">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Elemento Faltante</th>
                            <th>Categoría</th>
                            <th>Descripción</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${anexoI.elementos_faltantes.map((elemento, index) => `
                            <tr>
                                <td>
                                    <strong>${elemento.nombre || elemento.element || elemento}</strong>
                                </td>
                                <td>
                                    <span class="badge bg-info">${elemento.categoria || elemento.category || 'General'}</span>
                                </td>
                                <td>
                                    <small class="text-muted">${elemento.descripcion || elemento.description || 'Elemento requerido por Anexo I'}</small>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    extractIncumplimientos(results) {
        const incumplimientos = [];

        // Extraer de verificación normativa
        if (results.normative_verification && results.normative_verification.incumplimientos) {
            incumplimientos.push(...results.normative_verification.incumplimientos);
        }

        // Extraer de verificación CTE
        if (results.cte_verification && results.cte_verification.incumplimientos) {
            incumplimientos.push(...results.cte_verification.incumplimientos);
        }

        // Extraer de verificación PGOUM
        if (results.pgoum_verification && results.pgoum_verification.incumplimientos) {
            incumplimientos.push(...results.pgoum_verification.incumplimientos);
        }

        return incumplimientos;
    }

    renderIncumplimientos(incumplimientos) {
        if (!incumplimientos || incumplimientos.length === 0) {
            return `
                <div class="alert alert-success">
                    <h6><i class="fas fa-check-circle me-2"></i>¡Proyecto Conforme!</h6>
                    <p class="mb-0">No se han detectado incumplimientos normativos en el proyecto analizado.</p>
                </div>
            `;
        }

        return `
            <div class="alert alert-warning">
                <h6><i class="fas fa-exclamation-triangle me-2"></i>Incumplimientos Detectados (${incumplimientos.length})</h6>
            </div>
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Descripción</th>
                            <th>Normativa</th>
                            <th>Página Normativa</th>
                            <th>Documento Proyecto</th>
                            <th>Página Proyecto</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${incumplimientos.map((inc, index) => `
                            <tr>
                                <td>
                                    <strong>${inc.descripcion || 'Incumplimiento detectado'}</strong>
                                    ${inc.detalle ? `<br><small class="text-muted">${inc.detalle}</small>` : ''}
                                </td>
                                <td>
                                    <span class="badge bg-primary">${inc.normativa || 'N/A'}</span>
                                </td>
                                <td>
                                    ${inc.pagina_normativa ? `<span class="badge bg-info">Pág. ${inc.pagina_normativa}</span>` : 'N/A'}
                                </td>
                                <td>
                                    <span class="badge bg-secondary">${inc.documento_proyecto || 'N/A'}</span>
                                </td>
                                <td>
                                    ${inc.pagina_proyecto ? `<span class="badge bg-info">Pág. ${inc.pagina_proyecto}</span>` : 'N/A'}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    // Funciones obsoletas eliminadas - ahora se usa startCompleteAnalysis() y showCompleteResults()

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

// Inicialización movida al HTML para mejor control

// Funciones globales para uso en HTML
function removeFile(category, fileId) {
    if (window.app) {
        window.app.removeFile(category, fileId);
    }
}
