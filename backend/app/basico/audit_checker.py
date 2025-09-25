"""
Auditoría completa del sistema básico para verificar que todo está listo para producción.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import importlib
import inspect
import os
import sys

logger = logging.getLogger("basico.audit")

class BasicoAuditChecker:
    """Auditor para verificar que el sistema está listo para producción"""
    
    def __init__(self):
        self.audit_results = {}
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Configurar logger para auditoría"""
        logger = logging.getLogger("basico.audit")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def run_complete_audit(self) -> Dict[str, Any]:
        """Ejecutar auditoría completa del sistema básico"""
        
        self.logger.info("🔍 Iniciando auditoría completa del sistema básico")
        
        # Ejecutar todas las verificaciones
        components_check = self._check_components()
        dependencies_check = self._check_dependencies()
        config_check = self._check_configuration()
        normative_check = self._check_normative_files()
        ai_check = self._check_ai_integration()
        ocr_check = self._check_ocr_processing()
        
        # Calcular puntuaciones
        individual_scores = {
            "components": self._calculate_component_score(components_check),
            "dependencies": self._calculate_dependency_score(dependencies_check),
            "configuration": self._calculate_config_score(config_check),
            "normative_files": self._calculate_normative_score(normative_check),
            "ai_integration": self._calculate_ai_score(ai_check),
            "ocr_processing": self._calculate_ocr_score(ocr_check)
        }
        
        # Calcular puntuación general (ponderada)
        weights = {
            "components": 0.25,
            "dependencies": 0.20,
            "configuration": 0.15,
            "normative_files": 0.15,
            "ai_integration": 0.15,
            "ocr_processing": 0.10
        }
        
        overall_score = sum(
            individual_scores[key] * weights[key] 
            for key in weights.keys()
        )
        
        # Determinar estado del sistema
        system_status = self._determine_system_status(overall_score)
        readiness_level = self._determine_readiness_level(overall_score)
        production_ready = overall_score >= 80.0
        
        # Generar recomendaciones
        all_checks = {
            'components': components_check,
            'dependencies': dependencies_check,
            'configuration': config_check,
            'normative_files': normative_check,
            'ai_integration': ai_check,
            'ocr_processing': ocr_check,
            'individual_scores': individual_scores
        }
        recommendations = self._generate_recommendations(all_checks)
        
        audit_result = {
            "audit_timestamp": self._get_timestamp(),
            "system_status": system_status,
            "overall_score": round(overall_score, 1),
            "readiness_level": readiness_level,
            "production_ready": production_ready,
            "individual_scores": {k: round(v, 1) for k, v in individual_scores.items()},
            "detailed_checks": {
                "components": components_check,
                "dependencies": dependencies_check,
                "configuration": config_check,
                "normative_files": normative_check,
                "ai_integration": ai_check,
                "ocr_processing": ocr_check
            },
            "recommendations": recommendations,
            "next_steps": self._generate_next_steps(individual_scores)
        }
        
        self.audit_results = audit_result
        return audit_result
    
    def _calculate_component_score(self, components_check: Dict[str, Any]) -> float:
        """Calcular puntuación de componentes"""
        if components_check.get('total_count', 0) == 0:
            return 0.0
        return (components_check.get('working_count', 0) / components_check.get('total_count', 1)) * 100
    
    def _calculate_dependency_score(self, dependencies_check: Dict[str, Any]) -> float:
        """Calcular puntuación de dependencias"""
        if dependencies_check.get('total_count', 0) == 0:
            return 0.0
        return (dependencies_check.get('working_count', 0) / dependencies_check.get('total_count', 1)) * 100
    
    def _calculate_config_score(self, config_check: Dict[str, Any]) -> float:
        """Calcular puntuación de configuración"""
        if config_check.get('total_count', 0) == 0:
            return 0.0
        return (config_check.get('working_count', 0) / config_check.get('total_count', 1)) * 100
    
    def _calculate_normative_score(self, normative_check: Dict[str, Any]) -> float:
        """Calcular puntuación de archivos normativos"""
        score = 0.0
        if normative_check.get('directory_exists', False):
            score += 40
        if normative_check.get('anexo1_exists', False):
            score += 60
        return score
    
    def _calculate_ai_score(self, ai_check: Dict[str, Any]) -> float:
        """Calcular puntuación de integración IA"""
        status = ai_check.get('status')
        if status == 'good':
            return 100.0
        elif status == 'partial':
            return 75.0
        else:
            return 0.0
    
    def _calculate_ocr_score(self, ocr_check: Dict[str, Any]) -> float:
        """Calcular puntuación de procesamiento OCR"""
        return 100.0 if ocr_check.get('status') == 'good' else 0.0
    
    def _determine_system_status(self, overall_score: float) -> str:
        """Determinar estado del sistema"""
        if overall_score >= 90:
            return "production_ready"
        elif overall_score >= 70:
            return "needs_minor_fixes"
        else:
            return "needs_major_fixes"
    
    def _determine_readiness_level(self, overall_score: float) -> str:
        """Determinar nivel de preparación"""
        if overall_score >= 95:
            return "Excelente"
        elif overall_score >= 85:
            return "Bueno"
        elif overall_score >= 70:
            return "Regular"
        else:
            return "Deficiente"
    
    def _generate_next_steps(self, individual_scores: Dict[str, float]) -> List[str]:
        """Generar próximos pasos"""
        steps = []
        for category, score in individual_scores.items():
            if score < 80:
                steps.append(f"Mejorar {category} (puntuación actual: {score:.1f}%)")
        
        if not steps:
            steps.append("Sistema listo para producción")
        
        return steps
    
    def _get_timestamp(self) -> str:
        """Obtener timestamp actual"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _check_components(self) -> Dict[str, Any]:
        """Verificar que todos los componentes del sistema básico estén disponibles"""
        
        components = {
            "SessionManager": "backend.app.basico.session_manager.BasicoSessionManager",
            "Analyzer": "backend.app.basico.analyzer.BasicoAnalyzer",
            "AnexoVerifier": "backend.app.basico.anexo_verifier.BasicoAnexoVerifier",
            "OCRProcessor": "backend.app.basico.ocr_processor.BasicoOCRProcessor",
            "AIClient": "backend.app.basico.ai_client.BasicoAIClient",
            "FileManager": "backend.app.core.file_manager.FileManager",
            "PromptManager": "backend.app.basico.basico_prompts",
            "ConfigManager": "backend.app.core.config.get_config"
        }
        
        component_status = {}
        working_components = 0
        
        for component_name, module_path in components.items():
            try:
                # Intentar importar el módulo/clase
                if '.' in module_path:
                    module_name, class_name = module_path.rsplit('.', 1)
                    module = importlib.import_module(module_name)
                    
                    if hasattr(module, class_name):
                        # Intentar instanciar la clase
                        component_class = getattr(module, class_name)
                        if callable(component_class):
                            instance = component_class()
                            status = "working"
                            working_components += 1
                        else:
                            status = "not_callable"
                    else:
                        status = "class_not_found"
                else:
                    # Es un módulo simple
                    module = importlib.import_module(module_path)
                    status = "working"
                    working_components += 1
                
                component_status[component_name] = {
                    "status": status,
                    "module_path": module_path,
                    "available": status == "working"
                }
                
            except ImportError as e:
                component_status[component_name] = {
                    "status": "import_error",
                    "module_path": module_path,
                    "available": False,
                    "error": str(e)
                }
            except Exception as e:
                component_status[component_name] = {
                    "status": "error",
                    "module_path": module_path,
                    "available": False,
                    "error": str(e)
                }
        
        return {
            "total_count": len(components),
            "working_count": working_components,
            "component_details": component_status,
            "all_working": working_components == len(components)
        }
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Verificar dependencias críticas"""
        
        critical_dependencies = {
            "fastapi": "FastAPI framework",
            "groq": "Groq AI client",
            "PyMuPDF": "PDF processing (fitz)",
            "pytesseract": "OCR processing",
            "redis": "Session storage",
            "Pillow": "Image processing"
        }
        
        dependency_status = {}
        available_deps = 0
        
        for dep_name, description in critical_dependencies.items():
            try:
                if dep_name == "PyMuPDF":
                    import fitz
                elif dep_name == "Pillow":
                    import PIL
                else:
                    importlib.import_module(dep_name.lower())
                
                dependency_status[dep_name] = {
                    "available": True,
                    "description": description,
                    "status": "installed"
                }
                available_deps += 1
                
            except ImportError:
                dependency_status[dep_name] = {
                    "available": False,
                    "description": description,
                    "status": "missing"
                }
        
        return {
            "total_count": len(critical_dependencies),
            "working_count": available_deps,
            "dependency_details": dependency_status,
            "all_available": available_deps == len(critical_dependencies)
        }
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Verificar configuración del sistema"""
        
        config_checks = {
            "environment_variables": self._check_env_variables(),
            "directories": self._check_directories(),
            "file_permissions": self._check_file_permissions(),
            "logging_config": self._check_logging_config()
        }
        
        all_good = all(check.get("status") == "good" for check in config_checks.values())
        
        return {
            "all_configured": all_good,
            "checks": config_checks,
            "working_count": sum(1 for check in config_checks.values() if check.get("status") == "good"),
            "total_count": len(config_checks)
        }
    
    def _check_env_variables(self) -> Dict[str, Any]:
        """Verificar variables de entorno críticas"""
        required_vars = [
            "GROQ_API_KEY_1", "GROQ_API_KEY_2", "GROQ_API_KEY_3", "GROQ_API_KEY_4",
            "HOST", "PORT"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        return {
            "status": "good" if not missing_vars else "needs_attention",
            "missing_variables": missing_vars,
            "total_required": len(required_vars),
            "found": len(required_vars) - len(missing_vars)
        }
    
    def _check_directories(self) -> Dict[str, Any]:
        """Verificar directorios necesarios"""
        required_dirs = [
            "uploads", "sessions", "Normativa", "logs", "temp"
        ]
        
        missing_dirs = []
        for dir_name in required_dirs:
            if not Path(dir_name).exists():
                missing_dirs.append(dir_name)
        
        return {
            "status": "good" if not missing_dirs else "needs_attention",
            "missing_directories": missing_dirs,
            "total_required": len(required_dirs),
            "found": len(required_dirs) - len(missing_dirs)
        }
    
    def _check_file_permissions(self) -> Dict[str, Any]:
        """Verificar permisos de archivos"""
        # Verificación básica de permisos
        critical_paths = ["uploads", "sessions", "logs", "temp"]
        permission_issues = []
        
        for path_name in critical_paths:
            path = Path(path_name)
            if path.exists():
                try:
                    # Intentar crear un archivo temporal para verificar permisos de escritura
                    test_file = path / "test_permissions.tmp"
                    test_file.touch()
                    test_file.unlink()
                except (PermissionError, OSError):
                    permission_issues.append(path_name)
        
        return {
            "status": "good" if not permission_issues else "needs_attention",
            "permission_issues": permission_issues,
            "checked_paths": critical_paths
        }
    
    def _check_logging_config(self) -> Dict[str, Any]:
        """Verificar configuración de logging"""
        try:
            # Verificar que el logger funcione
            test_logger = logging.getLogger("basico.test")
            test_logger.info("Test logging")
            
            return {
                "status": "good",
                "logging_available": True
            }
        except Exception as e:
            return {
                "status": "needs_attention",
                "logging_available": False,
                "error": str(e)
            }
    
    def _check_normative_files(self) -> Dict[str, Any]:
        """Verificar archivos normativos"""
        
        normativa_dir = Path("Normativa")
        anexo_file = normativa_dir / "anexo1.json"
        
        checks = {
            "normativa_directory": {
                "exists": normativa_dir.exists(),
                "is_directory": normativa_dir.is_dir() if normativa_dir.exists() else False
            },
            "anexo1_json": {
                "exists": anexo_file.exists(),
                "valid_json": False,
                "structure_valid": False
            }
        }
        
        # Verificar anexo1.json
        if anexo_file.exists():
            try:
                with open(anexo_file, 'r', encoding='utf-8') as f:
                    anexo_data = json.load(f)
                
                checks["anexo1_json"]["valid_json"] = True
                
                # Verificar estructura básica
                if "Proyecto_Basico_Obligatorio" in anexo_data:
                    proyecto = anexo_data["Proyecto_Basico_Obligatorio"]
                    if all(section in proyecto for section in ["Memoria", "Planos", "Presupuesto"]):
                        checks["anexo1_json"]["structure_valid"] = True
                
            except json.JSONDecodeError:
                checks["anexo1_json"]["valid_json"] = False
            except Exception:
                pass
        
        # Contar archivos normativos
        normative_files = 0
        if normativa_dir.exists():
            normative_files = len(list(normativa_dir.rglob("*.pdf")))
        
        checks["normative_files_count"] = normative_files
        
        # Determinar estado general
        if (checks["normativa_directory"]["exists"] and 
            checks["anexo1_json"]["exists"] and 
            checks["anexo1_json"]["valid_json"] and 
            checks["anexo1_json"]["structure_valid"]):
            status = "good"
        elif checks["anexo1_json"]["exists"]:
            status = "partial"
        else:
            status = "missing"
        
        return {
            "status": status,
            "checks": checks,
            "directory_exists": checks["normativa_directory"]["exists"],
            "anexo1_exists": checks["anexo1_json"]["exists"],
            "pdf_files_count": len(list(normativa_dir.glob("**/*.pdf"))) if normativa_dir.exists() else 0,
            "json_files_count": len(list(normativa_dir.glob("**/*.json"))) if normativa_dir.exists() else 0
        }
    
    def _check_ai_integration(self) -> Dict[str, Any]:
        """Verificar integración con IA"""
        
        checks = {
            "groq_api_key": any(os.getenv(f'GROQ_API_KEY_{i}') for i in range(1, 5)),
            "prompts_available": False,
            "client_available": False
        }
        
        # Verificar prompts
        try:
            from backend.app.basico import basico_prompts
            checks["prompts_available"] = hasattr(basico_prompts, 'BASICO_VERIFICACION_DOCUMENTOS')
        except ImportError:
            pass
        
        # Verificar cliente
        try:
            from backend.app.basico.ai_client import BasicoAIClient
            client = BasicoAIClient()
            checks["client_available"] = client.is_available()
        except Exception:
            pass
        
        # Determinar estado
        if all(checks.values()):
            status = "good"
        elif checks["groq_api_key"] and checks["prompts_available"]:
            status = "partial"
        else:
            status = "missing"
        
        return {
            "status": status,
            "checks": checks,
            "prompts_available": checks["prompts_available"],
            "config_available": checks["groq_api_key"]
        }
    
    def _check_ocr_processing(self) -> Dict[str, Any]:
        """Auditar procesamiento OCR"""
        try:
            from .ocr_processor import BasicoOCRProcessor
            
            ocr = BasicoOCRProcessor()
            
            # Verificar métodos principales
            has_extract_method = hasattr(ocr, 'extract_text_from_pdf')
            has_image_method = hasattr(ocr, 'extract_text_from_image')
            has_ocr_info = hasattr(ocr, 'get_ocr_info')
            
            return {
                'status': 'good' if has_extract_method and has_image_method else 'missing_methods',
                'ocr_available': True,
                'extract_method': 'extract_text_from_pdf' if has_extract_method else 'missing',
                'search_method': 'extract_text_from_image' if has_image_method else 'missing',
                'tesseract_config': hasattr(ocr, 'tesseract_config')
            }
        except Exception as e:
            return {
                'status': 'error',
                'ocr_available': False,
                'error': str(e)
            }
    
    def _evaluate_production_readiness(self, audit_results: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluar preparación para producción"""
        scores = {
            'components': audit_results['components']['success_rate'] * 100,
            'dependencies': audit_results['dependencies']['success_rate'] * 100,
            'configuration': audit_results['configuration']['success_rate'] * 100,
            'ai_integration': 100 if audit_results['ai_integration']['status'] == 'good' else 0,
            'ocr_processing': 100 if audit_results['ocr_processing']['status'] == 'good' else 0
        }
        
        overall_score = sum(scores.values()) / len(scores)
        
        readiness_level = 'production_ready' if overall_score >= 90 else \
                         'needs_minor_fixes' if overall_score >= 70 else \
                         'needs_major_fixes'
        
        return {
            'overall_score': overall_score,
            'individual_scores': scores,
            'readiness_level': readiness_level,
            'production_ready': overall_score >= 90
        }
    
    def _generate_recommendations(self, audit_results: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones basadas en auditoría"""
        recommendations = []
        
        # Recomendaciones por componentes
        components_score = audit_results.get('individual_scores', {}).get('components', 0)
        if components_score < 100:
            recommendations.append("🔧 Reparar componentes con errores")
        
        # Recomendaciones por dependencias
        dependencies_score = audit_results.get('individual_scores', {}).get('dependencies', 0)
        if dependencies_score < 100:
            recommendations.append("📦 Instalar dependencias faltantes")
        
        # Recomendaciones por configuración
        config_score = audit_results.get('individual_scores', {}).get('configuration', 0)
        if config_score < 100:
            recommendations.append("⚙️ Corregir configuración del sistema")
        
        # Recomendaciones por archivos normativos
        if not audit_results.get('normative_files', {}).get('anexo1_exists', False):
            recommendations.append("📋 Verificar archivo anexo1.json")
        
        # Recomendaciones por IA
        if audit_results.get('ai_integration', {}).get('status') != 'good':
            recommendations.append("🤖 Verificar integración con IA")
        
        # Recomendaciones por OCR
        if audit_results.get('ocr_processing', {}).get('status') != 'good':
            recommendations.append("🔍 Verificar procesamiento OCR")
        
        if not recommendations:
            recommendations.append("✅ Sistema listo para producción")
        
        return recommendations
    
    def _determine_system_status(self, overall_score: float) -> str:
        """Determinar estado final del sistema"""
        if overall_score >= 90:
            return 'production_ready'
        elif overall_score >= 70:
            return 'needs_minor_fixes'
        else:
            return 'needs_major_fixes'
    
    def _get_timestamp(self) -> str:
        """Obtener timestamp actual"""
        from datetime import datetime
        return datetime.now().isoformat()
