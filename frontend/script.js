// Sistema de Verificación Arquitectónica Madrid - Frontend JavaScript

class MadridVerificationSystem {
    constructor() {
        this.currentStep = 0; // 0 = mostrar todos los pasos
        this.maxSteps = 7; // 7 pasos: Info → Subida → Clasificación → Normativa → Análisis → Chatbot → Checklist
        this.projectData = {
            is_existing_building: false,
            primary_use: null,
            has_secondary_uses: false,
            secondary_uses: [],
            secondary_uses_floors: {},
            memoria_files: [],
            planos_files: [],
            jobId: null
        };
        this.chatbotSession = null;
        this.ambiguities = [];
        this.resolvedAmbiguities = [];
        this.init();
    }

    init() {
        console.log('🚀 Inicializando MadridVerificationSystem...');
        console.log('📊 currentStep:', this.currentStep);
        console.log('📊 maxSteps:', this.maxSteps);
        
        // Esperar a que el DOM esté listo
        if (document.readyState === 'loading') {
            console.log('⏳ Esperando que el DOM se cargue...');
            document.addEventListener('DOMContentLoaded', () => {
                console.log('✅ DOM cargado, inicializando sistema...');
                this.setupEventListeners();
                this.updateStepVisibility();
                this.updateNavigationButtons();
                console.log('🎯 Sistema inicializado completamente');
            });
        } else {
            console.log('✅ DOM ya cargado, inicializando sistema...');
            this.setupEventListeners();
            this.updateStepVisibility();
            this.updateNavigationButtons();
            console.log('🎯 Sistema inicializado completamente');
        }
    }

    setupEventListeners() {
        console.log('🔧 Configurando event listeners...');

        // Building type toggle
        const buildingToggle = document.getElementById('isExistingBuilding');
        console.log('🏗️ Building toggle encontrado:', !!buildingToggle);
        if (buildingToggle) {
            buildingToggle.addEventListener('change', () => {
                console.log('🏗️ Building type changed:', buildingToggle.checked);
                this.toggleBuildingType();
            });
        }

        // Primary use selector
        const primaryUse = document.getElementById('primaryUse');
        if (primaryUse) {
            primaryUse.addEventListener('change', () => {
                console.log('Primary use changed:', primaryUse.value);
                this.updatePrimaryUse();
            });
        }

        // Secondary uses toggle
        const secondaryToggle = document.getElementById('hasSecondaryUses');
        if (secondaryToggle) {
            secondaryToggle.addEventListener('change', () => {
                console.log('Secondary uses toggle changed:', secondaryToggle.checked);
                this.toggleSecondaryUses();
            });
        }

        // Secondary use checkboxes
        document.addEventListener('change', (e) => {
            if (e.target.id && e.target.id.startsWith('sec_')) {
                const useType = e.target.value;
                console.log('Secondary use changed:', useType, e.target.checked);
                this.toggleSecondaryUse(useType);
            }
        });

        // Memoria input change
        const memoriaInput = document.getElementById('memoriaInput');
        console.log('📄 Memoria input encontrado:', !!memoriaInput);
        if (memoriaInput) {
            memoriaInput.addEventListener('change', (e) => {
                console.log('📄 Memoria seleccionada:', e.target.files);
                this.handleMemoriaSelection(e.target.files);
            });
        }

        // Planos input change
        const planosInput = document.getElementById('planosInput');
        console.log('📐 Planos input encontrado:', !!planosInput);
        if (planosInput) {
            planosInput.addEventListener('change', (e) => {
                console.log('📐 Planos seleccionados:', e.target.files);
                this.handlePlanosSelection(e.target.files);
            });
        }

        // Drag and drop for Memoria
        const memoriaUploadArea = document.getElementById('memoriaUploadArea');
        console.log('📄 Memoria upload area encontrada:', !!memoriaUploadArea);
        if (memoriaUploadArea) {
            memoriaUploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                memoriaUploadArea.classList.add('dragover');
                console.log('Memoria drag over');
            });

            memoriaUploadArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                memoriaUploadArea.classList.remove('dragover');
                console.log('Memoria drag leave');
            });

            memoriaUploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                memoriaUploadArea.classList.remove('dragover');
                console.log('Memoria files dropped:', e.dataTransfer.files);
                this.handleMemoriaSelection(e.dataTransfer.files);
            });

            // Click to select memoria
            memoriaUploadArea.addEventListener('click', () => {
                console.log('Memoria upload area clicked');
                const memoriaInput = document.getElementById('memoriaInput');
                if (memoriaInput) {
                    memoriaInput.click();
                }
            });
        }

        // Drag and drop for Planos
        const planosUploadArea = document.getElementById('planosUploadArea');
        if (planosUploadArea) {
            planosUploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                planosUploadArea.classList.add('dragover');
                console.log('Planos drag over');
            });

            planosUploadArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                planosUploadArea.classList.remove('dragover');
                console.log('Planos drag leave');
            });

            planosUploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                planosUploadArea.classList.remove('dragover');
                console.log('Planos files dropped:', e.dataTransfer.files);
                this.handlePlanosSelection(e.dataTransfer.files);
            });

            // Click to select planos
            planosUploadArea.addEventListener('click', () => {
                console.log('Planos upload area clicked');
                const planosInput = document.getElementById('planosInput');
                if (planosInput) {
                    planosInput.click();
                }
            });
        }

        // Navigation buttons
        const prevBtn = document.getElementById('prevBtn');
        if (prevBtn) {
            console.log('Configurando botón anterior...');
            prevBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Botón anterior clickeado');
                this.changeStep(-1);
            });
        }

        const nextBtn = document.getElementById('nextBtn');
        if (nextBtn) {
            console.log('Configurando botón siguiente...');
            nextBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Botón siguiente clickeado');
                this.changeStep(1);
            });
        }

        // Start verification button
        const startButton = document.getElementById('startVerification');
        if (startButton) {
            startButton.addEventListener('click', () => {
                this.startMadridVerification();
            });
        }
        
        console.log('✅ Todos los event listeners configurados correctamente');

        // New verification button
        const newVerificationButton = document.getElementById('newVerification');
        if (newVerificationButton) {
            newVerificationButton.addEventListener('click', () => {
                this.startNewVerification();
            });
        }

        // Chatbot input
        const chatbotInput = document.getElementById('chatbotInput');
        if (chatbotInput) {
            chatbotInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendChatbotMessage();
                }
            });
        }

        // Send message button
        const sendMessageBtn = document.getElementById('sendMessageBtn');
        if (sendMessageBtn) {
            sendMessageBtn.addEventListener('click', () => {
                this.sendChatbotMessage();
            });
        }

        // Document classification button
        const classifyDocumentsBtn = document.getElementById('classifyDocumentsBtn');
        if (classifyDocumentsBtn) {
            classifyDocumentsBtn.addEventListener('click', () => {
                this.classifyDocuments();
            });
        }

        // Normative application button
        const applyNormativeBtn = document.getElementById('applyNormativeBtn');
        if (applyNormativeBtn) {
            applyNormativeBtn.addEventListener('click', () => {
                this.applyNormative();
            });
        }

        // Document analysis button
        const analyzeDocumentsBtn = document.getElementById('analyzeDocumentsBtn');
        if (analyzeDocumentsBtn) {
            analyzeDocumentsBtn.addEventListener('click', () => {
                this.analyzeDocuments();
            });
        }

        // Final checklist button
        const generateFinalChecklistBtn = document.getElementById('generateFinalChecklistBtn');
        if (generateFinalChecklistBtn) {
            generateFinalChecklistBtn.addEventListener('click', () => {
                this.generateFinalChecklist();
            });
        }
    }

    toggleBuildingType() {
        this.projectData.is_existing_building = document.getElementById('isExistingBuilding').checked;
        console.log('Building type:', this.projectData.is_existing_building);
        this.updateNavigationButtons();
    }

    updatePrimaryUse() {
        this.projectData.primary_use = document.getElementById('primaryUse').value;
        console.log('Primary use:', this.projectData.primary_use);
        this.updateNavigationButtons();
    }

    toggleSecondaryUses() {
        this.projectData.has_secondary_uses = document.getElementById('hasSecondaryUses').checked;
        const section = document.getElementById('secondaryUsesSection');
        
        console.log('Secondary uses toggle:', this.projectData.has_secondary_uses);
        
        if (this.projectData.has_secondary_uses) {
            section.classList.remove('d-none');
            console.log('Showing secondary uses section');
        } else {
            section.classList.add('d-none');
            // Clear secondary uses
            this.projectData.secondary_uses = [];
            this.projectData.secondary_uses_floors = {};
            document.getElementById('secondaryUsesFloors').innerHTML = '';
            console.log('Hiding secondary uses section');
        }
        
        this.updateNavigationButtons();
    }

    toggleSecondaryUse(useType) {
        const checkbox = document.getElementById(`sec_${useType.replace('-', '_')}`);
        const isChecked = checkbox.checked;
        
        console.log('Toggling secondary use:', useType, isChecked);
        
        if (isChecked) {
            // Add to secondary uses
            this.projectData.secondary_uses.push({
                use_type: useType,
                floors: []
            });
            this.createFloorSelector(useType);
        } else {
            // Remove from secondary uses
            this.projectData.secondary_uses = this.projectData.secondary_uses.filter(use => use.use_type !== useType);
            this.removeFloorSelector(useType);
        }
        
        this.updateNavigationButtons();
    }

    createFloorSelector(useType) {
        const container = document.getElementById('secondaryUsesFloors');
        const floorSelector = document.createElement('div');
        floorSelector.id = `floor_selector_${useType.replace('-', '_')}`;
        floorSelector.className = 'mb-3';
        
        const floors = this.generateFloorOptions();
        floorSelector.innerHTML = `
            <label class="form-label fw-bold">Plantas para ${useType}:</label>
            <select class="form-select" id="floors_${useType.replace('-', '_')}" multiple>
                ${floors.map(floor => `<option value="${floor}">${floor}</option>`).join('')}
            </select>
            <small class="form-text text-muted">Selecciona las plantas donde se encuentra este uso secundario</small>
        `;
        
        container.appendChild(floorSelector);
        
        // Add event listener for floor selection
        const floorSelect = document.getElementById(`floors_${useType.replace('-', '_')}`);
        floorSelect.addEventListener('change', () => {
            const selectedFloors = Array.from(floorSelect.selectedOptions).map(option => option.value);
            this.updateSecondaryUseFloors(useType, selectedFloors);
        });
    }

    removeFloorSelector(useType) {
        const floorSelector = document.getElementById(`floor_selector_${useType.replace('-', '_')}`);
        if (floorSelector) {
            floorSelector.remove();
        }
        delete this.projectData.secondary_uses_floors[useType];
    }

    generateFloorOptions() {
        const floors = [];
        // Generar plantas de -100 a 100
        for (let i = -100; i <= 100; i++) {
            if (i === 0) {
                floors.push('Planta Baja');
            } else if (i > 0) {
                floors.push(`Planta ${i}`);
        } else {
                floors.push(`Sótano ${Math.abs(i)}`);
            }
        }
        floors.push('Entreplanta');
        floors.push('Entresótano');
        return floors;
    }

    updateSecondaryUseFloors(useType, floors) {
        this.projectData.secondary_uses_floors[useType] = floors;
        
        // Actualizar también el array secondary_uses
        const secondaryUse = this.projectData.secondary_uses.find(use => use.use_type === useType);
        if (secondaryUse) {
            secondaryUse.floors = floors;
        }
        
        console.log('Updated floors for', useType, ':', floors);
        console.log('Updated secondary_uses:', this.projectData.secondary_uses);
    }

    handleMemoriaSelection(files) {
        console.log('Handling memoria selection:', files);
        
        const fileArray = Array.from(files).filter(file => file.type === 'application/pdf');
        
        if (fileArray.length === 0) {
            this.showAlert('Por favor, selecciona solo archivos PDF para la memoria.', 'warning');
            return;
        }
        
        // Solo permitir un archivo de memoria
        if (fileArray.length > 1) {
            this.showAlert('Solo se permite un archivo de memoria descriptiva.', 'warning');
            return;
        }
        
        this.projectData.memoria_files = fileArray;
        this.displayMemoriaFileList();
        this.updateNavigationButtons();
    }

    handlePlanosSelection(files) {
        console.log('Handling planos selection:', files);
        
        const fileArray = Array.from(files).filter(file => file.type === 'application/pdf');
        
        if (fileArray.length === 0) {
            this.showAlert('Por favor, selecciona solo archivos PDF para los planos.', 'warning');
            return;
        }

        this.projectData.planos_files = fileArray;
        this.displayPlanosFileList();
        this.updateNavigationButtons();
    }

    displayMemoriaFileList() {
        const fileList = document.getElementById('memoriaFileList');
        fileList.innerHTML = '';

        this.projectData.memoria_files.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item memoria-file';
            fileItem.innerHTML = `
                <i class="fas fa-file-pdf file-icon"></i>
                <div class="file-info">
                    <div class="fw-bold">${file.name}</div>
                    <small class="text-muted">${this.formatFileSize(file.size)}</small>
                </div>
                <div class="file-actions">
                    <button class="btn btn-sm btn-outline-danger" onclick="madridSystem.removeMemoriaFile(${index})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            fileList.appendChild(fileItem);
        });
    }

    displayPlanosFileList() {
        const fileList = document.getElementById('planosFileList');
        fileList.innerHTML = '';

        this.projectData.planos_files.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item planos-file';
            fileItem.innerHTML = `
                <i class="fas fa-file-pdf file-icon"></i>
                <div class="file-info">
                    <div class="fw-bold">${file.name}</div>
                    <small class="text-muted">${this.formatFileSize(file.size)}</small>
                </div>
                <div class="file-actions">
                    <button class="btn btn-sm btn-outline-danger" onclick="madridSystem.removePlanosFile(${index})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            fileList.appendChild(fileItem);
        });
    }

    removeMemoriaFile(index) {
        this.projectData.memoria_files.splice(index, 1);
        this.displayMemoriaFileList();
        this.updateNavigationButtons();
    }

    removePlanosFile(index) {
        this.projectData.planos_files.splice(index, 1);
        this.displayPlanosFileList();
        this.updateNavigationButtons();
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    nextStep() {
            if (this.validateCurrentStep()) {
            if (this.currentStep < this.maxSteps) {
                this.currentStep++;
                this.updateStepVisibility();
                this.updateNavigationButtons();
            }
        }
        }

    previousStep() {
        if (this.currentStep > 1) {
            this.currentStep--;
        this.updateStepVisibility();
        this.updateNavigationButtons();
        }
    }

    changeStep(direction) {
        console.log('changeStep llamado con dirección:', direction);
        const newStep = this.currentStep + direction;
        
        if (newStep < 1 || newStep > this.maxSteps) {
            console.log('Paso fuera de rango:', newStep);
            return;
        }
        
        // Verificar si el paso actual está completo antes de avanzar
        if (direction > 0 && !this.isCurrentStepComplete()) {
            console.log('Paso actual no está completo, no se puede avanzar');
            this.showAlert('Por favor completa todos los campos requeridos antes de continuar', 'warning');
            return;
        }
        
        this.currentStep = newStep;
        console.log('Cambiando a paso:', this.currentStep);

        this.updateStepVisibility();
        this.updateNavigationButtons();
        
        // Scroll to top of verification section
        const verificationSection = document.getElementById('verification');
        if (verificationSection) {
            verificationSection.scrollIntoView({ behavior: 'smooth' });
        }
    }

    validateCurrentStep() {
        switch (this.currentStep) {
            case 1:
                // No validation needed for step 1
                return true;
            case 2:
                if (!this.projectData.primary_use) {
                    this.showAlert('Por favor, selecciona el uso principal del edificio.', 'warning');
                    return false;
                }
                break;
            case 3:
                // No validation needed for step 3 (secondary uses are optional)
                return true;
            case 4:
                if (this.projectData.memoria_files.length === 0) {
                    this.showAlert('Por favor, sube la memoria descriptiva del proyecto.', 'warning');
                        return false;
                    }
                if (this.projectData.planos_files.length === 0) {
                    this.showAlert('Por favor, sube al menos un plano del proyecto.', 'warning');
                            return false;
                        }
                break;
            case 5: // Document Analysis
                return this.projectData.analysis_results && this.projectData.analysis_results.documents_analyzed > 0;
        }
        return true;
    }

    canProceedToNextStep() {
        switch (this.currentStep) {
            case 1:
                return true;
            case 2:
                return this.projectData.primary_use !== null;
            case 3:
                return true; // Secondary uses are optional
            case 4:
                return this.projectData.memoria_files.length > 0 && this.projectData.planos_files.length > 0;
            case 5: // Document Analysis
                return this.projectData.analysis_results && this.projectData.analysis_results.documents_analyzed > 0;
        }
                    return false;
                }

    updateStepVisibility() {
        // Si currentStep es 0, mostrar todos los pasos
        if (this.currentStep === 0) {
            // Mostrar todos los pasos
            for (let i = 1; i <= this.maxSteps; i++) {
                const step = document.getElementById(`step${i}`);
                if (step) {
                    step.classList.remove('d-none');
                }
            }
            
            // Actualizar barra de progreso al 100%
            const progressBar = document.getElementById('progressBar');
            if (progressBar) {
                progressBar.style.width = '100%';
            }
            
            // Marcar todos los indicadores como completados
            for (let i = 1; i <= this.maxSteps; i++) {
                const indicator = document.getElementById(`stepIndicator${i}`);
                if (indicator) {
                    indicator.classList.remove('bg-primary', 'bg-secondary');
                    indicator.classList.add('bg-success');
                }
            }
        } else {
            // Lógica original: mostrar solo el paso actual
            for (let i = 1; i <= this.maxSteps; i++) {
                const step = document.getElementById(`step${i}`);
                if (step) {
                    step.classList.add('d-none');
                }
            }

            // Show current step
            const currentStep = document.getElementById(`step${this.currentStep}`);
            if (currentStep) {
                currentStep.classList.remove('d-none');
            }

            // Update progress bar
            const progressBar = document.getElementById('progressBar');
            if (progressBar) {
                const progress = ((this.currentStep - 1) / (this.maxSteps - 1)) * 100;
                progressBar.style.width = `${progress}%`;
            }

            // Update step indicators
            for (let i = 1; i <= this.maxSteps; i++) {
                const indicator = document.getElementById(`stepIndicator${i}`);
                if (indicator) {
                    if (i < this.currentStep) {
                        indicator.classList.remove('bg-primary', 'bg-secondary');
                        indicator.classList.add('bg-success');
                    } else if (i === this.currentStep) {
                        indicator.classList.remove('bg-success', 'bg-secondary');
                        indicator.classList.add('bg-primary');
                    } else {
                        indicator.classList.remove('bg-primary', 'bg-success');
                        indicator.classList.add('bg-secondary');
                    }
                }
            }
        }
    }

    updateNavigationButtons() {
        const prevButton = document.getElementById('prevButton');
        const nextButton = document.getElementById('nextButton');

        // Si currentStep es 0 (mostrar todos los pasos), ocultar botones de navegación
        if (this.currentStep === 0) {
            if (prevButton) {
                prevButton.style.display = 'none';
            }
            if (nextButton) {
                nextButton.style.display = 'none';
            }
            return;
        }

        // Lógica original para navegación paso a paso
        if (prevButton) {
            prevButton.style.display = 'inline-block';
            prevButton.disabled = this.currentStep === 1;
        }

        if (nextButton) {
            if (this.currentStep === this.maxSteps) {
                nextButton.style.display = 'none';
            } else {
                nextButton.style.display = 'inline-block';
                nextButton.disabled = !this.canProceedToNextStep();
            }
        }
    }

    showAlert(message, type = 'info') {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());

        // Create new alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert at the top of the form
        const form = document.querySelector('.verification-form');
        if (form) {
            form.insertBefore(alertDiv, form.firstChild);
        }

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    async startMadridVerification() {
        console.log('Starting Madrid verification...');
        
        // Show loading state
        const startButton = document.getElementById('startVerification');
        const loadingSpinner = document.getElementById('loadingSpinner');
        
        if (startButton) startButton.disabled = true;
        if (loadingSpinner) loadingSpinner.classList.remove('d-none');

        try {
            // Prepare project data for Madrid API
            const madridProjectData = {
                is_existing_building: this.projectData.is_existing_building,
                primary_use: this.projectData.primary_use,
                has_secondary_uses: this.projectData.has_secondary_uses,
                secondary_uses: this.projectData.secondary_uses,
                secondary_uses_floors: this.projectData.secondary_uses_floors,
                memoria_files: this.projectData.memoria_files.map(file => file.name),
                planos_files: this.projectData.planos_files.map(file => file.name)
            };

            console.log('Sending data to Madrid API:', madridProjectData);

            const response = await fetch('/api/madrid/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(madridProjectData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Madrid verification result:', result);

            this.projectData.jobId = result.job_id;
            this.displayResults(result);

        } catch (error) {
            console.error('Error during Madrid verification:', error);
            this.showAlert(`Error durante la verificación: ${error.message}`, 'danger');
        } finally {
            // Hide loading state
            if (startButton) startButton.disabled = false;
            if (loadingSpinner) loadingSpinner.classList.add('d-none');
        }
    }

    displayResults(result) {
        const resultsContainer = document.getElementById('resultsContainer');
        const resultsContent = document.getElementById('resultsContent');

        if (resultsContainer && resultsContent) {
            resultsContent.innerHTML = `
            <div class="row">
                    <div class="col-12">
                        <h4 class="mb-4">Resultados de la Verificación</h4>
                        <div class="alert alert-info">
                            <strong>Job ID:</strong> ${result.job_id}
                    </div>
                        <div class="alert alert-success">
                            <strong>Estado:</strong> ${result.status}
                </div>
                        <div class="alert alert-primary">
                            <strong>Mensaje:</strong> ${result.message}
                    </div>
                </div>
            </div>
        `;
            
            resultsContainer.classList.remove('d-none');
        }
    }

    startNewVerification() {
        console.log('Starting new verification...');
        
        // Reset form
        this.currentStep = 1;
        this.projectData = {
            is_existing_building: false,
            primary_use: null,
            has_secondary_uses: false,
            secondary_uses: [],
            secondary_uses_floors: {},
            memoria_files: [],
            planos_files: [],
            jobId: null
        };

        // Reset UI
        document.getElementById('isExistingBuilding').checked = false;
        document.getElementById('primaryUse').value = '';
        document.getElementById('hasSecondaryUses').checked = false;
        document.getElementById('secondaryUsesSection').classList.add('d-none');
        document.getElementById('secondaryUsesFloors').innerHTML = '';
        document.getElementById('memoriaFileList').innerHTML = '';
        document.getElementById('planosFileList').innerHTML = '';
        document.getElementById('memoriaInput').value = '';
        document.getElementById('planosInput').value = '';
        document.getElementById('resultsContainer').classList.add('d-none');

        // Update UI
        this.updateStepVisibility();
        this.updateNavigationButtons();
    }

    // =============================================================================
    // CHATBOT FUNCTIONS
    // =============================================================================

    async startChatbotSession() {
        console.log('Iniciando sesión de chatbot...');
        
        try {
            // Preparar datos del proyecto para el chatbot
            const chatbotProjectData = {
                is_existing_building: this.projectData.is_existing_building,
                primary_use: this.projectData.primary_use,
                has_secondary_uses: this.projectData.has_secondary_uses,
                secondary_uses: this.projectData.secondary_uses,
                secondary_uses_floors: this.projectData.secondary_uses_floors,
                files: [
                    ...this.projectData.memoria_files.map(f => f.name),
                    ...this.projectData.planos_files.map(f => f.name)
                ]
            };

            const response = await fetch('/api/madrid/chatbot/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    project_data: chatbotProjectData
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.chatbotSession = result;
            
            // Actualizar interfaz del chatbot
            this.updateChatbotInterface(result);
            
            // Habilitar input del chatbot
            this.enableChatbotInput();
            
            console.log('Sesión de chatbot iniciada:', result.session_id);
            
        } catch (error) {
            console.error('Error iniciando sesión de chatbot:', error);
            this.showChatbotError('Error iniciando el asistente de verificación');
        }
    }

    updateChatbotInterface(sessionData) {
        // Actualizar estado del chatbot
        const statusElement = document.getElementById('chatbotStatus');
        if (statusElement) {
            statusElement.textContent = sessionData.state === 'resolving_ambiguities' ? 'Resolviendo' : 'Analizando';
            statusElement.className = `badge ${sessionData.state === 'resolving_ambiguities' ? 'bg-info' : 'bg-warning'}`;
        }

        // Actualizar contadores
        const ambiguityCount = document.getElementById('ambiguityCount');
        const resolvedCount = document.getElementById('resolvedCount');
        if (ambiguityCount) ambiguityCount.textContent = sessionData.ambiguities_count || 0;
        if (resolvedCount) resolvedCount.textContent = 0;

        // Mostrar mensaje inicial si hay
        if (sessionData.message) {
            this.addChatbotMessage(sessionData.message, 'bot');
        }

        // Mostrar acciones sugeridas si las hay
        if (sessionData.message && sessionData.message.suggested_actions) {
            this.showSuggestedActions(sessionData.message.suggested_actions);
        }
    }

    enableChatbotInput() {
        const chatbotInput = document.getElementById('chatbotInput');
        const sendMessageBtn = document.getElementById('sendMessageBtn');
        
        if (chatbotInput) {
            chatbotInput.disabled = false;
            chatbotInput.focus();
        }
        if (sendMessageBtn) {
            sendMessageBtn.disabled = false;
        }
    }

    async sendChatbotMessage() {
        const chatbotInput = document.getElementById('chatbotInput');
        const message = chatbotInput.value.trim();
        
        if (!message || !this.chatbotSession) return;

        // Agregar mensaje del usuario
        this.addChatbotMessage(message, 'user');
        
        // Limpiar input
        chatbotInput.value = '';
        
        // Deshabilitar input temporalmente
        this.disableChatbotInput();

        try {
            const response = await fetch('/api/madrid/chatbot/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.chatbotSession.session_id,
                    message: message
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            // Agregar respuesta del chatbot
            this.addChatbotMessage(result.content, 'bot');
            
            // Mostrar acciones sugeridas si las hay
            if (result.suggested_actions && result.suggested_actions.length > 0) {
                this.showSuggestedActions(result.suggested_actions);
            } else {
                this.hideSuggestedActions();
            }

            // Actualizar estado de la sesión
            if (result.session_status) {
                this.updateChatbotStatus(result.session_status);
            }

            // Verificar si se completó la resolución de ambigüedades
            if (result.type === 'completion') {
                this.completeAmbiguityResolution();
            }

        } catch (error) {
            console.error('Error enviando mensaje al chatbot:', error);
            this.showChatbotError('Error enviando mensaje al asistente');
        } finally {
            // Rehabilitar input
            this.enableChatbotInput();
        }
    }

    addChatbotMessage(content, type) {
        const messagesContainer = document.getElementById('chatbotMessages');
        if (!messagesContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const avatar = type === 'bot' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
        const time = new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                ${avatar}
            </div>
            <div class="message-content">
                <div class="message-text">${content}</div>
                <div class="message-time">
                    <small class="text-muted">${time}</small>
                </div>
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        
        // Scroll al final
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showSuggestedActions(actions) {
        const actionsContainer = document.getElementById('suggestedActions');
        if (!actionsContainer) return;

        actionsContainer.innerHTML = '';
        
        actions.forEach(action => {
            const button = document.createElement('button');
            button.className = 'btn btn-outline-primary btn-sm me-2 mb-2';
            button.textContent = action.label;
            button.onclick = () => {
                this.selectSuggestedAction(action);
            };
            actionsContainer.appendChild(button);
        });
    }

    hideSuggestedActions() {
        const actionsContainer = document.getElementById('suggestedActions');
        if (actionsContainer) {
            actionsContainer.innerHTML = '';
        }
    }

    selectSuggestedAction(action) {
        // Simular click en el botón sugerido
        const chatbotInput = document.getElementById('chatbotInput');
        if (chatbotInput) {
            chatbotInput.value = action.label;
            this.sendChatbotMessage();
        }
    }

    updateChatbotStatus(status) {
        // Actualizar contadores
        const ambiguityCount = document.getElementById('ambiguityCount');
        const resolvedCount = document.getElementById('resolvedCount');
        const progressBar = document.getElementById('ambiguityProgress');
        
        if (ambiguityCount) ambiguityCount.textContent = status.ambiguities_remaining || 0;
        if (resolvedCount) resolvedCount.textContent = status.ambiguities_resolved || 0;
        
        if (progressBar) {
            const total = (status.ambiguities_remaining || 0) + (status.ambiguities_resolved || 0);
            const resolved = status.ambiguities_resolved || 0;
            const percentage = total > 0 ? (resolved / total) * 100 : 0;
            progressBar.style.width = `${percentage}%`;
        }
    }

    completeAmbiguityResolution() {
        console.log('Resolución de ambigüedades completada');
        
        // Actualizar estado del chatbot
        const statusElement = document.getElementById('chatbotStatus');
        if (statusElement) {
            statusElement.textContent = 'Completado';
            statusElement.className = 'badge bg-success';
        }

        // Deshabilitar input del chatbot
        this.disableChatbotInput();
        
        // Mostrar mensaje de finalización
        this.addChatbotMessage(
            '¡Perfecto! He resuelto todas las ambigüedades. Ahora procederé con la verificación normativa completa de tu proyecto.',
            'bot'
        );

        // Habilitar botón de verificación
        setTimeout(() => {
            this.updateNavigationButtons();
        }, 2000);
    }

    disableChatbotInput() {
        const chatbotInput = document.getElementById('chatbotInput');
        const sendMessageBtn = document.getElementById('sendMessageBtn');
        
        if (chatbotInput) {
            chatbotInput.disabled = true;
        }
        if (sendMessageBtn) {
            sendMessageBtn.disabled = true;
        }
    }

    showChatbotError(message) {
        this.addChatbotMessage(`❌ ${message}`, 'bot');
    }

    // =============================================================================
    // UPDATED NAVIGATION FUNCTIONS
    // =============================================================================

    nextStep() {
        if (this.validateCurrentStep()) {
            if (this.currentStep < this.maxSteps) {
                this.currentStep++;
                
                // Si llegamos al paso 5 (chatbot), iniciar sesión
                if (this.currentStep === 5) {
                    this.startChatbotSession();
                }
                
                this.updateStepVisibility();
                this.updateNavigationButtons();
            }
        }
    }

    canProceedToNextStep() {
        switch (this.currentStep) {
            case 1:
                return true;
            case 2:
                return this.projectData.primary_use !== null;
            case 3:
                return true; // Secondary uses are optional
            case 4:
                return this.projectData.memoria_files.length > 0 && this.projectData.planos_files.length > 0;
            case 5: // Document Analysis
                return this.projectData.analysis_results && this.projectData.analysis_results.documents_analyzed > 0;
            case 6:
                return true;
        }
        return false;
    }

    // =============================================================================
    // DOCUMENT CLASSIFICATION FUNCTIONS
    // =============================================================================

    async classifyDocuments() {
        console.log('Clasificando documentos automáticamente...');
        
        try {
            this.showSpinner();
            
            // Preparar archivos para clasificación
            const formData = new FormData();
            
            // Agregar archivos de memoria
            this.projectData.memoria_files.forEach(file => {
                formData.append('memoria_files', file);
            });
            
            // Agregar archivos de planos
            this.projectData.planos_files.forEach(file => {
                formData.append('plano_files', file);
            });
            
            // Agregar datos del proyecto
            formData.append('is_existing_building', this.projectData.is_existing_building);
            formData.append('primary_use', this.projectData.primary_use);
            formData.append('has_secondary_uses', this.projectData.has_secondary_uses);
            formData.append('secondary_uses', JSON.stringify(this.projectData.secondary_uses));

            const response = await fetch('/api/madrid/classify-documents', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Resultado de clasificación:', result);
            
            // Actualizar interfaz con resultados de clasificación
            this.updateDocumentClassificationUI(result);
            
            this.hideSpinner();
            this.showAlert('Documentos clasificados automáticamente', 'success');
            
        } catch (error) {
            console.error('Error en clasificación de documentos:', error);
            this.hideSpinner();
            this.showAlert('Error en la clasificación: ' + error.message, 'danger');
        }
    }

    updateDocumentClassificationUI(classificationResult) {
        // Actualizar contadores de documentos
        const memoriaCount = document.getElementById('memoriaCount');
        const planosCount = document.getElementById('planosCount');
        
        if (memoriaCount) {
            memoriaCount.textContent = classificationResult.memoria_files?.length || 0;
        }
        if (planosCount) {
            planosCount.textContent = classificationResult.plano_files?.length || 0;
        }
        
        // Mostrar detalles de clasificación
        this.showClassificationDetails(classificationResult);
    }

    showClassificationDetails(classificationResult) {
        // Crear modal o sección para mostrar detalles de clasificación
        const detailsContainer = document.getElementById('classificationDetails');
        if (!detailsContainer) return;
        
        let html = '<div class="classification-details">';
        html += '<h5>Clasificación Automática de Documentos</h5>';
        
        // Mostrar memorias clasificadas
        if (classificationResult.memoria_files?.length > 0) {
            html += '<div class="memoria-classification">';
            html += '<h6><i class="fas fa-file-alt text-primary"></i> Memorias Descriptivas</h6>';
            html += '<ul class="list-group list-group-flush">';
            
            classificationResult.memoria_files.forEach(file => {
                html += `<li class="list-group-item d-flex justify-content-between align-items-center">`;
                html += `<span>${file.filename}</span>`;
                html += `<span class="badge bg-primary">Confianza: ${(file.classification.confidence * 100).toFixed(1)}%</span>`;
                html += `</li>`;
            });
            
            html += '</ul></div>';
        }
        
        // Mostrar planos clasificados
        if (classificationResult.plano_files?.length > 0) {
            html += '<div class="plano-classification">';
            html += '<h6><i class="fas fa-compass text-success"></i> Planos Arquitectónicos</h6>';
            html += '<ul class="list-group list-group-flush">';
            
            classificationResult.plano_files.forEach(file => {
                html += `<li class="list-group-item d-flex justify-content-between align-items-center">`;
                html += `<span>${file.filename}</span>`;
                html += `<span class="badge bg-success">Confianza: ${(file.classification.confidence * 100).toFixed(1)}%</span>`;
                html += `</li>`;
            });
            
            html += '</ul></div>';
        }
        
        html += '</div>';
        detailsContainer.innerHTML = html;
    }

    // =============================================================================
    // NORMATIVE INTEGRATION FUNCTIONS
    // =============================================================================

    async applyNormative() {
        console.log('Aplicando normativa específica...');
        
        try {
            this.showSpinner();
            
            // Preparar datos del proyecto para aplicación de normativa
            const normativeData = {
                project_id: this.projectData.jobId || 'temp_project',
                primary_use: this.projectData.primary_use,
                secondary_uses: this.projectData.secondary_uses,
                is_existing_building: this.projectData.is_existing_building,
                memoria_files: this.projectData.memoria_files.map(f => f.name),
                planos_files: this.projectData.planos_files.map(f => f.name)
            };

            const response = await fetch('/api/madrid/apply-normative', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(normativeData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Resultado de aplicación de normativa:', result);
            
            // Actualizar interfaz con normativa aplicada
            this.updateNormativeUI(result);
            
            this.hideSpinner();
            this.showAlert('Normativa específica aplicada correctamente', 'success');
            
        } catch (error) {
            console.error('Error aplicando normativa:', error);
            this.hideSpinner();
            this.showAlert('Error aplicando normativa: ' + error.message, 'danger');
        }
    }

    updateNormativeUI(normativeResult) {
        // Mostrar documentos normativos aplicables
        this.showApplicableDocuments(normativeResult.applicable_documents);
        
        // Mostrar asignación por plantas
        this.showFloorAssignments(normativeResult.floor_assignments);
        
        // Mostrar requisitos de cumplimiento
        this.showComplianceRequirements(normativeResult.compliance_requirements);
    }

    showApplicableDocuments(documents) {
        const container = document.getElementById('normativeDocuments');
        if (!container) return;
        
        let html = '<div class="normative-documents">';
        html += '<h6><i class="fas fa-book text-info"></i> Documentos Normativos Aplicables</h6>';
        html += '<div class="row">';
        
        // Agrupar por tipo
        const byType = {
            'basic': documents.filter(d => d.type === 'basic'),
            'pgoum': documents.filter(d => d.type === 'pgoum'),
            'support': documents.filter(d => d.type === 'support')
        };
        
        Object.entries(byType).forEach(([type, docs]) => {
            if (docs.length > 0) {
                html += '<div class="col-md-4 mb-3">';
                html += `<h6 class="text-${type === 'basic' ? 'primary' : type === 'pgoum' ? 'success' : 'warning'}">`;
                html += `${type === 'basic' ? 'Básicos' : type === 'pgoum' ? 'PGOUM' : 'Apoyo'}</h6>`;
                html += '<ul class="list-group list-group-flush">';
                
                docs.forEach(doc => {
                    html += `<li class="list-group-item d-flex justify-content-between align-items-center">`;
                    html += `<span>${doc.name}</span>`;
                    html += `<span class="badge bg-${type === 'basic' ? 'primary' : type === 'pgoum' ? 'success' : 'warning'}">${doc.priority}</span>`;
                    html += `</li>`;
                });
                
                html += '</ul></div>';
            }
        });
        
        html += '</div></div>';
        container.innerHTML = html;
    }

    showFloorAssignments(floorAssignments) {
        const container = document.getElementById('floorAssignments');
        if (!container) return;
        
        let html = '<div class="floor-assignments">';
        html += '<h6><i class="fas fa-building text-secondary"></i> Asignación por Plantas</h6>';
        html += '<div class="accordion" id="floorAccordion">';
        
        Object.entries(floorAssignments).forEach(([floor, documents], index) => {
            html += `<div class="accordion-item">`;
            html += `<h2 class="accordion-header" id="heading${index}">`;
            html += `<button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse${index}">`;
            html += `Planta ${floor} (${documents.length} documentos)`;
            html += `</button></h2>`;
            html += `<div id="collapse${index}" class="accordion-collapse collapse" data-bs-parent="#floorAccordion">`;
            html += `<div class="accordion-body">`;
            html += '<ul class="list-group list-group-flush">';
            
            documents.forEach(doc => {
                html += `<li class="list-group-item">${doc}</li>`;
            });
            
            html += '</ul></div></div></div>';
        });
        
        html += '</div></div>';
        container.innerHTML = html;
    }

    showComplianceRequirements(requirements) {
        const container = document.getElementById('complianceRequirements');
        if (!container) return;
        
        let html = '<div class="compliance-requirements">';
        html += '<h6><i class="fas fa-check-circle text-success"></i> Requisitos de Cumplimiento</h6>';
        html += '<div class="row">';
        
        Object.entries(requirements).forEach(([docName, reqs]) => {
            html += '<div class="col-md-6 mb-3">';
            html += `<div class="card">`;
            html += `<div class="card-header">${docName}</div>`;
            html += `<div class="card-body">`;
            html += '<ul class="list-group list-group-flush">';
            
            reqs.forEach(req => {
                const severityClass = {
                    'critical': 'danger',
                    'high': 'warning',
                    'medium': 'info',
                    'low': 'secondary'
                }[req.severity] || 'secondary';
                
                html += `<li class="list-group-item d-flex justify-content-between align-items-center">`;
                html += `<span>${req.title}</span>`;
                html += `<span class="badge bg-${severityClass}">${req.severity}</span>`;
                html += `</li>`;
            });
            
            html += '</ul></div></div></div>';
        });
        
        html += '</div></div>';
        container.innerHTML = html;
    }

    // =============================================================================
    // DOCUMENT ANALYSIS FUNCTIONS
    // =============================================================================

    async analyzeDocuments() {
        console.log('Analizando documentos...');
        
        try {
            this.showSpinner();
            
            // Preparar datos para análisis
            const analysisData = {
                project_data: {
                    project_id: this.projectData.jobId || 'temp_project',
                    primary_use: this.projectData.primary_use,
                    secondary_uses: this.projectData.secondary_uses,
                    is_existing_building: this.projectData.is_existing_building,
                    memoria_files: this.projectData.memoria_files.map(f => f.name),
                    planos_files: this.projectData.planos_files.map(f => f.name)
                },
                files: {
                    memoria: this.projectData.memoria_files,
                    planos: this.projectData.planos_files
                }
            };

            const response = await fetch('/api/madrid/analyze-documents', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(analysisData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Análisis completado:', result);
            
            // Guardar resultados del análisis
            this.projectData.analysis_results = result;
            
            // Mostrar resultados en la interfaz
            this.displayAnalysisResults(result);
            
            this.hideSpinner();
            this.showAlert('Análisis de documentos completado', 'success');
            
        } catch (error) {
            console.error('Error analizando documentos:', error);
            this.hideSpinner();
            this.showAlert('Error en el análisis: ' + error.message, 'danger');
        }
    }

    displayAnalysisResults(results) {
        const container = document.getElementById('analysisResults');
        if (!container) return;
        
        let html = '<div class="analysis-results">';
        html += '<h5><i class="fas fa-search text-primary"></i> Resultados del Análisis</h5>';
        
        // Resumen del análisis
        html += '<div class="row mb-4">';
        html += '<div class="col-md-4">';
        html += '<div class="card text-center">';
        html += '<div class="card-body">';
        html += `<h5 class="card-title text-primary">${results.documents_analyzed || 0}</h5>`;
        html += '<p class="card-text">Documentos Analizados</p>';
        html += '</div></div></div>';
        
        html += '<div class="col-md-4">';
        html += '<div class="card text-center">';
        html += '<div class="card-body">';
        html += `<h5 class="card-title text-warning">${results.ambiguities_detected || 0}</h5>`;
        html += '<p class="card-text">Ambigüedades Detectadas</p>';
        html += '</div></div></div>';
        
        html += '<div class="col-md-4">';
        html += '<div class="card text-center">';
        html += '<div class="card-body">';
        html += `<h5 class="card-title text-success">${results.compliance_issues || 0}</h5>`;
        html += '<p class="card-text">Problemas de Cumplimiento</p>';
        html += '</div></div></div>';
        html += '</div>';
        
        // Detalles del análisis
        if (results.analysis_details) {
            html += '<div class="analysis-details">';
            html += '<h6>Detalles del Análisis</h6>';
            html += '<div class="accordion" id="analysisAccordion">';
            
            results.analysis_details.forEach((detail, index) => {
                html += '<div class="accordion-item">';
                html += `<h2 class="accordion-header" id="analysisHeading${index}">`;
                html += `<button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#analysisCollapse${index}">`;
                html += `<i class="fas fa-file-alt me-2"></i>${detail.document_name}`;
                html += '</button></h2>';
                html += `<div id="analysisCollapse${index}" class="accordion-collapse collapse" data-bs-parent="#analysisAccordion">`;
                html += '<div class="accordion-body">';
                html += `<p><strong>Tipo:</strong> ${detail.document_type}</p>`;
                html += `<p><strong>Confianza:</strong> ${(detail.confidence * 100).toFixed(1)}%</p>`;
                html += `<p><strong>Páginas analizadas:</strong> ${detail.pages_analyzed}</p>`;
                if (detail.key_findings && detail.key_findings.length > 0) {
                    html += '<p><strong>Hallazgos clave:</strong></p>';
                    html += '<ul>';
                    detail.key_findings.forEach(finding => {
                        html += `<li>${finding}</li>`;
                    });
                    html += '</ul>';
                }
                html += '</div></div></div>';
            });
            
            html += '</div></div>';
        }
        
        html += '</div>';
        container.innerHTML = html;
        
        // Mostrar ambigüedades si las hay
        if (results.ambiguities && results.ambiguities.length > 0) {
            this.displayAmbiguities(results.ambiguities);
        }
    }

    displayAmbiguities(ambiguities) {
        const container = document.getElementById('ambiguitiesDetected');
        const listContainer = document.getElementById('ambiguitiesList');
        
        if (!container || !listContainer) return;
        
        container.style.display = 'block';
        
        let html = '';
        ambiguities.forEach((ambiguity, index) => {
            html += '<div class="list-group-item">';
            html += '<div class="d-flex w-100 justify-content-between">';
            html += `<h6 class="mb-1">${ambiguity.title}</h6>`;
            html += `<small class="text-muted">Prioridad: ${ambiguity.priority}</small>`;
            html += '</div>';
            html += `<p class="mb-1">${ambiguity.description}</p>`;
            html += `<small class="text-muted">Documento: ${ambiguity.document_name} | Página: ${ambiguity.page_number}</small>`;
            html += '</div>';
        });
        
        listContainer.innerHTML = html;
    }

    // =============================================================================
    // FINAL CHECKLIST FUNCTIONS
    // =============================================================================

    async generateFinalChecklist() {
        console.log('Generando checklist final...');
        
        try {
            this.showSpinner();
            
            // Preparar datos para generación de checklist
            const checklistData = {
                project_data: {
                    project_id: this.projectData.jobId || 'temp_project',
                    project_name: 'Proyecto de Verificación',
                    primary_use: this.projectData.primary_use,
                    secondary_uses: this.projectData.secondary_uses,
                    is_existing_building: this.projectData.is_existing_building,
                    memoria_files: this.projectData.memoria_files.map(f => f.name),
                    planos_files: this.projectData.planos_files.map(f => f.name)
                },
                normative_application: this.projectData.normative_application || {},
                compliance_results: this.projectData.compliance_results || {}
            };

            const response = await fetch('/api/madrid/final-checklist/generate-checklist', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(checklistData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Checklist final generado:', result);
            
            // Guardar checklist en projectData
            this.projectData.final_checklist = result;
            
            // Mostrar checklist en la interfaz
            this.displayFinalChecklist(result);
            
            this.hideSpinner();
            this.showAlert('Checklist final generado correctamente', 'success');
            
        } catch (error) {
            console.error('Error generando checklist final:', error);
            this.hideSpinner();
            this.showAlert('Error generando checklist: ' + error.message, 'danger');
        }
    }

    displayFinalChecklist(checklist) {
        // Mostrar checklist en el paso 6 (Verificación Final)
        const container = document.getElementById('finalChecklistContainer');
        if (!container) return;
        
        let html = '<div class="final-checklist">';
        html += '<h4><i class="fas fa-clipboard-check text-primary"></i> Checklist Final de Verificación</h4>';
        
        // Resumen general
        html += '<div class="checklist-summary mb-4">';
        html += '<div class="row">';
        html += '<div class="col-md-3">';
        html += `<div class="card text-center">`;
        html += `<div class="card-body">`;
        html += `<h5 class="card-title text-primary">${checklist.overall_completion.toFixed(1)}%</h5>`;
        html += '<p class="card-text">Completado</p>';
        html += '</div></div></div>';
        
        html += '<div class="col-md-3">';
        html += `<div class="card text-center">`;
        html += `<div class="card-body">`;
        html += `<h5 class="card-title text-success">${checklist.completed_items}</h5>`;
        html += '<p class="card-text">Completados</p>';
        html += '</div></div></div>';
        
        html += '<div class="col-md-3">';
        html += `<div class="card text-center">`;
        html += `<div class="card-body">`;
        html += `<h5 class="card-title text-warning">${checklist.total_items - checklist.completed_items}</h5>`;
        html += '<p class="card-text">Pendientes</p>';
        html += '</div></div></div>';
        
        html += '<div class="col-md-3">';
        html += `<div class="card text-center">`;
        html += `<div class="card-body">`;
        html += `<h5 class="card-title text-danger">${checklist.critical_items}</h5>`;
        html += '<p class="card-text">Críticos</p>';
        html += '</div></div></div>';
        
        html += '</div></div>';
        
        // Categorías del checklist
        html += '<div class="checklist-categories">';
        html += '<h5>Categorías de Verificación</h5>';
        html += '<div class="accordion" id="checklistAccordion">';
        
        checklist.categories.forEach((category, index) => {
            const statusClass = category.completion_percentage >= 100 ? 'success' : 
                               category.completion_percentage >= 70 ? 'warning' : 'danger';
            
            html += `<div class="accordion-item">`;
            html += `<h2 class="accordion-header" id="heading${index}">`;
            html += `<button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse${index}">`;
            html += `<i class="${category.icon} text-${category.color} me-2"></i>`;
            html += `${category.name} `;
            html += `<span class="badge bg-${statusClass} ms-2">${category.completion_percentage.toFixed(1)}%</span>`;
            html += `</button></h2>`;
            html += `<div id="collapse${index}" class="accordion-collapse collapse" data-bs-parent="#checklistAccordion">`;
            html += `<div class="accordion-body">`;
            html += `<p class="text-muted">${category.description}</p>`;
            html += '<div class="progress mb-3">';
            html += `<div class="progress-bar bg-${statusClass}" style="width: ${category.completion_percentage}%"></div>`;
            html += '</div>';
            html += '<div class="row">';
            html += '<div class="col-md-6">';
            html += `<small class="text-muted">Completados: ${category.completed_items}/${category.total_items}</small>`;
            html += '</div>';
            html += '<div class="col-md-6 text-end">';
            html += `<small class="text-muted">Críticos: ${category.items.filter(item => item.priority === 'critical').length}</small>`;
            html += '</div></div>';
            
            // Items del checklist
            html += '<div class="checklist-items mt-3">';
            category.items.forEach(item => {
                const itemStatusClass = {
                    'completed': 'success',
                    'failed': 'danger',
                    'in_progress': 'warning',
                    'pending': 'secondary',
                    'requires_attention': 'warning'
                }[item.status] || 'secondary';
                
                const priorityClass = {
                    'critical': 'danger',
                    'high': 'warning',
                    'medium': 'info',
                    'low': 'secondary'
                }[item.priority] || 'secondary';
                
                html += `<div class="checklist-item card mb-2">`;
                html += `<div class="card-body">`;
                html += '<div class="row align-items-center">';
                html += '<div class="col-md-8">';
                html += `<h6 class="mb-1">${item.title}</h6>`;
                html += `<p class="text-muted small mb-1">${item.description}</p>`;
                html += `<small class="text-muted">Referencia: ${item.normative_reference}</small>`;
                html += '</div>';
                html += '<div class="col-md-4 text-end">';
                html += `<span class="badge bg-${itemStatusClass} me-1">${item.status}</span>`;
                html += `<span class="badge bg-${priorityClass}">${item.priority}</span>`;
                html += '</div></div>';
                
                // Evidencia requerida
                if (item.evidence_required && item.evidence_required.length > 0) {
                    html += '<div class="mt-2">';
                    html += '<small class="text-muted">Evidencia requerida:</small>';
                    html += '<ul class="list-unstyled small">';
                    item.evidence_required.forEach(evidence => {
                        html += `<li><i class="fas fa-file-pdf text-danger me-1"></i>${evidence}</li>`;
                    });
                    html += '</ul></div>';
                }
                
                html += '</div></div>';
            });
            
            html += '</div></div></div></div>';
        });
        
        html += '</div></div></div>';
        
        // Botones de acción
        html += '<div class="checklist-actions mt-4">';
        html += '<div class="row">';
        html += '<div class="col-md-6">';
        html += '<button id="generateReportBtn" class="btn btn-primary">';
        html += '<i class="fas fa-file-alt"></i> Generar Reporte Final';
        html += '</button>';
        html += '</div>';
        html += '<div class="col-md-6 text-end">';
        html += '<button id="exportChecklistBtn" class="btn btn-outline-secondary">';
        html += '<i class="fas fa-download"></i> Exportar Checklist';
        html += '</button>';
        html += '</div></div></div>';
        
        html += '</div>';
        container.innerHTML = html;
        
        // Agregar event listeners
        this.addChecklistEventListeners();
    }

    addChecklistEventListeners() {
        // Botón de generar reporte
        const generateReportBtn = document.getElementById('generateReportBtn');
        if (generateReportBtn) {
            generateReportBtn.addEventListener('click', () => {
                this.generateFinalReport();
            });
        }

        // Botón de exportar checklist
        const exportChecklistBtn = document.getElementById('exportChecklistBtn');
        if (exportChecklistBtn) {
            exportChecklistBtn.addEventListener('click', () => {
                this.exportChecklist();
            });
        }
    }

    async generateFinalReport() {
        console.log('Generando reporte final...');
        
        try {
            this.showSpinner();
            
            if (!this.projectData.final_checklist) {
                throw new Error('No hay checklist final disponible');
            }
            
            const reportData = {
                project_data: {
                    project_id: this.projectData.jobId || 'temp_project',
                    project_name: 'Proyecto de Verificación',
                    primary_use: this.projectData.primary_use,
                    secondary_uses: this.projectData.secondary_uses,
                    is_existing_building: this.projectData.is_existing_building
                },
                normative_application: this.projectData.normative_application || {},
                compliance_results: this.projectData.compliance_results || {},
                checklist_data: this.projectData.final_checklist
            };

            const response = await fetch('/api/madrid/final-checklist/generate-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(reportData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Reporte final generado:', result);
            
            // Mostrar reporte en modal
            this.displayFinalReport(result);
            
            this.hideSpinner();
            this.showAlert('Reporte final generado correctamente', 'success');
            
        } catch (error) {
            console.error('Error generando reporte final:', error);
            this.hideSpinner();
            this.showAlert('Error generando reporte: ' + error.message, 'danger');
        }
    }

    displayFinalReport(report) {
        // Crear modal para mostrar reporte
        const modalHtml = `
            <div class="modal fade" id="finalReportModal" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-file-alt text-primary"></i> Reporte Final de Verificación
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="report-content">
                                <!-- Resumen ejecutivo -->
                                <div class="executive-summary mb-4">
                                    <h6>Resumen Ejecutivo</h6>
                                    <div class="alert alert-${report.executive_summary.status_color}">
                                        <h6>Estado General: ${report.executive_summary.overall_status}</h6>
                                        <p>${report.executive_summary.summary_text}</p>
                                        <div class="row">
                                            <div class="col-md-3">
                                                <small>Cumplimiento: ${report.executive_summary.completion_percentage.toFixed(1)}%</small>
                                            </div>
                                            <div class="col-md-3">
                                                <small>Total verificaciones: ${report.executive_summary.total_checks}</small>
                                            </div>
                                            <div class="col-md-3">
                                                <small>Completadas: ${report.executive_summary.completed_checks}</small>
                                            </div>
                                            <div class="col-md-3">
                                                <small>Problemas críticos: ${report.executive_summary.critical_issues}</small>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Recomendaciones -->
                                <div class="recommendations mb-4">
                                    <h6>Recomendaciones</h6>
                                    ${report.recommendations.map(rec => `
                                        <div class="alert alert-${rec.priority === 'critical' ? 'danger' : rec.priority === 'high' ? 'warning' : 'info'}">
                                            <h6>${rec.title}</h6>
                                            <p>${rec.description}</p>
                                            <small>Acción: ${rec.action}</small>
                                        </div>
                                    `).join('')}
                                </div>
                                
                                <!-- Próximos pasos -->
                                <div class="next-steps mb-4">
                                    <h6>Próximos Pasos</h6>
                                    <ol>
                                        ${report.next_steps.map(step => `
                                            <li>
                                                <strong>${step.title}</strong><br>
                                                <small class="text-muted">${step.description}</small><br>
                                                <small class="text-muted">Tiempo estimado: ${step.estimated_time}</small>
                                            </li>
                                        `).join('')}
                                    </ol>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                            <button type="button" class="btn btn-primary" onclick="downloadReport()">
                                <i class="fas fa-download"></i> Descargar Reporte
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Agregar modal al DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('finalReportModal'));
        modal.show();
        
        // Guardar reporte para descarga
        window.currentReport = report;
    }

    async exportChecklist() {
        console.log('Exportando checklist...');
        
        try {
            if (!this.projectData.final_checklist) {
                throw new Error('No hay checklist final disponible');
            }
            
            const response = await fetch(`/api/madrid/final-checklist/${this.projectData.jobId}/export-json`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Descargar archivo JSON
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `checklist_${this.projectData.jobId}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            this.showAlert('Checklist exportado correctamente', 'success');
            
        } catch (error) {
            console.error('Error exportando checklist:', error);
            this.showAlert('Error exportando checklist: ' + error.message, 'danger');
        }
    }
}

// Initialize the system when the page loads
const madridSystem = new MadridVerificationSystem();

// Global functions for HTML onclick handlers
function changeStep(direction) {
    console.log('changeStep llamado con dirección:', direction);
    if (madridSystem) {
        madridSystem.changeStep(direction);
    } else {
        console.error('MadridSystem no está inicializado');
    }
}

function startMadridVerification() {
    console.log('startMadridVerification llamado');
    if (madridSystem) {
        madridSystem.startMadridVerification();
    } else {
        console.error('MadridSystem no está inicializado');
    }
}

function scrollToSection(sectionId) {
    console.log('scrollToSection llamado con:', sectionId);
    const element = document.getElementById(sectionId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}