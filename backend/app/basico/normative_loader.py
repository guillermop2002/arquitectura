import json
from typing import Dict, Any, List
from pathlib import Path
from .ocr_processor import BasicoOCRProcessor

class BasicoNormativeLoader:
    """
    Carga y gestiona las normativas específicas según el contexto del proyecto.
    Implementa la lógica contextual para aplicar solo normativas relevantes.
    """
    
    def __init__(self):
        self.normativa_dir = Path("Normativa")
        self.ocr_processor = BasicoOCRProcessor()
        self.normative_cache = {}
        
    def get_applicable_normatives(self, project_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Determina qué normativas son aplicables según el contexto del proyecto.
        Esta es la lógica crítica para la Fase 3.
        """
        applicable_normatives = []
        
        uso_principal = project_context.get("uso_principal", "").lower()
        norma_zonal = project_context.get("norma_zonal", "").lower()
        grado = project_context.get("grado", "").lower()
        
        # 1. PGOUM General - SIEMPRE aplicable
        pgoum_general = {
            "name": "PGOUM General",
            "file_path": "Normativa/PGOUM/pgoum_general.pdf",
            "justification": "Aplicable a todos los proyectos",
            "priority": 1,
            "sections_to_apply": "all_relevant"  # No todo el documento
        }
        applicable_normatives.append(pgoum_general)
        
        # 2. PGOUM Específico de Uso - Solo si coincide con uso_principal
        uso_files = {
            "residencial": "pgoum_residencial.pdf",
            "industrial": "pgoum_industrial.pdf",
            "garaje-aparcamiento": "pgoum_garaje.pdf",
            "servicios_terciarios": "pgoum_terciario.pdf",
            "dotacional_zona_verde": "pgoum_dotacional.pdf",
            "dotacional_deportivo": "pgoum_dotacional deportivo.pdf",
            "dotacional_equipamiento": "pgoum_dotacional.pdf",
            "dotacional_servicios_publicos": "pgoum_dotacional.pdf",
            "dotacional_administracion_publica": "pgoum_dotacional.pdf",
            "dotacional_infraestructural": "pgoum_dotacional.pdf",
            "dotacional_via_publica": "pgoum_dotacional.pdf",
            "dotacional_transporte": "pgoum_dotacional.pdf"
        }
        
        if uso_principal in uso_files:
            uso_specific = {
                "name": f"PGOUM {uso_principal.title()}",
                "file_path": f"Normativa/PGOUM/Usos/{uso_files[uso_principal]}",
                "justification": f"Aplicable por uso principal: {uso_principal}",
                "priority": 2,
                "sections_to_apply": "use_specific"
            }
            applicable_normatives.append(uso_specific)
        
        # 3. PGOUM Zonal - Solo si coincide con norma_zonal
        zona_files = {
            "nz1": "NZ1.pdf",
            "nz2": "NZ2.pdf", 
            "nz3": "NZ3.pdf",
            "nz4": "NZ4.pdf",
            "nz5": "NZ5.pdf",
            "nz6": "NZ6.pdf",
            "nz7": "NZ7.pdf",
            "nz8": "NZ8.pdf",
            "nz9": "NZ9.pdf"
        }
        
        if norma_zonal in zona_files:
            zona_specific = {
                "name": f"Norma Zonal {norma_zonal.upper()}",
                "file_path": f"Normativa/PGOUM/Zonas/{zona_files[norma_zonal]}",
                "justification": f"Aplicable por norma zonal: {norma_zonal}",
                "priority": 3,
                "sections_to_apply": "zone_specific"
            }
            applicable_normatives.append(zona_specific)
        
        # 4. CTE - Según requisitos del proyecto
        cte_normatives = self._get_applicable_cte(project_context)
        applicable_normatives.extend(cte_normatives)
        
        # 5. Reglamentos específicos
        if uso_principal == "industrial":
            reglamento_industrial = {
                "name": "Reglamento de Instalaciones Industriales",
                "file_path": "Normativa/DOCUMENTOS BASICOS/DBSI/REGLAMENTO INSTALACIONES.pdf",
                "justification": "Aplicable por uso industrial",
                "priority": 4,
                "sections_to_apply": "industrial_specific"
            }
            applicable_normatives.append(reglamento_industrial)
        else:
            # Para usos no industriales, aplicar DBSI
            dbsi = {
                "name": "DB-SI (Seguridad en caso de Incendio)",
                "file_path": "Normativa/DOCUMENTOS BASICOS/DBSI/DBSI.pdf",
                "justification": "Aplicable por uso no industrial",
                "priority": 4,
                "sections_to_apply": "fire_safety"
            }
            applicable_normatives.append(dbsi)
        
        return applicable_normatives
    
    def _get_applicable_cte(self, project_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determinar qué Documentos Básicos del CTE son aplicables"""
        cte_normatives = []
        
        # Analizar requisitos específicos del proyecto
        requisitos_cte = project_context.get("requisitos_cte", {})
        superficie = project_context.get("superficie_construida", 0)
        plantas = project_context.get("plantas", 1)
        uso_principal = project_context.get("uso_principal", "").lower()
        
        # DB-SE (Seguridad Estructural) - Casi siempre aplicable
        if superficie > 50 or plantas > 1:
            cte_normatives.append({
                "name": "DB-SE (Seguridad Estructural)",
                "file_path": "Normativa/DOCUMENTOS BASICOS/DBSE/DBSE.pdf",
                "justification": f"Aplicable por superficie ({superficie}m²) y/o plantas ({plantas})",
                "priority": 5,
                "sections_to_apply": "structural"
            })
        
        # DB-SUA (Seguridad de Utilización y Accesibilidad)
        if superficie > 20:  # Prácticamente todos los edificios
            cte_normatives.append({
                "name": "DB-SUA (Seguridad de Utilización y Accesibilidad)",
                "file_path": "Normativa/DOCUMENTOS BASICOS/DBSUA/DBSUA.pdf",
                "justification": "Aplicable por requisitos de accesibilidad",
                "priority": 6,
                "sections_to_apply": "accessibility"
            })
        
        # DB-HE (Ahorro de Energía) - Según uso y superficie
        if superficie > 100 or uso_principal in ["residencial", "oficinas", "comercial"]:
            cte_normatives.append({
                "name": "DB-HE (Ahorro de Energía)",
                "file_path": "Normativa/DOCUMENTOS BASICOS/DBHE/DBHE.pdf",
                "justification": f"Aplicable por uso ({uso_principal}) y superficie ({superficie}m²)",
                "priority": 7,
                "sections_to_apply": "energy_efficiency"
            })
        
        # DB-HS (Salubridad) - Según uso
        if uso_principal in ["residencial", "comercial", "oficinas", "dotacional"]:
            cte_normatives.append({
                "name": "DB-HS (Salubridad)",
                "file_path": "Normativa/DOCUMENTOS BASICOS/DBHS/DBHS.pdf",
                "justification": f"Aplicable por uso: {uso_principal}",
                "priority": 8,
                "sections_to_apply": "health"
            })
        
        return cte_normatives
    
    def load_normative_content(self, normative_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Carga el contenido de una normativa específica.
        Solo carga las secciones relevantes, no todo el documento.
        """
        file_path = Path(normative_info["file_path"])
        
        if not file_path.exists():
            return {
                "error": f"Archivo no encontrado: {file_path}",
                "content": ""
            }
        
        # Verificar cache
        cache_key = f"{file_path}_{normative_info.get('sections_to_apply', 'all')}"
        if cache_key in self.normative_cache:
            return self.normative_cache[cache_key]
        
        try:
            # Extraer texto del PDF
            extracted_content = self.ocr_processor.extract_text_from_pdf(str(file_path))
            
            # Filtrar contenido según secciones aplicables
            filtered_content = self._filter_relevant_sections(
                extracted_content,
                normative_info.get("sections_to_apply", "all")
            )
            
            result = {
                "name": normative_info["name"],
                "file_path": str(file_path),
                "content": filtered_content,
                "sections_applied": normative_info.get("sections_to_apply", "all"),
                "justification": normative_info.get("justification", "")
            }
            
            # Guardar en cache
            self.normative_cache[cache_key] = result
            return result
            
        except Exception as e:
            return {
                "error": f"Error cargando {file_path}: {str(e)}",
                "content": ""
            }
    
    def _filter_relevant_sections(self, extracted_content: Dict[str, Any], sections_type: str) -> str:
        """
        Filtra el contenido para mostrar solo las secciones relevantes.
        Esto es crítico para evitar aplicar normativas irrelevantes.
        """
        full_text = extracted_content.get("full_text", "")
        
        if sections_type == "all":
            return full_text
        
        # Definir patrones de secciones relevantes según el tipo
        section_patterns = {
            "structural": [
                r"artículo\s+\d+\.\d*\s*estructur",
                r"sección\s+\d+\s*estructur",
                r"cimentación",
                r"forjados",
                r"muros\s+de\s+carga"
            ],
            "fire_safety": [
                r"artículo\s+\d+\.\d*\s*incendio",
                r"sección\s+\d+\s*seguridad.*incendio",
                r"evacuación",
                r"sectores\s+de\s+incendio",
                r"resistencia\s+al\s+fuego"
            ],
            "accessibility": [
                r"artículo\s+\d+\.\d*\s*accesib",
                r"sección\s+\d+\s*accesib",
                r"barreras\s+arquitectónicas",
                r"rampas",
                r"ascensores"
            ],
            "energy_efficiency": [
                r"artículo\s+\d+\.\d*\s*energ",
                r"sección\s+\d+\s*ahorro.*energ",
                r"aislamiento\s+térmico",
                r"eficiencia\s+energética"
            ],
            "use_specific": [
                r"artículo\s+\d+\.\d*\s*uso",
                r"sección\s+\d+\s*uso",
                r"condiciones\s+de\s+uso"
            ],
            "zone_specific": [
                r"artículo\s+\d+\.\d*",
                r"sección\s+\d+",
                r"parámetros\s+urbanísticos",
                r"condiciones\s+de\s+edificación"
            ]
        }
        
        if sections_type not in section_patterns:
            return full_text[:5000]  # Limitar texto si no hay patrón específico
        
        # Extraer secciones relevantes usando patrones
        import re
        relevant_sections = []
        
        for pattern in section_patterns[sections_type]:
            matches = re.finditer(pattern, full_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                start = max(0, match.start() - 200)
                end = min(len(full_text), match.end() + 1000)
                section_text = full_text[start:end]
                relevant_sections.append(section_text)
        
        if relevant_sections:
            return "\n\n---\n\n".join(relevant_sections[:10])  # Máximo 10 secciones
        else:
            # Si no encuentra secciones específicas, devolver una muestra del documento
            return full_text[:3000]
    
    def get_normative_summary(self, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """Obtener resumen de normativas aplicables"""
        applicable_normatives = self.get_applicable_normatives(project_context)
        
        return {
            "total_normatives": len(applicable_normatives),
            "normatives": [
                {
                    "name": norm["name"],
                    "justification": norm["justification"],
                    "priority": norm["priority"],
                    "file_exists": Path(norm["file_path"]).exists()
                }
                for norm in applicable_normatives
            ],
            "context_used": {
                "uso_principal": project_context.get("uso_principal"),
                "norma_zonal": project_context.get("norma_zonal"),
                "grado": project_context.get("grado"),
                "superficie_construida": project_context.get("superficie_construida")
            }
        }
