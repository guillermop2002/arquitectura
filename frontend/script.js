// Sistema de Verificación Arquitectónica - Frontend JavaScript

class VerificationSystem {
    constructor() {
        this.currentStep = 1;
        this.maxSteps = 4;
        this.projectData = {
            type: null,
            files: [],
            details: {},
            jobId: null
        };
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateStepVisibility();
        this.updateNavigationButtons();
    }

    setupEventListeners() {
        // File input change
        document.getElementById('fileInput').addEventListener('change', (e) => {
            this.handleFileSelection(e.target.files);
        });

        // Drag and drop
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            this.handleFileSelection(e.dataTransfer.files);
        });

        // Click to select files
        uploadArea.addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    }

    selectProjectType(type) {
        this.projectData.type = type;
        
        // Update UI
        document.querySelectorAll('.project-type-card').forEach(card => {
            card.classList.remove('selected');
        });
        event.currentTarget.classList.add('selected');
        
        this.updateNavigationButtons();
    }

    handleFileSelection(files) {
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
                    <button class="btn btn-sm btn-outline-danger" onclick="verificationSystem.removeFile(${index})">
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
        switch (this.currentStep) {
            case 1:
                if (!this.projectData.type) {
                    this.showAlert('Por favor, selecciona el tipo de proyecto.', 'warning');
                    return false;
                }
                break;
            case 2:
                if (this.projectData.files.length === 0) {
                    this.showAlert('Por favor, sube al menos un archivo PDF.', 'warning');
                    return false;
                }
                break;
            case 3:
                const projectName = document.getElementById('projectName').value.trim();
                const buildingUse = document.getElementById('buildingUse').value;
                if (!projectName || !buildingUse) {
                    this.showAlert('Por favor, completa todos los campos requeridos.', 'warning');
                    return false;
                }
                this.projectData.details = {
                    name: projectName,
                    location: document.getElementById('projectLocation').value.trim(),
                    buildingUse: buildingUse,
                    totalArea: document.getElementById('totalArea').value
                };
                break;
        }
        return true;
    }

    updateStepVisibility() {
        document.querySelectorAll('.verification-step').forEach((step, index) => {
            step.classList.toggle('active', index + 1 === this.currentStep);
        });
    }

    updateNavigationButtons() {
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');

        prevBtn.disabled = this.currentStep === 1;

        if (this.currentStep === this.maxSteps) {
            nextBtn.innerHTML = '<i class="fas fa-check me-2"></i>Iniciar Verificación';
            nextBtn.onclick = () => this.startVerification();
        } else {
            nextBtn.innerHTML = 'Siguiente <i class="fas fa-arrow-right ms-2"></i>';
            nextBtn.onclick = () => this.changeStep(1);
            nextBtn.disabled = !this.canProceedToNextStep();
        }
    }

    canProceedToNextStep() {
        switch (this.currentStep) {
            case 1:
                return this.projectData.type !== null;
            case 2:
                return this.projectData.files.length > 0;
            case 3:
                const projectName = document.getElementById('projectName').value.trim();
                const buildingUse = document.getElementById('buildingUse').value;
                return projectName && buildingUse;
            default:
                return true;
        }
    }

    async startVerification() {
        if (!this.validateCurrentStep()) {
            return;
        }

        this.currentStep = 4;
        this.updateStepVisibility();
        this.updateNavigationButtons();

        try {
            // Show loading state
            this.showVerificationStatus('Iniciando verificación...', 'loading');

            // Prepare form data
            const formData = new FormData();
            this.projectData.files.forEach(file => {
                formData.append('files', file);
            });
            formData.append('is_existing_building', this.projectData.type === 'existing');

            // Start verification
            const response = await fetch('/verify', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.projectData.jobId = result.job_id;

            // Show success and continue with next phase
            this.showVerificationStatus('Verificación inicial completada. Continuando con análisis completo...', 'success');
            
            // Continue with complete verification
            await this.continueVerification();

        } catch (error) {
            console.error('Error during verification:', error);
            this.showVerificationStatus('Error durante la verificación. Por favor, inténtalo de nuevo.', 'error');
        }
    }

    async continueVerification() {
        try {
            this.showVerificationStatus('Realizando verificación normativa completa...', 'loading');

            const formData = new FormData();
            formData.append('job_id', this.projectData.jobId);
            formData.append('is_existing_building', this.projectData.type === 'existing');

            const response = await fetch('/continue-verification', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            // Show final results
            this.showVerificationStatus('Verificación completada exitosamente!', 'success');
            this.displayResults(result);

        } catch (error) {
            console.error('Error during complete verification:', error);
            this.showVerificationStatus('Error durante la verificación completa. Por favor, inténtalo de nuevo.', 'error');
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
        resultsContent.innerHTML = this.generateResultsHTML(result);
    }

    generateResultsHTML(result) {
        const issues = result.issues || [];
        const summary = result.summary || {};

        return `
            <div class="row">
                <!-- Summary Cards -->
                <div class="col-md-3">
                    <div class="summary-card">
                        <div class="summary-number">${summary.total_issues || 0}</div>
                        <div class="summary-label">Total de Issues</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="summary-card" style="background: linear-gradient(135deg, #dc3545, #fd7e14);">
                        <div class="summary-number">${summary.high_severity || 0}</div>
                        <div class="summary-label">Alta Prioridad</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="summary-card" style="background: linear-gradient(135deg, #ffc107, #fd7e14);">
                        <div class="summary-number">${summary.medium_severity || 0}</div>
                        <div class="summary-label">Media Prioridad</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="summary-card" style="background: linear-gradient(135deg, #0dcaf0, #6f42c1);">
                        <div class="summary-number">${summary.low_severity || 0}</div>
                        <div class="summary-label">Baja Prioridad</div>
                    </div>
                </div>
            </div>

            <!-- Issues List -->
            <div class="mt-5">
                <h3>Issues Detectados</h3>
                ${issues.length > 0 ? issues.map(issue => `
                    <div class="issue-card ${issue.severity?.toLowerCase() || 'low'}">
                        <div class="issue-title">
                            <span class="status-indicator ${issue.severity?.toLowerCase() || 'low'}"></span>
                            ${issue.title || 'Issue sin título'}
                        </div>
                        <div class="issue-description">
                            ${issue.description || 'Sin descripción disponible'}
                        </div>
                        ${issue.recommendation ? `
                            <div class="issue-recommendation">
                                <strong>Recomendación:</strong> ${issue.recommendation}
                            </div>
                        ` : ''}
                        ${issue.reference ? `
                            <div class="mt-2">
                                <small class="text-muted">
                                    <i class="fas fa-book me-1"></i>
                                    Referencia: ${issue.reference}
                                </small>
                            </div>
                        ` : ''}
                    </div>
                `).join('') : '<p class="text-muted">No se detectaron issues en este proyecto.</p>'}
            </div>

            <!-- Actions -->
            <div class="mt-4 text-center">
                <button class="btn btn-primary me-2" onclick="verificationSystem.downloadReport()">
                    <i class="fas fa-download me-2"></i>
                    Descargar Reporte
                </button>
                <button class="btn btn-outline-primary" onclick="verificationSystem.startNewVerification()">
                    <i class="fas fa-plus me-2"></i>
                    Nueva Verificación
                </button>
            </div>
        `;
    }

    downloadReport() {
        if (this.projectData.jobId) {
            window.open(`/project/${this.projectData.jobId}/report`, '_blank');
        } else {
            this.showAlert('No hay reporte disponible para descargar.', 'warning');
        }
    }

    startNewVerification() {
        // Reset form
        this.currentStep = 1;
        this.projectData = {
            type: null,
            files: [],
            details: {},
            jobId: null
        };

        // Reset UI
        document.querySelectorAll('.project-type-card').forEach(card => {
            card.classList.remove('selected');
        });
        document.getElementById('fileList').innerHTML = '';
        document.getElementById('fileInput').value = '';
        document.getElementById('projectName').value = '';
        document.getElementById('projectLocation').value = '';
        document.getElementById('buildingUse').value = '';
        document.getElementById('totalArea').value = '';
        document.getElementById('resultsContainer').classList.add('d-none');

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
function selectProjectType(type) {
    verificationSystem.selectProjectType(type);
}

function changeStep(direction) {
    verificationSystem.changeStep(direction);
}

function startVerification() {
    verificationSystem.startVerification();
}

function scrollToSection(sectionId) {
    document.getElementById(sectionId).scrollIntoView({ behavior: 'smooth' });
}

// Initialize the system when the page loads
let verificationSystem;
document.addEventListener('DOMContentLoaded', () => {
    verificationSystem = new VerificationSystem();
});
