import json
import logging
from typing import Dict, Any, List
from pathlib import Path
from .ocr_processor import BasicoOCRProcessor

# Configurar logger específico con logs detallados
logger = logging.getLogger("basico.normative_loader")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

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
        LÓGICA ESPECÍFICA: Solo PGOUM + normativas de incendios según especificación exacta.
        """
        logger.info(f"🔍 INICIANDO get_applicable_normatives con contexto: {project_context}")
        applicable_normatives = []
        
        uso_principal = project_context.get("uso_principal", "").lower()
        norma_zonal = project_context.get("norma_zonal", "").lower()
        
        logger.debug(f"📋 Parámetros extraídos - Uso: '{uso_principal}', Zona: '{norma_zonal}'")
        
        # 1. PGOUM General - SIEMPRE aplicable (para todos los planos MENOS Planos_Incendios)
        pgoum_general = {
            "name": "PGOUM General",
            "file_path": "Normativa/PGOUM/pgoum_general.pdf",
            "justification": "Aplicable a todos los planos excepto Planos_Incendios",
            "priority": 1,
            "applies_to": "all_except_fire",
            "sections_to_apply": "general_pgoum"
        }
        applicable_normatives.append(pgoum_general)
        
        # 2. PGOUM Específico de Uso - Solo si existe el archivo correspondiente
        uso_files = {
            "residencial": "pgoum_residencial.pdf",
            "industrial": "pgoum_industrial.pdf",
            "garaje-aparcamiento": "pgoum_garaje-aparcamiento.pdf",
            "servicios_terciarios": "pgoum_servicios terciarios.pdf",
            "dotacional_zona_verde": "pgoum_dotacional zona verde.pdf",
            "dotacional_deportivo": "pgoum_dotacional deportivo.pdf",
            "dotacional_equipamiento": "pgoum_dotacional equipamiento.pdf",
            "dotacional_servicios_publicos": "pgoum_dotacional servicios publicos.pdf",
            "dotacional_administracion_publica": "pgoum_dotacional administracion publica.pdf",
            "dotacional_infraestructural": "pgoum_dotacional infraestructural.pdf",
            "dotacional_via_publica": "pgoum_dotacional via publica.pdf",
            "dotacional_transporte": "pgoum_dotacional transporte.pdf"
        }
        
        logger.debug(f"📋 Mapeo de archivos de uso configurado: {uso_files}")
        
        if uso_principal in uso_files:
            archivo_uso = uso_files[uso_principal]
            ruta_completa_uso = f"Normativa/PGOUM/Usos/{archivo_uso}"
            logger.info(f"✅ USO ENCONTRADO: '{uso_principal}' -> archivo: '{archivo_uso}'")
            logger.debug(f"📁 Ruta completa uso: '{ruta_completa_uso}'")
            
            uso_specific = {
                "name": f"PGOUM {uso_principal.replace('_', ' ').title()}",
                "file_path": ruta_completa_uso,
                "justification": f"Aplicable por uso principal: {uso_principal}",
                "priority": 2,
                "applies_to": "all_except_fire",
                "sections_to_apply": "use_specific"
            }
            applicable_normatives.append(uso_specific)
        else:
            logger.warning(f"⚠️  USO NO ENCONTRADO: '{uso_principal}' no está en uso_files")
            logger.debug(f"📋 Usos disponibles: {list(uso_files.keys())}")
        
        # 3. PGOUM Zonal - Solo si existe la zona
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
            archivo_zona = zona_files[norma_zonal]
            ruta_completa_zona = f"Normativa/PGOUM/Zonas/{archivo_zona}"
            logger.info(f"✅ ZONA ENCONTRADA: '{norma_zonal}' -> archivo: '{archivo_zona}'")
            logger.debug(f"📁 Ruta completa zona: '{ruta_completa_zona}'")
            
            zona_specific = {
                "name": f"Norma Zonal {norma_zonal.upper()}",
                "file_path": ruta_completa_zona,
                "justification": f"Aplicable por norma zonal: {norma_zonal}",
                "priority": 3,
                "applies_to": "all_except_fire",
                "sections_to_apply": "zone_specific"
            }
            applicable_normatives.append(zona_specific)
        else:
            logger.warning(f"⚠️  ZONA NO ENCONTRADA: '{norma_zonal}' no está en zona_files")
            logger.debug(f"📋 Zonas disponibles: {list(zona_files.keys())}")
        
        # 4. NORMATIVAS DE INCENDIOS - ÚNICAMENTE para Planos_Incendios
        if uso_principal == "industrial":
            # Para uso industrial: REGLAMENTO INSTALACIONES
            fire_regulation = {
                "name": "Reglamento de Instalaciones Industriales",
                "file_path": "Normativa/DOCUMENTOS BASICOS/DBSI/REGLAMENTO INSTALACIONES.pdf",
                "justification": "ÚNICAMENTE para Planos_Incendios - uso industrial",
                "priority": 4,
                "applies_to": "fire_plans_only",
                "sections_to_apply": "industrial_fire"
            }
            applicable_normatives.append(fire_regulation)
        else:
            # Para cualquier otro uso: DBSI
            dbsi = {
                "name": "DB-SI (Seguridad en caso de Incendio)",
                "file_path": "Normativa/DOCUMENTOS BASICOS/DBSI/DBSI.pdf",
                "justification": "ÚNICAMENTE para Planos_Incendios - uso no industrial",
                "priority": 4,
                "applies_to": "fire_plans_only",
                "sections_to_apply": "fire_safety"
            }
            applicable_normatives.append(dbsi)
        
        return applicable_normatives
    
    
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
        """Obtener resumen de normativas aplicables con logs detallados"""
        logger.info(f"🎯 GENERANDO RESUMEN DE NORMATIVAS para contexto: {project_context}")
        applicable_normatives = self.get_applicable_normatives(project_context)
        
        logger.info(f"📊 Total de normativas encontradas: {len(applicable_normatives)}")
        
        normatives_with_existence = []
        for norm in applicable_normatives:
            file_path = Path(norm["file_path"])
            file_exists = file_path.exists()
            
            logger.info(f"🔍 VERIFICANDO ARCHIVO: '{norm['name']}'")
            logger.debug(f"   📁 Ruta: {file_path}")
            logger.debug(f"   📁 Ruta absoluta: {file_path.absolute()}")
            logger.info(f"   {'✅' if file_exists else '❌'} Existe: {file_exists}")
            
            if not file_exists:
                logger.warning(f"⚠️  ARCHIVO NO ENCONTRADO: {file_path}")
                # Verificar directorio padre
                parent_dir = file_path.parent
                logger.debug(f"   📂 Directorio padre: {parent_dir}")
                logger.debug(f"   📂 Directorio padre existe: {parent_dir.exists()}")
                if parent_dir.exists():
                    archivos_en_directorio = list(parent_dir.glob("*.pdf"))
                    logger.debug(f"   📋 Archivos PDF en directorio: {[f.name for f in archivos_en_directorio]}")
            
            normatives_with_existence.append({
                "name": norm["name"],
                "justification": norm["justification"],
                "priority": norm["priority"],
                "file_exists": file_exists
            })
        
        result = {
            "total_normatives": len(applicable_normatives),
            "normatives": normatives_with_existence,
            "context_used": {
                "uso_principal": project_context.get("uso_principal"),
                "norma_zonal": project_context.get("norma_zonal"),
                "grado": project_context.get("grado"),
                "superficie_construida": project_context.get("superficie_construida")
            }
        }
        
        logger.info(f"📋 RESUMEN COMPLETADO - {len([n for n in normatives_with_existence if n['file_exists']])} archivos existen, {len([n for n in normatives_with_existence if not n['file_exists']])} no existen")
        
        return result
