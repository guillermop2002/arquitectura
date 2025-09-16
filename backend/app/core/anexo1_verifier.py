"""
Verificador del Anexo I del CTE para proyectos básicos.
Verifica que los documentos subidos contengan todas las secciones obligatorias.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import fitz  # PyMuPDF
import re

logger = logging.getLogger(__name__)

class Anexo1Verifier:
    """
    Verificador de cumplimiento del Anexo I del CTE.
    Verifica la presencia de secciones obligatorias en documentos PDF.
    """
    
    def __init__(self):
        """Initialize the Anexo I verifier."""
        self.anexo1_data = self._load_anexo1_data()
        self.text_cache = {}  # Cache para texto extraído
        
        # Palabras clave para cada sección
        self.keywords = {
            # Memoria Descriptiva
            "Agentes": ["agentes", "intervinientes", "proyectista", "director", "constructor"],
            "Informacion_Previa": ["información previa", "antecedentes", "situación actual", "estado previo"],
            "Descripcion_Proyecto": ["descripción del proyecto", "descripción general", "objeto del proyecto"],
            "Prestaciones_Edificio": ["prestaciones", "características", "funcionalidad", "uso del edificio"],
            
            # Cumplimiento CTE
            "Seguridad_Incendio": ["seguridad en caso de incendio", "protección contra incendios", "evacuación", "resistencia al fuego"],
            
            # Planos
            "Plano_Situacion": ["plano de situación", "situación", "emplazamiento general"],
            "Plano_Emplazamiento": ["plano de emplazamiento", "emplazamiento", "lote"],
            "Plano_Urbanizacion": ["plano de urbanización", "urbanización", "accesos", "servicios"],
            "Plantas_Generales": ["plantas generales", "planta baja", "planta primera", "distribución"],
            "Planos_Cubiertas": ["plano de cubiertas", "cubierta", "azotea", "tejado"],
            "Alzados_Secciones": ["alzados", "secciones", "fachadas", "cortes"],
            
            # Presupuesto
            "Presupuesto_Aproximado": ["presupuesto", "coste", "precio", "valoración", "económico"]
        }
        
        logger.info("Anexo I verifier initialized")
    
    def _load_anexo1_data(self) -> Dict[str, Any]:
        """Load Anexo I requirements from JSON file."""
        try:
            anexo1_path = Path(__file__).parent / "anexo1.json"
            with open(anexo1_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info("Anexo I data loaded successfully")
            return data
        except Exception as e:
            logger.error(f"Error loading Anexo I data: {e}")
            return {}
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file using PyMuPDF."""
        try:
            # Check cache first
            if file_path in self.text_cache:
                return self.text_cache[file_path]
            
            doc = fitz.open(file_path)
            text = ""
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text()
            
            doc.close()
            
            # Cache the text
            self.text_cache[file_path] = text
            logger.info(f"Text extracted from {file_path} ({len(text)} characters)")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def search_section_in_text(self, text: str, section_name: str) -> bool:
        """Search for section keywords in text."""
        if section_name not in self.keywords:
            return False
        
        text_lower = text.lower()
        keywords = self.keywords[section_name]
        
        # Search for any of the keywords
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        
        return False
    
    def verify_file(self, file_path: str) -> Dict[str, Any]:
        """Verify a single file against Anexo I requirements."""
        try:
            # Extract text
            text = self.extract_text_from_pdf(file_path)
            if not text:
                return {
                    "file": file_path,
                    "status": "error",
                    "message": "Could not extract text from PDF"
                }
            
            # Check each required section
            results = {
                "file": file_path,
                "status": "verified",
                "sections_found": [],
                "sections_missing": []
            }
            
            # Check Memoria Descriptiva sections
            for section, required in self.anexo1_data["Proyecto_Basico_Obligatorio"]["Memoria"]["Memoria_Descriptiva"].items():
                if required:
                    if self.search_section_in_text(text, section):
                        results["sections_found"].append(f"Memoria_Descriptiva.{section}")
                    else:
                        results["sections_missing"].append(f"Memoria_Descriptiva.{section}")
            
            # Check Cumplimiento CTE sections
            for section, required in self.anexo1_data["Proyecto_Basico_Obligatorio"]["Memoria"]["Cumplimiento_CTE"].items():
                if required:
                    if self.search_section_in_text(text, section):
                        results["sections_found"].append(f"Cumplimiento_CTE.{section}")
                    else:
                        results["sections_missing"].append(f"Cumplimiento_CTE.{section}")
            
            # Check Planos sections
            for section, required in self.anexo1_data["Proyecto_Basico_Obligatorio"]["Planos"].items():
                if required:
                    if self.search_section_in_text(text, section):
                        results["sections_found"].append(f"Planos.{section}")
                    else:
                        results["sections_missing"].append(f"Planos.{section}")
            
            # Check Presupuesto sections
            for section, required in self.anexo1_data["Proyecto_Basico_Obligatorio"]["Presupuesto"].items():
                if required:
                    if self.search_section_in_text(text, section):
                        results["sections_found"].append(f"Presupuesto.{section}")
                    else:
                        results["sections_missing"].append(f"Presupuesto.{section}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error verifying file {file_path}: {e}")
            return {
                "file": file_path,
                "status": "error",
                "message": str(e)
            }
    
    def verify_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Verify multiple files against Anexo I requirements."""
        try:
            all_results = []
            all_sections_found = set()
            all_sections_missing = set()
            
            # Verify each file
            for file_path in file_paths:
                if not os.path.exists(file_path):
                    logger.warning(f"File not found: {file_path}")
                    continue
                
                file_result = self.verify_file(file_path)
                all_results.append(file_result)
                
                if file_result["status"] == "verified":
                    all_sections_found.update(file_result["sections_found"])
                    all_sections_missing.update(file_result["sections_missing"])
            
            # Calculate overall status
            total_required = len([s for s in self._get_all_required_sections()])
            found_count = len(all_sections_found)
            missing_count = len(all_sections_missing)
            completion_percentage = (found_count / total_required) * 100 if total_required > 0 else 0
            
            overall_status = "complete" if missing_count == 0 else "incomplete"
            
            return {
                "overall_status": overall_status,
                "completion_percentage": round(completion_percentage, 2),
                "total_required": total_required,
                "sections_found": list(all_sections_found),
                "sections_missing": list(all_sections_missing),
                "files_verified": len([r for r in all_results if r["status"] == "verified"]),
                "files_with_errors": len([r for r in all_results if r["status"] == "error"]),
                "file_results": all_results,
                "summary": self._generate_summary(overall_status, found_count, missing_count, completion_percentage)
            }
            
        except Exception as e:
            logger.error(f"Error verifying files: {e}")
            return {
                "overall_status": "error",
                "completion_percentage": 0,
                "error": str(e)
            }
    
    def _get_all_required_sections(self) -> List[str]:
        """Get all required sections from Anexo I data."""
        sections = []
        
        # Memoria Descriptiva
        for section, required in self.anexo1_data["Proyecto_Basico_Obligatorio"]["Memoria"]["Memoria_Descriptiva"].items():
            if required:
                sections.append(f"Memoria_Descriptiva.{section}")
        
        # Cumplimiento CTE
        for section, required in self.anexo1_data["Proyecto_Basico_Obligatorio"]["Memoria"]["Cumplimiento_CTE"].items():
            if required:
                sections.append(f"Cumplimiento_CTE.{section}")
        
        # Planos
        for section, required in self.anexo1_data["Proyecto_Basico_Obligatorio"]["Planos"].items():
            if required:
                sections.append(f"Planos.{section}")
        
        # Presupuesto
        for section, required in self.anexo1_data["Proyecto_Basico_Obligatorio"]["Presupuesto"].items():
            if required:
                sections.append(f"Presupuesto.{section}")
        
        return sections
    
    def _generate_summary(self, status: str, found: int, missing: int, percentage: float) -> str:
        """Generate a summary of the verification results."""
        if status == "complete":
            return f"✅ Verificación completa: Se encontraron todas las {found} secciones obligatorias del Anexo I."
        elif status == "incomplete":
            return f"⚠️ Verificación incompleta: Se encontraron {found} de {found + missing} secciones obligatorias ({percentage:.1f}% completado). Faltan {missing} secciones."
        else:
            return f"❌ Error en la verificación: No se pudo procesar correctamente los documentos."
    
    def get_missing_sections(self, verification_results: Dict[str, Any]) -> List[str]:
        """Get list of missing sections from verification results."""
        return verification_results.get("sections_missing", [])
    
    def get_present_sections(self, verification_results: Dict[str, Any]) -> List[str]:
        """Get list of present sections from verification results."""
        return verification_results.get("sections_found", [])
    
    def clear_cache(self):
        """Clear the text cache."""
        self.text_cache.clear()
        logger.info("Text cache cleared")
