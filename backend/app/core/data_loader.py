"""
Cargador de datos para la aplicación.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import os

logger = logging.getLogger(__name__)

class DataLoader:
    """Cargador de datos del sistema."""
    
    def __init__(self, data_path: str = "data"):
        """
        Inicializar el cargador de datos.
        
        Args:
            data_path: Ruta base de los datos
        """
        self.data_path = Path(data_path)
        self.data_path.mkdir(exist_ok=True)
        self.logger = logging.getLogger(f"{__name__}.DataLoader")
    
    def load_json(self, filename: str, subdirectory: str = "") -> Optional[Dict[str, Any]]:
        """
        Cargar datos desde un archivo JSON.
        
        Args:
            filename: Nombre del archivo
            subdirectory: Subdirectorio (opcional)
            
        Returns:
            Datos cargados o None si hay error
        """
        try:
            file_path = self.data_path
            if subdirectory:
                file_path = file_path / subdirectory
                file_path.mkdir(exist_ok=True)
            
            file_path = file_path / filename
            
            if not file_path.exists():
                self.logger.warning(f"Archivo no encontrado: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(f"Datos cargados desde: {file_path}")
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decodificando JSON {filename}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error cargando archivo {filename}: {e}")
            return None
    
    def save_json(self, data: Dict[str, Any], filename: str, subdirectory: str = "") -> bool:
        """
        Guardar datos en un archivo JSON.
        
        Args:
            data: Datos a guardar
            filename: Nombre del archivo
            subdirectory: Subdirectorio (opcional)
            
        Returns:
            True si se guardó correctamente
        """
        try:
            file_path = self.data_path
            if subdirectory:
                file_path = file_path / subdirectory
                file_path.mkdir(exist_ok=True)
            
            file_path = file_path / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Datos guardados en: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error guardando archivo {filename}: {e}")
            return False
    
    def load_anexo1_data(self) -> Optional[Dict[str, Any]]:
        """
        Cargar datos del Anexo 1.
        
        Returns:
            Datos del Anexo 1 o None si hay error
        """
        try:
            # Buscar archivo anexo1.json en diferentes ubicaciones
            possible_paths = [
                self.data_path / "anexo1.json",
                Path("backend/app/core/anexo1.json"),
                Path("anexo1.json")
            ]
            
            for path in possible_paths:
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.logger.info(f"Anexo 1 cargado desde: {path}")
                    return data
            
            self.logger.warning("Archivo anexo1.json no encontrado")
            return None
            
        except Exception as e:
            self.logger.error(f"Error cargando Anexo 1: {e}")
            return None
    
    def load_normative_documents(self) -> Dict[str, Any]:
        """
        Cargar información de documentos normativos.
        
        Returns:
            Información de documentos normativos
        """
        try:
            normative_data = {
                "db_he": {
                    "name": "DB-HE Ahorro de Energía",
                    "description": "Documento Básico de Ahorro de Energía",
                    "sections": ["HE1", "HE2", "HE3", "HE4", "HE5"]
                },
                "db_hr": {
                    "name": "DB-HR Salubridad",
                    "description": "Documento Básico de Salubridad",
                    "sections": ["HR1", "HR2", "HR3", "HR4", "HR5"]
                },
                "db_si": {
                    "name": "DB-SI Seguridad en caso de Incendio",
                    "description": "Documento Básico de Seguridad en caso de Incendio",
                    "sections": ["SI1", "SI2", "SI3", "SI4", "SI5", "SI6"]
                },
                "db_su": {
                    "name": "DB-SU Seguridad de Utilización",
                    "description": "Documento Básico de Seguridad de Utilización",
                    "sections": ["SU1", "SU2", "SU3", "SU4", "SU5"]
                }
            }
            
            self.logger.info("Datos normativos cargados")
            return normative_data
            
        except Exception as e:
            self.logger.error(f"Error cargando documentos normativos: {e}")
            return {}
    
    def load_project_templates(self) -> Dict[str, Any]:
        """
        Cargar plantillas de proyecto.
        
        Returns:
            Plantillas de proyecto
        """
        try:
            templates = {
                "residential_new": {
                    "name": "Edificio Residencial Nuevo",
                    "description": "Plantilla para edificios residenciales de nueva construcción",
                    "applicable_norms": ["DB-HE", "DB-HR", "DB-SI", "DB-SU"],
                    "required_documents": [
                        "Memoria descriptiva",
                        "Planos de planta",
                        "Planos de alzado",
                        "Planos de sección",
                        "Memoria de cálculo"
                    ]
                },
                "residential_existing": {
                    "name": "Edificio Residencial Existente",
                    "description": "Plantilla para rehabilitación de edificios residenciales",
                    "applicable_norms": ["DB-HE", "DB-HR", "DB-SI", "DB-SU"],
                    "required_documents": [
                        "Memoria descriptiva de la intervención",
                        "Planos de estado actual",
                        "Planos de proyecto",
                        "Memoria de cálculo de la intervención"
                    ]
                },
                "commercial_new": {
                    "name": "Edificio Comercial Nuevo",
                    "description": "Plantilla para edificios comerciales de nueva construcción",
                    "applicable_norms": ["DB-HE", "DB-HR", "DB-SI", "DB-SU"],
                    "required_documents": [
                        "Memoria descriptiva",
                        "Planos de planta",
                        "Planos de alzado",
                        "Planos de sección",
                        "Memoria de cálculo",
                        "Memoria de accesibilidad"
                    ]
                }
            }
            
            self.logger.info("Plantillas de proyecto cargadas")
            return templates
            
        except Exception as e:
            self.logger.error(f"Error cargando plantillas de proyecto: {e}")
            return {}
    
    def load_verification_rules(self) -> Dict[str, Any]:
        """
        Cargar reglas de verificación.
        
        Returns:
            Reglas de verificación
        """
        try:
            rules = {
                "area_verification": {
                    "min_area": 10,  # m²
                    "max_area": 10000,  # m²
                    "description": "Verificación de área del proyecto"
                },
                "document_verification": {
                    "required_documents": [
                        "memoria_descriptiva",
                        "planos_planta",
                        "planos_alzado",
                        "planos_seccion"
                    ],
                    "description": "Verificación de documentos requeridos"
                },
                "normative_verification": {
                    "applicable_norms": [
                        "DB-HE", "DB-HR", "DB-SI", "DB-SU"
                    ],
                    "description": "Verificación de normativas aplicables"
                }
            }
            
            self.logger.info("Reglas de verificación cargadas")
            return rules
            
        except Exception as e:
            self.logger.error(f"Error cargando reglas de verificación: {e}")
            return {}
    
    def get_data_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen de los datos disponibles.
        
        Returns:
            Resumen de datos
        """
        try:
            summary = {
                "data_path": str(self.data_path),
                "available_files": [],
                "total_size": 0
            }
            
            # Listar archivos disponibles
            for file_path in self.data_path.rglob("*"):
                if file_path.is_file():
                    summary["available_files"].append({
                        "name": file_path.name,
                        "path": str(file_path.relative_to(self.data_path)),
                        "size": file_path.stat().st_size
                    })
                    summary["total_size"] += file_path.stat().st_size
            
            summary["total_files"] = len(summary["available_files"])
            summary["total_size_mb"] = round(summary["total_size"] / (1024 * 1024), 2)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generando resumen de datos: {e}")
            return {"error": str(e)}
