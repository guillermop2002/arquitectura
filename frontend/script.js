// Sistema de Verificación Arquitectónica Madrid - Frontend JavaScript

class MadridVerificationSystem {
    constructor() {
        this.currentStep = 1;
        this.maxSteps = 5;
        this.projectData = {
            is_existing_building: false,
            primary_use: null,
            has_secondary_uses: false,
            secondary_uses: [],
            files: [],
            jobId: null
        };
        this.init();
    }

    init() {
        // Esperar a que el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.setupEventListeners();
                this.updateStepVisibility();
                this.updateNavigationButtons();
            });
        } else {
            this.setupEventListeners();
            this.updateStepVisibility();
            this.updateNavigationButtons();
        }
    }

    setupEventListeners() {
        console.log('Configurando event listeners...');
        
        // File input change
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                console.log('Archivos seleccionados:', e.target.files);
                this.handleFileSelection(e.target.files);
            });
        }

        // Drag and drop
        const uploadArea = document.getElementById('uploadArea');
        if (uploadArea) {
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
                console.log('Drag over');
            });

            uploadArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                console.log('Drag leave');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                console.log('Files dropped:', e.dataTransfer.files);
                this.handleFileSelection(e.dataTransfer.files);
            });

            // Click to select files
            uploadArea.addEventListener('click', () => {
                console.log('Upload area clicked');
                const fileInput = document.getElementById('fileInput');
                if (fileInput) {
                    fileInput.click();
                }
            });
        }

        // Building type toggle
        const buildingToggle = document.getElementById('isExistingBuilding');
        if (buildingToggle) {
            buildingToggle.addEventListener('change', () => {
                console.log('Building type changed:', buildingToggle.checked);
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
        document.querySelectorAll('input[id^="sec_"]').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const useType = e.target.value;
                console.log('Secondary use changed:', useType, e.target.checked);
                this.toggleSecondaryUse(useType);
            });
        });
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
        const floorSelectorId = `floors_${useType.replace('-', '_')}`;
        
        console.log('Creating floor selector for:', useType);
        
        const floorSelector = document.createElement('div');
        floorSelector.className = 'card mb-3';
        floorSelector.id = `floor_selector_${useType.replace('-', '_')}`;
        floorSelector.innerHTML = `
            <div class="card-header">
                <h6 class="mb-0">Plantas para uso: ${this.getUseDisplayName(useType)}</h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-8">
                        <label class="form-label">Selecciona las plantas donde se encuentra este uso:</label>
                        <div class="floor-selection">
                            <div class="row">
                                <div class="col-md-4">
                                    <h6>Plantas Especiales:</h6>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" value="-0.5" id="${floorSelectorId}_entresotano" onchange="madridSystem.updateSecondaryUseFloors('${useType}')">
                                        <label class="form-check-label" for="${floorSelectorId}_entresotano">Entresótano (-0.5)</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" value="0" id="${floorSelectorId}_planta_baja" onchange="madridSystem.updateSecondaryUseFloors('${useType}')">
                                        <label class="form-check-label" for="${floorSelectorId}_planta_baja">Planta Baja (0)</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" value="0.5" id="${floorSelectorId}_entreplanta" onchange="madridSystem.updateSecondaryUseFloors('${useType}')">
                                        <label class="form-check-label" for="${floorSelectorId}_entreplanta">Entreplanta (0.5)</label>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <h6>Sótanos (-100 a -1):</h6>
                                    <div class="floor-range">
                                        <input type="number" class="form-control form-control-sm mb-2" placeholder="Desde" min="-100" max="-1" id="${floorSelectorId}_sotano_desde">
                                        <input type="number" class="form-control form-control-sm" placeholder="Hasta" min="-100" max="-1" id="${floorSelectorId}_sotano_hasta">
                                        <button type="button" class="btn btn-sm btn-outline-primary mt-2" onclick="madridSystem.addFloorRange('${useType}', 'sotano')">Agregar Rango</button>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <h6>Pisos (1 a 100):</h6>
                                    <div class="floor-range">
                                        <input type="number" class="form-control form-control-sm mb-2" placeholder="Desde" min="1" max="100" id="${floorSelectorId}_piso_desde">
                                        <input type="number" class="form-control form-control-sm" placeholder="Hasta" min="1" max="100" id="${floorSelectorId}_piso_hasta">
                                        <button type="button" class="btn btn-sm btn-outline-primary mt-2" onclick="madridSystem.addFloorRange('${useType}', 'piso')">Agregar Rango</button>
                                    </div>
                                </div>
                            </div>
                            <div class="mt-3">
                                <h6>Plantas Seleccionadas:</h6>
                                <div id="${floorSelectorId}_selected" class="selected-floors">
                                    <span class="text-muted">Ninguna planta seleccionada</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(floorSelector);
    }

    removeFloorSelector(useType) {
        const selector = document.getElementById(`floor_selector_${useType.replace('-', '_')}`);
        if (selector) {
            selector.remove();
        }
    }

    updateSecondaryUseFloors(useType) {
        const floorSelectorId = `floors_${useType.replace('-', '_')}`;
        const checkboxes = document.querySelectorAll(`input[id^="${floorSelectorId}_"]:checked`);
        
        const floors = Array.from(checkboxes).map(cb => parseFloat(cb.value));
        
        console.log('Updating floors for:', useType, floors);
        
        // Update project data
        const secondaryUse = this.projectData.secondary_uses.find(use => use.use_type === useType);
        if (secondaryUse) {
            secondaryUse.floors = floors;
        }
        
        // Update display
        this.updateSelectedFloorsDisplay(useType, floors);
        this.updateNavigationButtons();
    }

    updateSelectedFloorsDisplay(useType, floors) {
        const floorSelectorId = `floors_${useType.replace('-', '_')}`;
        const display = document.getElementById(`${floorSelectorId}_selected`);
        
        if (floors.length === 0) {
            display.innerHTML = '<span class="text-muted">Ninguna planta seleccionada</span>';
        } else {
            const floorNames = floors.map(floor => {
                if (floor === -0.5) return 'Entresótano';
                if (floor === 0) return 'Planta Baja';
                if (floor === 0.5) return 'Entreplanta';
                if (floor < 0) return `Sótano ${Math.abs(floor)}`;
                return `Planta ${floor}`;
            });
            display.innerHTML = floorNames.map(name => `<span class="badge bg-primary me-1">${name}</span>`).join('');
        }
    }

    getUseDisplayName(useType) {
        const names = {
            'residencial': 'Residencial',
            'industrial': 'Industrial',
            'garaje-aparcamiento': 'Garaje-Aparcamiento',
            'servicios_terciarios': 'Servicios Terciarios',
            'dotacional_zona_verde': 'Dotacional zona verde',
            'dotacional_deportivo': 'Dotacional Deportivo',
            'dotacional_equipamiento': 'Dotacional equipamiento',
            'dotacional_servicios_publicos': 'Dotacional servicios públicos',
            'dotacional_administracion_publica': 'Dotacional administración pública',
            'dotacional_infraestructural': 'Dotacional Infraestructural',
            'dotacional_via_publica': 'Dotacional Vía Pública',
            'dotacional_transporte': 'Dotacional Transporte'
        };
        return names[useType] || useType;
    }

    addFloorRange(useType, type) {
        const floorSelectorId = `floors_${useType.replace('-', '_')}`;
        const desde = document.getElementById(`${floorSelectorId}_${type}_desde`).value;
        const hasta = document.getElementById(`${floorSelectorId}_${type}_hasta`).value;
        
        if (!desde || !hasta) {
            this.showAlert('Por favor, completa ambos campos del rango.', 'warning');
            return;
        }
        
        const start = parseInt(desde);
        const end = parseInt(hasta);
        
        if (start > end) {
            this.showAlert('El valor "desde" debe ser menor o igual que "hasta".', 'warning');
            return;
        }
        
        // Add range to floors
        const secondaryUse = this.projectData.secondary_uses.find(use => use.use_type === useType);
        if (secondaryUse) {
            for (let i = start; i <= end; i++) {
                if (!secondaryUse.floors.includes(i)) {
                    secondaryUse.floors.push(i);
                }
            }
            // Sort floors
            secondaryUse.floors.sort((a, b) => a - b);
        }
        
        // Update display
        this.updateSelectedFloorsDisplay(useType, secondaryUse.floors);
        this.updateNavigationButtons();
    }

    handleFileSelection(files) {
        console.log('Handling file selection:', files);
        
        const fileArray = Array.from(files).filter(file => file.type === 'application/pdf');
        
        if (fileArray.length === 0) {
            this.showAlert('Por favor, selecciona solo archivos PDF.', 'warning');
            return;
        }

        this.projectData.files = fileArray;
        this.displayFileList();
        this.updateNavigationButtons();
    }

    displayFileList() {
        const fileList = document.getElementById('fileList');
        fileList.innerHTML = '';

        this.projectData.files.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <i class="fas fa-file-pdf file-icon"></i>
                <div class="file-info">
                    <div class="fw-bold">${file.name}</div>
                    <small class="text-muted">${this.formatFileSize(file.size)}</small>
                </div>
                <div class="file-actions">
                    <button class="btn btn-sm btn-outline-danger" onclick="madridSystem.removeFile(${index})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            fileList.appendChild(fileItem);
        });
    }

    removeFile(index) {
        this.projectData.files.splice(index, 1);
        this.displayFileList();
        this.updateNavigationButtons();
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    changeStep(direction) {
        console.log('Changing step:', direction, 'from', this.currentStep);
        
        if (direction > 0 && this.currentStep < this.maxSteps) {
            if (this.validateCurrentStep()) {
                this.currentStep++;
            }
        } else if (direction < 0 && this.currentStep > 1) {
            this.currentStep--;
        }

        this.updateStepVisibility();
        this.updateNavigationButtons();
    }

    validateCurrentStep() {
        console.log('Validating step:', this.currentStep);
        
        switch (this.currentStep) {
            case 1:
                // Building type is optional, always valid
                return true;
            case 2:
                if (!this.projectData.primary_use) {
                    this.showAlert('Por favor, selecciona el uso principal del edificio.', 'warning');
                    return false;
                }
                break;
            case 3:
                if (this.projectData.has_secondary_uses) {
                    if (this.projectData.secondary_uses.length === 0) {
                        this.showAlert('Por favor, selecciona al menos un uso secundario.', 'warning');
                        return false;
                    }
                    // Check if all secondary uses have floors selected
                    for (const use of this.projectData.secondary_uses) {
                        if (use.floors.length === 0) {
                            this.showAlert(`Por favor, selecciona las plantas para el uso: ${this.getUseDisplayName(use.use_type)}`, 'warning');
                            return false;
                        }
                    }
                }
                break;
            case 4:
                if (this.projectData.files.length === 0) {
                    this.showAlert('Por favor, sube al menos un archivo PDF (memoria o planos).', 'warning');
                    return false;
                }
                break;
        }
        return true;
    }

    updateStepVisibility() {
        console.log('Updating step visibility, current step:', this.currentStep);
        
        document.querySelectorAll('.verification-step').forEach((step, index) => {
            const isActive = index + 1 === this.currentStep;
            step.classList.toggle('active', isActive);
            console.log(`Step ${index + 1} active:`, isActive);
        });
    }

    updateNavigationButtons() {
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');

        if (prevBtn) {
            prevBtn.disabled = this.currentStep === 1;
        }

        if (nextBtn) {
            if (this.currentStep === this.maxSteps) {
                nextBtn.innerHTML = '<i class="fas fa-check me-2"></i>Iniciar Verificación Madrid';
                nextBtn.onclick = () => this.startMadridVerification();
            } else {
                nextBtn.innerHTML = 'Siguiente <i class="fas fa-arrow-right ms-2"></i>';
                nextBtn.onclick = () => this.changeStep(1);
                nextBtn.disabled = !this.canProceedToNextStep();
            }
        }
        
        console.log('Navigation buttons updated. Can proceed:', this.canProceedToNextStep());
    }

    canProceedToNextStep() {
        switch (this.currentStep) {
            case 1:
                return true; // Building type is optional
            case 2:
                return this.projectData.primary_use !== null;
            case 3:
                if (this.projectData.has_secondary_uses) {
                    return this.projectData.secondary_uses.length > 0 && 
                           this.projectData.secondary_uses.every(use => use.floors.length > 0);
                }
                return true;
            case 4:
                return this.projectData.files.length > 0;
            default:
                return true;
        }
    }

    async startMadridVerification() {
        console.log('Starting Madrid verification...');
        
        if (!this.validateCurrentStep()) {
            return;
        }

        this.currentStep = 5;
        this.updateStepVisibility();
        this.updateNavigationButtons();

        try {
            // Show loading state
            this.showVerificationStatus('Iniciando verificación Madrid...', 'loading');

            // Prepare project data for Madrid API
            const madridProjectData = {
                is_existing_building: this.projectData.is_existing_building,
                primary_use: this.projectData.primary_use,
                has_secondary_uses: this.projectData.has_secondary_uses,
                secondary_uses: this.projectData.secondary_uses,
                files: this.projectData.files.map(file => file.name) // Just file names for now
            };

            console.log('Sending Madrid project data:', madridProjectData);

            // Start Madrid verification
            const response = await fetch('/madrid/integration/process-project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    project_data: madridProjectData,
                    auto_resolve_ambiguities: false,
                    generate_report: true
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.projectData.jobId = result.project_id;

            // Show success and display results
            this.showVerificationStatus('Verificación Madrid completada exitosamente!', 'success');
            this.displayResults(result);

        } catch (error) {
            console.error('Error during Madrid verification:', error);
            this.showVerificationStatus('Error durante la verificación Madrid. Por favor, inténtalo de nuevo.', 'error');
        }
    }

    showVerificationStatus(message, type) {
        const statusDiv = document.getElementById('verificationStatus');
        let iconClass = 'fas fa-spinner fa-spin';
        let textClass = 'text-primary';

        switch (type) {
            case 'success':
                iconClass = 'fas fa-check-circle';
                textClass = 'text-success';
                break;
            case 'error':
                iconClass = 'fas fa-exclamation-circle';
                textClass = 'text-danger';
                break;
            case 'loading':
                iconClass = 'fas fa-spinner fa-spin';
                textClass = 'text-primary';
                break;
        }

        statusDiv.innerHTML = `
            <div class="verification-status">
                <i class="${iconClass} fa-3x ${textClass} mb-3"></i>
                <p class="status-text ${textClass}">${message}</p>
            </div>
        `;
    }

    displayResults(result) {
        const resultsContainer = document.getElementById('resultsContainer');
        const resultsContent = document.getElementById('resultsContent');

        // Show results section
        resultsContainer.classList.remove('d-none');
        resultsContainer.scrollIntoView({ behavior: 'smooth' });

        // Generate results HTML
        resultsContent.innerHTML = this.generateMadridResultsHTML(result);
    }

    generateMadridResultsHTML(result) {
        const verification = result.verification_result || {};
        const summary = {
            overall_status: verification.overall_status || 'unknown',
            compliance_percentage: verification.compliance_percentage || 0,
            total_items: verification.total_items || 0,
            compliant_items: verification.compliant_items || 0,
            non_compliant_items: verification.non_compliant_items || 0
        };

        return `
            <div class="row">
                <!-- Summary Cards -->
                <div class="col-md-3">
                    <div class="summary-card">
                        <div class="summary-number">${summary.total_items}</div>
                        <div class="summary-label">Total de Items</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="summary-card" style="background: linear-gradient(135deg, #28a745, #20c997);">
                        <div class="summary-number">${summary.compliant_items}</div>
                        <div class="summary-label">Cumplidos</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="summary-card" style="background: linear-gradient(135deg, #dc3545, #fd7e14);">
                        <div class="summary-number">${summary.non_compliant_items}</div>
                        <div class="summary-label">No Cumplidos</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="summary-card" style="background: linear-gradient(135deg, #0dcaf0, #6f42c1);">
                        <div class="summary-number">${summary.compliance_percentage}%</div>
                        <div class="summary-label">Cumplimiento</div>
                    </div>
                </div>
            </div>

            <!-- Status -->
            <div class="mt-4">
                <div class="alert alert-${summary.overall_status === 'compliant' ? 'success' : 'warning'}">
                    <h5 class="alert-heading">
                        <i class="fas fa-${summary.overall_status === 'compliant' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
                        Estado General: ${summary.overall_status === 'compliant' ? 'CUMPLE' : 'NO CUMPLE'}
                    </h5>
                    <p class="mb-0">El proyecto ${summary.overall_status === 'compliant' ? 'cumple' : 'no cumple'} con la normativa PGOUM de Madrid.</p>
                </div>
            </div>

            <!-- Project Data Summary -->
            <div class="mt-4">
                <h4>Datos del Proyecto Madrid</h4>
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Tipo de edificio:</strong> ${this.projectData.is_existing_building ? 'Existente' : 'Nuevo'}</p>
                        <p><strong>Uso principal:</strong> ${this.getUseDisplayName(this.projectData.primary_use)}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Usos secundarios:</strong> ${this.projectData.has_secondary_uses ? this.projectData.secondary_uses.length : 'Ninguno'}</p>
                        <p><strong>Archivos subidos:</strong> ${this.projectData.files.length}</p>
                    </div>
                </div>
            </div>

            <!-- Actions -->
            <div class="mt-4 text-center">
                <button class="btn btn-primary me-2" onclick="madridSystem.downloadReport()">
                    <i class="fas fa-download me-2"></i>
                    Descargar Reporte Madrid
                </button>
                <button class="btn btn-outline-primary" onclick="madridSystem.startNewVerification()">
                    <i class="fas fa-plus me-2"></i>
                    Nueva Verificación
                </button>
            </div>
        `;
    }

    downloadReport() {
        if (this.projectData.jobId) {
            window.open(`/madrid/integration/reports/${this.projectData.jobId}`, '_blank');
        } else {
            this.showAlert('No hay reporte disponible para descargar.', 'warning');
        }
    }

    startNewVerification() {
        // Reset form
        this.currentStep = 1;
        this.projectData = {
            is_existing_building: false,
            primary_use: null,
            has_secondary_uses: false,
            secondary_uses: [],
            files: [],
            jobId: null
        };

        // Reset UI
        document.getElementById('isExistingBuilding').checked = false;
        document.getElementById('primaryUse').value = '';
        document.getElementById('hasSecondaryUses').checked = false;
        document.getElementById('secondaryUsesSection').classList.add('d-none');
        document.getElementById('secondaryUsesFloors').innerHTML = '';
        document.getElementById('fileList').innerHTML = '';
        document.getElementById('fileInput').value = '';
        document.getElementById('resultsContainer').classList.add('d-none');

        // Clear all secondary use checkboxes
        document.querySelectorAll('input[id^="sec_"]').forEach(checkbox => {
            checkbox.checked = false;
        });

        this.updateStepVisibility();
        this.updateNavigationButtons();

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(alertDiv);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }
}

// Global functions for HTML onclick handlers
function toggleBuildingType() {
    if (window.madridSystem) {
        window.madridSystem.toggleBuildingType();
    }
}

function updatePrimaryUse() {
    if (window.madridSystem) {
        window.madridSystem.updatePrimaryUse();
    }
}

function toggleSecondaryUses() {
    if (window.madridSystem) {
        window.madridSystem.toggleSecondaryUses();
    }
}

function toggleSecondaryUse(useType) {
    if (window.madridSystem) {
        window.madridSystem.toggleSecondaryUse(useType);
    }
}

function updateSecondaryUseFloors(useType) {
    if (window.madridSystem) {
        window.madridSystem.updateSecondaryUseFloors(useType);
    }
}

function addFloorRange(useType, type) {
    if (window.madridSystem) {
        window.madridSystem.addFloorRange(useType, type);
    }
}

function changeStep(direction) {
    if (window.madridSystem) {
        window.madridSystem.changeStep(direction);
    }
}

function startMadridVerification() {
    if (window.madridSystem) {
        window.madridSystem.startMadridVerification();
    }
}

function scrollToSection(sectionId) {
    document.getElementById(sectionId).scrollIntoView({ behavior: 'smooth' });
}

// Initialize the system when the page loads
let madridSystem;
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing Madrid system...');
    madridSystem = new MadridVerificationSystem();
    window.madridSystem = madridSystem; // Make it globally available
    console.log('Madrid system initialized');
});