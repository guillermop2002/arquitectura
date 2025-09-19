"""
Aplicador de normativa específica de Madrid.
Aplica la normativa correcta según el tipo de edificio, uso secundario y plantas.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json

logger = logging.getLogger(__name__)

@dataclass
class NormativeDocument:
    """Documento normativo aplicable."""
    name: str
    path: str
    type: str  # 'basic', 'pgoum', 'support'
    building_types: List[str]
    floors: List[str]
    description: str
    priority: int

@dataclass
class NormativeApplication:
    """Aplicación de normativa específica."""
    project_id: str
    primary_use: str
    secondary_uses: List[Dict[str, Any]]
    is_existing_building: bool
    applicable_documents: List[NormativeDocument]
    floor_assignments: Dict[str, List[str]]  # floor -> [document_names]
    compliance_requirements: Dict[str, List[Dict[str, Any]]]

class MadridNormativeApplicator:
    """Aplicador de normativa específica de Madrid."""
    
    def __init__(self, normative_path: str = "Normativa"):
        """
        Inicializar el aplicador de normativa.
        
        Args:
            normative_path: Ruta a la carpeta de normativa
        """
        self.normative_path = Path(normative_path)
        self.documents = self._load_normative_documents()
        self.building_type_mapping = self._initialize_building_type_mapping()
        
        logger.info("MadridNormativeApplicator initialized")
    
    def _load_normative_documents(self) -> Dict[str, NormativeDocument]:
        """Cargar todos los documentos normativos disponibles."""
        documents = {}
        
        try:
            # Documentos básicos (siempre aplicables)
            basic_path = self.normative_path / "DOCUMENTOS BASICOS"
            if basic_path.exists():
                for category in basic_path.iterdir():
                    if category.is_dir():
                        for doc_file in category.glob("*.pdf"):
                            doc_name = doc_file.stem
                            documents[doc_name] = NormativeDocument(
                                name=doc_name,
                                path=str(doc_file),
                                type="basic",
                                building_types=["all"],
                                floors=["all"],
                                description=f"Documento básico {category.name}",
                                priority=1
                            )
            
            # Documentos PGOUM (específicos por tipo de edificio)
            pgoum_path = self.normative_path / "PGOUM"
            if pgoum_path.exists():
                for doc_file in pgoum_path.glob("*.pdf"):
                    doc_name = doc_file.stem
                    building_type = self._extract_building_type_from_filename(doc_name)
                    
                    documents[doc_name] = NormativeDocument(
                        name=doc_name,
                        path=str(doc_file),
                        type="pgoum",
                        building_types=[building_type],
                        floors=["all"],
                        description=f"PGOUM para {building_type}",
                        priority=2
                    )
            
            # Documentos de apoyo (solo para edificios existentes)
            support_path = self.normative_path / "DOCUMENTOS DE APOYO"
            if support_path.exists():
                for category in support_path.iterdir():
                    if category.is_dir():
                        for doc_file in category.glob("*.pdf"):
                            doc_name = doc_file.stem
                            documents[doc_name] = NormativeDocument(
                                name=doc_name,
                                path=str(doc_file),
                                type="support",
                                building_types=["all"],
                                floors=["all"],
                                description=f"Documento de apoyo {category.name}",
                                priority=3
                            )
            
            logger.info(f"Cargados {len(documents)} documentos normativos")
            
        except Exception as e:
            logger.error(f"Error cargando documentos normativos: {e}")
        
        return documents
    
    def _extract_building_type_from_filename(self, filename: str) -> str:
        """Extraer tipo de edificio del nombre del archivo PGOUM."""
        filename_lower = filename.lower()
        
        if "residencial" in filename_lower:
            return "residencial"
        elif "industrial" in filename_lower:
            return "industrial"
        elif "servicios terciarios" in filename_lower:
            return "servicios_terciarios"
        elif "garaje-aparcamiento" in filename_lower:
            return "garaje_aparcamiento"
        elif "dotacional" in filename_lower:
            if "administracion publica" in filename_lower:
                return "dotacional_administracion_publica"
            elif "deportivo" in filename_lower:
                return "dotacional_deportivo"
            elif "equipamiento" in filename_lower:
                return "dotacional_equipamiento"
            elif "infraestructural" in filename_lower:
                return "dotacional_infraestructural"
            elif "servicios publicos" in filename_lower:
                return "dotacional_servicios_publicos"
            elif "transporte" in filename_lower:
                return "dotacional_transporte"
            elif "via publica" in filename_lower:
                return "dotacional_via_publica"
            elif "zona verde" in filename_lower:
                return "dotacional_zona_verde"
            else:
                return "dotacional"
        elif "general universal" in filename_lower:
            return "general_universal"
        else:
            return "unknown"
    
    def _initialize_building_type_mapping(self) -> Dict[str, List[str]]:
        """Inicializar mapeo de tipos de edificio a documentos PGOUM."""
        return {
            "residencial": ["pgoum_residencial", "pgoum_general universal"],
            "industrial": ["pgoum_industrial", "pgoum_general universal"],
            "servicios_terciarios": ["pgoum_servicios terciarios", "pgoum_general universal"],
            "garaje_aparcamiento": ["pgoum_garaje-aparcamiento", "pgoum_general universal"],
            "dotacional_administracion_publica": ["pgoum_dotacional administracion publica", "pgoum_general universal"],
            "dotacional_deportivo": ["pgoum_dotacional deportivo", "pgoum_general universal"],
            "dotacional_equipamiento": ["pgoum_dotacional equipamiento", "pgoum_general universal"],
            "dotacional_infraestructural": ["pgoum_dotacional infraestructural", "pgoum_general universal"],
            "dotacional_servicios_publicos": ["pgoum_dotacional servicios publicos", "pgoum_general universal"],
            "dotacional_transporte": ["pgoum_dotacional transporte", "pgoum_general universal"],
            "dotacional_via_publica": ["pgoum_dotacional via publica", "pgoum_general universal"],
            "dotacional_zona_verde": ["pgoum_dotacional zona verde", "pgoum_general universal"],
            "dotacional": ["pgoum_general universal"]
        }
    
    def apply_normative(self, 
                       project_data: Dict[str, Any], 
                       primary_use: str, 
                       secondary_uses: List[Dict[str, Any]], 
                       is_existing_building: bool) -> NormativeApplication:
        """
        Aplicar normativa específica según el tipo de edificio y usos.
        
        Args:
            project_data: Datos del proyecto
            primary_use: Uso principal del edificio
            secondary_uses: Usos secundarios con sus plantas
            is_existing_building: Si es edificio existente
            
        Returns:
            Aplicación de normativa específica
        """
        try:
            logger.info(f"Aplicando normativa para uso principal: {primary_use}, "
                       f"usos secundarios: {len(secondary_uses)}, "
                       f"edificio existente: {is_existing_building}")
            
            # Determinar documentos aplicables
            applicable_documents = self._determine_applicable_documents(
                primary_use, secondary_uses, is_existing_building
            )
            
            # Asignar documentos por plantas
            floor_assignments = self._assign_documents_to_floors(
                primary_use, secondary_uses, applicable_documents
            )
            
            # Generar requisitos de cumplimiento
            compliance_requirements = self._generate_compliance_requirements(
                applicable_documents, floor_assignments
            )
            
            # Crear aplicación de normativa
            application = NormativeApplication(
                project_id=project_data.get('project_id', 'unknown'),
                primary_use=primary_use,
                secondary_uses=secondary_uses,
                is_existing_building=is_existing_building,
                applicable_documents=applicable_documents,
                floor_assignments=floor_assignments,
                compliance_requirements=compliance_requirements
            )
            
            logger.info(f"Normativa aplicada: {len(applicable_documents)} documentos, "
                       f"{len(floor_assignments)} plantas asignadas")
            
            return application
            
        except Exception as e:
            logger.error(f"Error aplicando normativa: {e}")
            raise
    
    def _determine_applicable_documents(self, 
                                      primary_use: str, 
                                      secondary_uses: List[Dict[str, Any]], 
                                      is_existing_building: bool) -> List[NormativeDocument]:
        """Determinar documentos normativos aplicables."""
        applicable = []
        
        # 1. Documentos básicos (siempre aplicables)
        for doc_name, doc in self.documents.items():
            if doc.type == "basic":
                applicable.append(doc)
        
        # 2. PGOUM general universal (siempre aplicable)
        if "pgoum_general universal" in self.documents:
            applicable.append(self.documents["pgoum_general universal"])
        
        # 3. PGOUM específico para uso principal
        if primary_use in self.building_type_mapping:
            for doc_name in self.building_type_mapping[primary_use]:
                if doc_name in self.documents:
                    applicable.append(self.documents[doc_name])
        
        # 4. PGOUM específico para usos secundarios
        for secondary_use in secondary_uses:
            use_type = secondary_use.get('use_type', '')
            if use_type in self.building_type_mapping:
                for doc_name in self.building_type_mapping[use_type]:
                    if doc_name in self.documents and doc_name not in [d.name for d in applicable]:
                        applicable.append(self.documents[doc_name])
        
        # 5. Documentos de apoyo (solo para edificios existentes)
        if is_existing_building:
            for doc_name, doc in self.documents.items():
                if doc.type == "support":
                    applicable.append(doc)
        
        return applicable
    
    def _assign_documents_to_floors(self, 
                                   primary_use: str, 
                                   secondary_uses: List[Dict[str, Any]], 
                                   applicable_documents: List[NormativeDocument]) -> Dict[str, List[str]]:
        """Asignar documentos normativos a plantas específicas."""
        floor_assignments = {}
        
        # Obtener plantas de usos secundarios
        secondary_floors = {}
        for secondary_use in secondary_uses:
            use_type = secondary_use.get('use_type', '')
            floors = secondary_use.get('floors', [])
            for floor in floors:
                if floor not in secondary_floors:
                    secondary_floors[floor] = []
                secondary_floors[floor].append(use_type)
        
        # Obtener documentos por tipo
        basic_docs = [d for d in applicable_documents if d.type == "basic"]
        pgoum_general = [d for d in applicable_documents if "pgoum_general universal" in d.name]
        pgoum_primary = [d for d in applicable_documents if d.type == "pgoum" and d.name != "pgoum_general universal"]
        support_docs = [d for d in applicable_documents if d.type == "support"]
        
        # Asignar documentos a cada planta
        # Asumir rango de plantas desde -5 hasta 20
        for floor_num in range(-5, 21):
            floor_str = str(floor_num)
            floor_docs = []
            
            # 1. Documentos básicos (siempre aplicables a todas las plantas)
            floor_docs.extend([d.name for d in basic_docs])
            
            # 2. PGOUM general universal (siempre aplicable)
            floor_docs.extend([d.name for d in pgoum_general])
            
            # 3. PGOUM específico según uso de la planta
            if floor_str in secondary_floors:
                # Planta con uso secundario - aplicar normativa del uso secundario
                for use_type in secondary_floors[floor_str]:
                    use_docs = [d for d in pgoum_primary if use_type in d.name]
                    floor_docs.extend([d.name for d in use_docs])
            else:
                # Planta con uso principal - aplicar normativa del uso principal
                primary_docs = [d for d in pgoum_primary if primary_use in d.name]
                floor_docs.extend([d.name for d in primary_docs])
            
            # 4. Documentos de apoyo (solo para edificios existentes)
            # Nota: is_existing_building se pasa desde apply_normative
            # floor_docs.extend([d.name for d in support_docs])
            
            floor_assignments[floor_str] = list(set(floor_docs))  # Eliminar duplicados
        
        return floor_assignments
    
    def _generate_compliance_requirements(self, 
                                        applicable_documents: List[NormativeDocument], 
                                        floor_assignments: Dict[str, List[str]]) -> Dict[str, List[Dict[str, Any]]]:
        """Generar requisitos de cumplimiento específicos."""
        requirements = {}
        
        for doc in applicable_documents:
            doc_requirements = []
            
            if doc.type == "basic":
                # Requisitos básicos del CTE
                doc_requirements.extend(self._get_basic_requirements(doc.name))
            elif doc.type == "pgoum":
                # Requisitos específicos del PGOUM
                doc_requirements.extend(self._get_pgoum_requirements(doc.name))
            elif doc.type == "support":
                # Requisitos de documentos de apoyo
                doc_requirements.extend(self._get_support_requirements(doc.name))
            
            requirements[doc.name] = doc_requirements
        
        return requirements
    
    def _get_basic_requirements(self, doc_name: str) -> List[Dict[str, Any]]:
        """Obtener requisitos de documentos básicos."""
        requirements = []
        
        if "DBHE" in doc_name:
            requirements.extend([
                {
                    "id": "dbhe_01",
                    "title": "Limitación de demanda energética",
                    "description": "Verificar cumplimiento de la limitación de demanda energética",
                    "severity": "high",
                    "category": "energy"
                },
                {
                    "id": "dbhe_02",
                    "title": "Eficiencia energética de las instalaciones",
                    "description": "Verificar eficiencia de instalaciones térmicas",
                    "severity": "high",
                    "category": "energy"
                }
            ])
        elif "DBHR" in doc_name:
            requirements.extend([
                {
                    "id": "dbhr_01",
                    "title": "Protección contra el ruido",
                    "description": "Verificar aislamiento acústico",
                    "severity": "medium",
                    "category": "acoustic"
                }
            ])
        elif "DBSI" in doc_name:
            requirements.extend([
                {
                    "id": "dbsi_01",
                    "title": "Seguridad contra incendios",
                    "description": "Verificar medidas de protección contra incendios",
                    "severity": "critical",
                    "category": "fire_safety"
                }
            ])
        elif "DBSUA" in doc_name:
            requirements.extend([
                {
                    "id": "dbsua_01",
                    "title": "Seguridad de utilización",
                    "description": "Verificar accesibilidad y seguridad de uso",
                    "severity": "high",
                    "category": "safety"
                }
            ])
        
        return requirements
    
    def _get_pgoum_requirements(self, doc_name: str) -> List[Dict[str, Any]]:
        """Obtener requisitos específicos del PGOUM."""
        requirements = []
        
        if "residencial" in doc_name:
            requirements.extend([
                {
                    "id": "pgoum_res_01",
                    "title": "Superficie mínima de viviendas",
                    "description": "Verificar superficie mínima según PGOUM residencial",
                    "severity": "high",
                    "category": "residential"
                },
                {
                    "id": "pgoum_res_02",
                    "title": "Iluminación natural",
                    "description": "Verificar iluminación natural en viviendas",
                    "severity": "medium",
                    "category": "residential"
                }
            ])
        elif "industrial" in doc_name:
            requirements.extend([
                {
                    "id": "pgoum_ind_01",
                    "title": "Distancia a viviendas",
                    "description": "Verificar distancia mínima a viviendas",
                    "severity": "critical",
                    "category": "industrial"
                },
                {
                    "id": "pgoum_ind_02",
                    "title": "Accesos y circulaciones",
                    "description": "Verificar accesos para vehículos industriales",
                    "severity": "high",
                    "category": "industrial"
                }
            ])
        elif "garaje-aparcamiento" in doc_name:
            requirements.extend([
                {
                    "id": "pgoum_gar_01",
                    "title": "Dimensiones de plazas",
                    "description": "Verificar dimensiones mínimas de plazas de aparcamiento",
                    "severity": "high",
                    "category": "parking"
                },
                {
                    "id": "pgoum_gar_02",
                    "title": "Ventilación",
                    "description": "Verificar sistema de ventilación del garaje",
                    "severity": "critical",
                    "category": "parking"
                }
            ])
        
        return requirements
    
    def _get_support_requirements(self, doc_name: str) -> List[Dict[str, Any]]:
        """Obtener requisitos de documentos de apoyo."""
        requirements = []
        
        # Requisitos específicos para edificios existentes
        requirements.extend([
            {
                "id": "support_01",
                "title": "Adaptación a normativa vigente",
                "description": "Verificar adaptación a normativa actual",
                "severity": "medium",
                "category": "adaptation"
            },
            {
                "id": "support_02",
                "title": "Mejoras de accesibilidad",
                "description": "Verificar mejoras de accesibilidad en edificios existentes",
                "severity": "high",
                "category": "accessibility"
            }
        ])
        
        return requirements
    
    def get_normative_summary(self, application: NormativeApplication) -> Dict[str, Any]:
        """Obtener resumen de la aplicación de normativa."""
        return {
            "project_id": application.project_id,
            "primary_use": application.primary_use,
            "secondary_uses": application.secondary_uses,
            "is_existing_building": application.is_existing_building,
            "total_documents": len(application.applicable_documents),
            "documents_by_type": {
                "basic": len([d for d in application.applicable_documents if d.type == "basic"]),
                "pgoum": len([d for d in application.applicable_documents if d.type == "pgoum"]),
                "support": len([d for d in application.applicable_documents if d.type == "support"])
            },
            "floors_covered": len(application.floor_assignments),
            "total_requirements": sum(len(reqs) for reqs in application.compliance_requirements.values()),
            "critical_requirements": sum(
                len([r for r in reqs if r.get("severity") == "critical"])
                for reqs in application.compliance_requirements.values()
            )
        }
