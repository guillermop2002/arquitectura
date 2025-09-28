import json
import re
from typing import Dict, Any, List, Set
from pathlib import Path
from .ocr_processor import BasicoOCRProcessor

class BasicoAnexoVerifier:
    def __init__(self):
        self.anexo_template = self._load_anexo_template()
        self.ocr_processor = BasicoOCRProcessor()
        self.verification_cache = {}
    
    def _load_anexo_template(self) -> Dict[str, Any]:
        """Cargar plantilla del anexo1.json"""
        anexo_path = Path("Normativa/anexo1.json")
        
        if not anexo_path.exists():
            # Crear anexo por defecto si no existe
            self._create_default_anexo()
        
        try:
            with open(anexo_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando anexo1.json: {e}")
            return self._get_default_anexo_structure()
    
    def verify_session_documents(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verificar documentos de una sesión contra el anexo"""
        
        session_id = session_data.get("session_id", "unknown")
        
        # Extraer todos los textos de los archivos
        all_texts = self._extract_session_texts(session_data)
        
        # Verificar cada elemento del anexo
        verification_results = self._verify_anexo_elements(all_texts)
        
        # Calcular estadísticas
        stats = self._calculate_verification_stats(verification_results)
        
        # Generar reporte
        report = {
            'session_id': session_id,
            'verification_results': verification_results,
            'statistics': stats,
            'files_processed': len(all_texts),
            'total_pages': sum(text['total_pages'] for text in all_texts.values()),
            'recommendations': self._generate_recommendations(verification_results, stats)
        }
        
        return report
    
    def _extract_session_texts(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer texto de todos los archivos de la sesión"""
        all_texts = {}
        
        for file_info in session_data.get("files", []):
            file_path = file_info["path"]
            filename = file_info["filename"]
            
            if file_path.lower().endswith('.pdf'):
                try:
                    text_data = self.ocr_processor.extract_text_from_pdf(file_path)
                    all_texts[filename] = text_data
                except Exception as e:
                    print(f"Error extrayendo texto de {filename}: {e}")
                    all_texts[filename] = {
                        "full_text": "",
                        "total_pages": 0,
                        "extraction_method": "error",
                        "confidence": 0.0
                    }
        
        return all_texts
    
    def _verify_anexo_elements(self, all_texts: Dict[str, Any]) -> Dict[str, Any]:
        """Verificar elementos del anexo en los textos"""
        
        # Combinar todo el texto
        combined_text = self._combine_all_texts(all_texts)
        
        verification_results = {}
        anexo_proyecto = self.anexo_template.get("Proyecto_Basico_Obligatorio", {})
        
        for section_name, section_data in anexo_proyecto.items():
            # Skip non-dictionary sections like "Documentos_Analizados", "Resumen_Resultados"
            if not isinstance(section_data, dict):
                continue
                
            section_results = {
                "completion_percentage": 0.0,
                "found_count": 0,
                "total_count": 0,
                "elements": {}
            }
            
            found_elements = 0
            total_elements = 0
            
            # Recursively process all elements in the section
            elements_to_process = self._extract_verifiable_elements(section_data)
            section_results["total_count"] = len(elements_to_process)
            
            for element_name, element_data in elements_to_process.items():
                element_result = self._verify_single_element(
                    element_name, 
                    element_data, 
                    combined_text,
                    all_texts
                )
                
                section_results["elements"][element_name] = element_result
                
                if element_result["presente"]:
                    found_elements += 1
            
            section_results["found_count"] = found_elements
            if section_results["total_count"] > 0:
                section_results["completion_percentage"] = (found_elements / section_results["total_count"]) * 100
            
            verification_results[section_name] = section_results
        
        return verification_results
    
    def _extract_verifiable_elements(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Recursively extract verifiable elements from the JSON structure"""
        elements = {}
        
        for key, value in data.items():
            if key == "origen":  # Skip origen arrays
                continue
                
            full_key = f"{prefix}_{key}" if prefix else key
            
            if isinstance(value, dict):
                # Check if this is a verifiable element (has presente, pages, snippet fields)
                if "presente" in value and "pages" in value and "snippet" in value:
                    # This is a verifiable element
                    elements[full_key] = {
                        "keywords": self._generate_keywords_for_element(full_key),
                        "element_type": "verifiable"
                    }
                else:
                    # Recursively process nested elements
                    nested_elements = self._extract_verifiable_elements(value, full_key)
                    elements.update(nested_elements)
        
        return elements
    
    def _generate_keywords_for_element(self, element_name: str) -> List[str]:
        """Generate keywords for an element based on its name"""
        # Convert element name to keywords
        keywords = []
        
        # Add the element name itself
        keywords.append(element_name.lower().replace("_", " "))
        
        # Add common variations
        if "promotor" in element_name.lower():
            keywords.extend(["promotor", "promotora", "cliente", "propietario"])
        elif "constructor" in element_name.lower():
            keywords.extend(["constructor", "constructora", "empresa constructora"])
        elif "proyectista" in element_name.lower():
            keywords.extend(["proyectista", "arquitecto", "arquitecta", "diseñador"])
        elif "director_obra" in element_name.lower():
            keywords.extend(["director obra", "director de obra", "jefe obra"])
        elif "director_ejecucion" in element_name.lower():
            keywords.extend(["director ejecución", "director de ejecución"])
        elif "antecedentes" in element_name.lower():
            keywords.extend(["antecedentes", "condicionantes", "situación previa"])
        elif "emplazamiento" in element_name.lower():
            keywords.extend(["emplazamiento", "situación", "localización", "ubicación"])
        elif "normativa" in element_name.lower():
            keywords.extend(["normativa", "reglamento", "ordenanza", "código"])
        elif "programa" in element_name.lower():
            keywords.extend(["programa", "necesidades", "usos", "funciones"])
        elif "geometria" in element_name.lower():
            keywords.extend(["geometría", "volumen", "dimensiones", "forma"])
        elif "superficie" in element_name.lower():
            keywords.extend(["superficie", "área", "metros cuadrados", "m²"])
        elif "estructura" in element_name.lower():
            keywords.extend(["estructura", "cimentación", "forjados", "pilares"])
        elif "incendio" in element_name.lower():
            keywords.extend(["incendio", "seguridad", "evacuación", "sectores"])
        elif "presupuesto" in element_name.lower():
            keywords.extend(["presupuesto", "coste", "precio", "valoración"])
        elif "situacion" in element_name.lower():
            keywords.extend(["situación", "emplazamiento", "localización"])
        elif "plantas" in element_name.lower():
            keywords.extend(["plantas", "distribución", "layout", "espacios"])
        elif "alzados" in element_name.lower():
            keywords.extend(["alzados", "fachadas", "elevaciones"])
        elif "secciones" in element_name.lower():
            keywords.extend(["secciones", "cortes", "perfiles"])
        elif "cubiertas" in element_name.lower():
            keywords.extend(["cubiertas", "tejados", "azoteas"])
        
        return keywords
    
    def _verify_single_element(self, element_name: str, element_data: Dict[str, Any], 
                             combined_text: str, all_texts: Dict[str, Any]) -> Dict[str, Any]:
        """Verificar un elemento específico del anexo"""
        
        keywords = element_data.get("keywords", [])
        
        # Buscar keywords en el texto
        matches_found = []
        confidence_scores = []
        
        for keyword in keywords:
            matches = self._search_keyword_in_text(keyword, combined_text)
            if matches:
                matches_found.extend(matches)
                confidence_scores.append(len(matches))
        
        # Calcular confianza
        confidence = self._calculate_element_confidence(
            matches_found, keywords, len(combined_text)
        )
        
        # Determinar si está presente (umbral del 30%)
        presente = confidence >= 0.3
        
        return {
            "presente": presente,
            "confidence": confidence,
            "matches_found": len(matches_found),
            "keywords_total": len(keywords),
            "keywords_matched": len(set(match["keyword"] for match in matches_found)),
            "pages": list(set(match.get("page", 0) for match in matches_found)),
            "context_samples": matches_found[:3]  # Primeras 3 coincidencias como muestra
        }
    
    def _search_keyword_in_text(self, keyword: str, text: str) -> List[Dict[str, Any]]:
        """Buscar una keyword en el texto"""
        matches = []
        
        # Búsqueda case-insensitive
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        
        for match in pattern.finditer(text):
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()
            
            matches.append({
                "keyword": keyword,
                "position": match.start(),
                "context": context,
                "page": self._estimate_page_from_position(match.start(), text)
            })
        
        return matches
    
    def _calculate_element_confidence(self, matches: List[Dict[str, Any]], 
                                    keywords: List[str], text_length: int) -> float:
        """Calcular confianza de que un elemento esté presente"""
        
        if not matches or not keywords:
            return 0.0
        
        # Factor 1: Número de coincidencias (máximo 1.0 si hay 2+ coincidencias)
        match_factor = min(1.0, len(matches) / 2.0)
        
        # Factor 2: Cobertura de keywords (porcentaje de keywords únicas encontradas)
        unique_keywords_found = len(set(match["keyword"] for match in matches))
        keyword_coverage = unique_keywords_found / len(keywords)
        
        # Factor 3: Distribución en el texto (bonus si aparece en múltiples páginas)
        unique_pages = len(set(match.get("page", 0) for match in matches))
        distribution_bonus = min(0.2, unique_pages * 0.05)
        
        # Combinar factores
        confidence = (match_factor * 0.7 + keyword_coverage * 0.3) + distribution_bonus
        
        return min(1.0, confidence)
    
    def _estimate_page_from_position(self, position: int, text: str) -> int:
        """Estimar número de página basado en la posición en el texto"""
        # Estimación simple: ~2000 caracteres por página
        return (position // 2000) + 1
    
    def _combine_all_texts(self, all_texts: Dict[str, Any]) -> str:
        """Combinar todos los textos en uno solo"""
        combined = []
        
        for filename, text_data in all_texts.items():
            combined.append(f"\n=== {filename} ===\n")
            combined.append(text_data.get("full_text", ""))
        
        return "\n".join(combined)
    
    def _calculate_verification_stats(self, verification_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calcular estadísticas generales de verificación"""
        
        total_elements = 0
        found_elements = 0
        
        for section_name, section_data in verification_results.items():
            total_elements += section_data["total_count"]
            found_elements += section_data["found_count"]
        
        completion_percentage = (found_elements / total_elements * 100) if total_elements > 0 else 0
        
        return {
            "completion_percentage": completion_percentage,
            "total_elements": total_elements,
            "found_elements": found_elements,
            "missing_elements": total_elements - found_elements,
            "sections_analyzed": len(verification_results)
        }
    
    def _generate_recommendations(self, verification_results: Dict[str, Any], 
                                stats: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones basadas en los resultados"""
        
        recommendations = []
        
        # Recomendación general
        completion = stats["completion_percentage"]
        if completion < 50:
            recommendations.append("🚨 Documentación muy incompleta. Revisar elementos faltantes críticos.")
        elif completion < 75:
            recommendations.append("⚠️ Documentación parcialmente completa. Completar elementos faltantes.")
        elif completion < 90:
            recommendations.append("✅ Documentación mayormente completa. Revisar elementos menores.")
        else:
            recommendations.append("🎉 Documentación completa según Anexo I.")
        
        # Recomendaciones por sección
        for section_name, section_data in verification_results.items():
            section_completion = section_data["completion_percentage"]
            
            if section_completion < 50:
                recommendations.append(f"🔍 Revisar sección {section_name} - Muy incompleta ({section_completion:.1f}%)")
            elif section_completion < 75:
                recommendations.append(f"📝 Completar sección {section_name} - Parcial ({section_completion:.1f}%)")
        
        return recommendations
    
    def get_missing_elements(self, verification_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Obtener lista de elementos faltantes"""
        
        missing_elements = []
        
        for section_name, section_data in verification_results.items():
            for element_name, element_result in section_data["elements"].items():
                if not element_result["presente"]:
                    missing_elements.append({
                        "section": section_name,
                        "element": element_name,
                        "confidence": element_result["confidence"],
                        "keywords_matched": element_result["keywords_matched"],
                        "keywords_total": element_result["keywords_total"]
                    })
        
        return missing_elements
    
    def _create_default_anexo(self):
        """Crear anexo1.json por defecto"""
        anexo_path = Path("Normativa/anexo1.json")
        anexo_path.parent.mkdir(exist_ok=True)
        
        default_anexo = self._get_default_anexo_structure()
        
        with open(anexo_path, 'w', encoding='utf-8') as f:
            json.dump(default_anexo, f, indent=2, ensure_ascii=False)
    
    def _get_default_anexo_structure(self) -> Dict[str, Any]:
        """Obtener estructura por defecto del anexo"""
        return {
            "Proyecto_Basico_Obligatorio": {
                "Memoria": {
                    "datos_generales": {
                        "keywords": ["datos generales", "identificación", "promotor", "situación", "referencia catastral"]
                    },
                    "agentes": {
                        "keywords": ["agentes", "arquitecto", "promotor", "constructor", "director obra", "coordinador seguridad"]
                    },
                    "informacion_previa": {
                        "keywords": ["información previa", "antecedentes", "condicionantes", "normativa urbanística"]
                    },
                    "descripcion_proyecto": {
                        "keywords": ["descripción", "programa", "necesidades", "justificación", "solución adoptada"]
                    },
                    "descripcion_geometrica": {
                        "keywords": ["descripción geométrica", "volumen", "superficie", "dimensiones", "geometría"]
                    },
                    "normativa_aplicable": {
                        "keywords": ["normativa", "código técnico", "CTE", "ordenanza", "reglamento"]
                    },
                    "accesibilidad": {
                        "keywords": ["accesibilidad", "barreras arquitectónicas", "discapacidad", "acceso"]
                    },
                    "sistemas_estructurales": {
                        "keywords": ["estructura", "cimentación", "forjados", "pilares", "vigas", "muros"]
                    },
                    "sistemas_ambientales": {
                        "keywords": ["climatización", "ventilación", "calefacción", "refrigeración", "ambiente"]
                    },
                    "sistemas_servicios": {
                        "keywords": ["instalaciones", "fontanería", "electricidad", "telecomunicaciones", "gas"]
                    },
                    "prestaciones_cte": {
                        "keywords": ["prestaciones", "requisitos básicos", "seguridad", "habitabilidad", "funcionalidad"]
                    },
                    "presupuesto_valoracion": {
                        "keywords": ["presupuesto", "valoración", "coste", "precio", "importe"]
                    },
                    "justificacion_suelo": {
                        "keywords": ["características suelo", "geotécnico", "cimentación", "terreno"]
                    },
                    "parametros_cimentacion": {
                        "keywords": ["parámetros", "cimentación", "zapatas", "losa", "pilotes"]
                    },
                    "justificacion_incendio": {
                        "keywords": ["seguridad incendio", "evacuación", "sectores", "resistencia fuego", "DB-SI"]
                    }
                },
                "Planos": {
                    "Plano_Situacion": {
                        "keywords": ["situación", "emplazamiento", "localización", "entorno"]
                    },
                    "Plano_Emplazamiento": {
                        "keywords": ["emplazamiento", "parcela", "solar", "linderos"]
                    },
                    "Plantas_Generales": {
                        "keywords": ["plantas", "distribución", "layout", "espacios"]
                    },
                    "Alzados_Secciones": {
                        "keywords": ["alzados", "secciones", "fachadas", "cortes"]
                    },
                    "Planos_Especificos": {
                        "keywords": ["cubiertas", "incendios", "instalaciones", "detalles"]
                    }
                },
                "Presupuesto": {
                    "mediciones": {
                        "keywords": ["mediciones", "cantidades", "unidades", "metros"]
                    },
                    "presupuesto": {
                        "keywords": ["presupuesto", "precios", "importe", "total"]
                    }
                }
            }
        }

