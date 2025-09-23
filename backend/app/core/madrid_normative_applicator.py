"""
Aplicador de normativa específica de Madrid.
Implementa la lógica correcta según las especificaciones:

1. NORMATIVA GENERAL (siempre aplica):
   - Todos los PDFs de Normativa/DOCUMENTOS BASICOS
   - Normativa/PGOUM/pgoum_general universal.pdf

2. NORMATIVA POR USO (aplicada según uso principal/secundario):
   - Normativa/PGOUM/pgoum_[tipo_de_edificio].pdf

3. NORMATIVA DE APOYO (solo edificios existentes):
   - Todos los PDFs de Normativa/DOCUMENTOS DE APOYO
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
    type: str  # 'basic', 'pgoum_general', 'pgoum_specific', 'support'
    building_types: List[str]
    floors: List[str]
    description: str
    priority: int
    is_existing_building_only: bool = False

@dataclass
class NormativeApplication:
    """Aplicación de normativa específica."""
    project_id: str
    primary_use: str
    secondary_uses: Dict[str, List[str]]  # use_type -> [floors]
    is_existing_building: bool
    applicable_documents: List[NormativeDocument]
    floor_assignments: Dict[str, List[str]]  # floor -> [document_names]
    compliance_requirements: Dict[str, List[Dict[str, Any]]]

class MadridNormativeApplicator:
    """Aplicador de normativa específica de Madrid con lógica correcta."""
    
    def __init__(self, normative_path: str = "Normativa"):
        """
        Inicializar el aplicador de normativa.
        
        Args:
            normative_path: Ruta a la carpeta de normativa
        """
        self.normative_path = Path(normative_path)
        self.documents = self._load_normative_documents()
        self.building_type_mapping = self._initialize_building_type_mapping()
        
        logger.info("MadridNormativeApplicator initialized with correct logic")
    
    def _load_normative_documents(self) -> Dict[str, NormativeDocument]:
        """Cargar todos los documentos normativos disponibles."""
        documents = {}
        
        try:
            # 1. DOCUMENTOS BÁSICOS (siempre aplicables)
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
                                priority=1,
                                is_existing_building_only=False
                            )
            
            # 2. PGOUM GENERAL UNIVERSAL (siempre aplicable)
            pgoum_general_path = self.normative_path / "PGOUM" / "pgoum_general universal.pdf"
            if pgoum_general_path.exists():
                documents["pgoum_general_universal"] = NormativeDocument(
                    name="pgoum_general_universal",
                    path=str(pgoum_general_path),
                    type="pgoum_general",
                    building_types=["all"],
                    floors=["all"],
                    description="PGOUM General Universal",
                    priority=1,
                    is_existing_building_only=False
                )
            
            # 3. PGOUM ESPECÍFICOS POR TIPO DE EDIFICIO
            pgoum_path = self.normative_path / "PGOUM"
            if pgoum_path.exists():
                for doc_file in pgoum_path.glob("pgoum_*.pdf"):
                    if doc_file.name == "pgoum_general universal.pdf":
                        continue  # Ya procesado arriba
                    
                    doc_name = doc_file.stem
                    building_type = self._extract_building_type_from_filename(doc_name)
                    
                    documents[doc_name] = NormativeDocument(
                        name=doc_name,
                        path=str(doc_file),
                        type="pgoum_specific",
                        building_types=[building_type],
                        floors=["all"],
                        description=f"PGOUM específico para {building_type}",
                        priority=2,
                        is_existing_building_only=False
                    )
            
            # 4. DOCUMENTOS DE APOYO (solo edificios existentes)
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
                                priority=3,
                                is_existing_building_only=True
                            )
            
            logger.info(f"Cargados {len(documents)} documentos normativos")
            return documents
            
        except Exception as e:
            logger.error(f"Error cargando documentos normativos: {e}")
            return {}
    
    def _extract_building_type_from_filename(self, filename: str) -> str:
        """Extraer el tipo de edificio del nombre del archivo."""
        # Remover prefijo "pgoum_"
        if filename.startswith("pgoum_"):
            building_type = filename[6:]  # Remover "pgoum_"
        else:
            building_type = filename
        
        # Mapear nombres a tipos estándar
        type_mapping = {
            "residencial": "residencial",
            "industrial": "industrial",
            "servicios terciarios": "terciario",
            "garaje-aparcamiento": "garaje",
            "dotacional administracion publica": "administracion_publica",
            "dotacional deportivo": "deportivo",
            "dotacional equipamiento": "equipamiento",
            "dotacional infraestructural": "infraestructural",
            "dotacional servicios publicos": "servicios_publicos",
            "dotacional transporte": "transporte",
            "dotacional via publica": "via_publica",
            "dotacional zona verde": "zona_verde"
        }
        
        return type_mapping.get(building_type, building_type)
    
    def _initialize_building_type_mapping(self) -> Dict[str, str]:
        """Inicializar mapeo de tipos de edificio."""
        return {
            "residencial": "residencial",
            "terciario": "servicios terciarios",
            "industrial": "industrial",
            "garaje": "garaje-aparcamiento",
            "administracion_publica": "dotacional administracion publica",
            "deportivo": "dotacional deportivo",
            "equipamiento": "dotacional equipamiento",
            "infraestructural": "dotacional infraestructural",
            "servicios_publicos": "dotacional servicios publicos",
            "transporte": "dotacional transporte",
            "via_publica": "dotacional via publica",
            "zona_verde": "dotacional zona verde"
        }
    
    def apply_normative(self, project_data: Dict[str, Any]) -> NormativeApplication:
        """
        Aplicar normativa según la lógica correcta.
        
        Args:
            project_data: Datos del proyecto con primary_use, secondary_uses, is_existing_building
            
        Returns:
            Aplicación de normativa específica
        """
        try:
            logger.info("Aplicando normativa con lógica correcta")
            
            project_id = project_data.get('project_id', 'unknown')
            primary_use = project_data.get('primary_use', 'residencial')
            secondary_uses = project_data.get('secondary_uses', {})
            is_existing_building = project_data.get('is_existing_building', False)
            
            logger.info(f"Proyecto: {project_id}, Uso principal: {primary_use}, "
                       f"Usos secundarios: {secondary_uses}, Edificio existente: {is_existing_building}")
            
            applicable_documents = []
            
            # 1. APLICAR DOCUMENTOS BÁSICOS (con lógica específica para DBSI)
            basic_docs = []
            for doc in self.documents.values():
                if doc.type == "basic":
                    # Lógica específica para DBSI según el tipo de uso
                    if doc.name in ["DBSI", "REGLAMENTO INSTALACIONES"]:
                        primary_use_normalized = self._normalize_building_type(primary_use)
                        if primary_use_normalized == "industrial":
                            # Para uso industrial: REGLAMENTO INSTALACIONES.pdf, NO DBSI.pdf
                            if doc.name == "REGLAMENTO INSTALACIONES":
                                basic_docs.append(doc)
                                logger.info(f"Aplicando REGLAMENTO INSTALACIONES para uso industrial")
                        else:
                            # Para otros usos: DBSI.pdf, NO REGLAMENTO INSTALACIONES.pdf
                            if doc.name == "DBSI":
                                basic_docs.append(doc)
                                logger.info(f"Aplicando DBSI para uso {primary_use}")
                    else:
                        # Todos los demás documentos básicos se aplican normalmente
                        basic_docs.append(doc)
            
            applicable_documents.extend(basic_docs)
            logger.info(f"Aplicando {len(basic_docs)} documentos básicos")
            
            # 2. APLICAR PGOUM GENERAL UNIVERSAL (siempre)
            pgoum_general = [doc for doc in self.documents.values() 
                           if doc.type == "pgoum_general"]
            applicable_documents.extend(pgoum_general)
            logger.info(f"Aplicando {len(pgoum_general)} documentos PGOUM general")
            
            # 3. APLICAR PGOUM ESPECÍFICO POR USO PRINCIPAL
            primary_use_normalized = self._normalize_building_type(primary_use)
            primary_pgoum = [doc for doc in self.documents.values() 
                           if doc.type == "pgoum_specific" and 
                           primary_use_normalized in doc.building_types]
            applicable_documents.extend(primary_pgoum)
            logger.info(f"Aplicando {len(primary_pgoum)} documentos PGOUM para uso principal: {primary_use}")
            
            # 4. APLICAR PGOUM ESPECÍFICO POR USOS SECUNDARIOS
            secondary_pgoum_docs = []
            for use_type, floors in secondary_uses.items():
                use_type_normalized = self._normalize_building_type(use_type)
                secondary_pgoum = [doc for doc in self.documents.values() 
                                 if doc.type == "pgoum_specific" and 
                                 use_type_normalized in doc.building_types]
                secondary_pgoum_docs.extend(secondary_pgoum)
                logger.info(f"Aplicando {len(secondary_pgoum)} documentos PGOUM para uso secundario: {use_type}")
            
            applicable_documents.extend(secondary_pgoum_docs)
            
            # 5. APLICAR DOCUMENTOS DE APOYO (solo edificios existentes)
            support_docs = []
            if is_existing_building:
                support_docs = [doc for doc in self.documents.values() 
                              if doc.type == "support"]
                applicable_documents.extend(support_docs)
                logger.info(f"Aplicando {len(support_docs)} documentos de apoyo (edificio existente)")
            else:
                logger.info("No aplicando documentos de apoyo (edificio nuevo)")
            
            # 6. ASIGNAR DOCUMENTOS A PLANTAS
            floor_assignments = self._assign_documents_to_floors(
                applicable_documents, primary_use, secondary_uses
            )
            
            # 7. GENERAR REQUISITOS DE CUMPLIMIENTO
            compliance_requirements = self._generate_compliance_requirements(
                applicable_documents, primary_use, secondary_uses, is_existing_building
            )
            
            application = NormativeApplication(
                project_id=project_id,
                primary_use=primary_use,
                secondary_uses=secondary_uses,
                is_existing_building=is_existing_building,
                applicable_documents=applicable_documents,
                floor_assignments=floor_assignments,
                compliance_requirements=compliance_requirements
            )
            
            logger.info(f"Normativa aplicada: {len(applicable_documents)} documentos, "
                       f"{len(floor_assignments)} asignaciones de plantas")
            
            return application
            
        except Exception as e:
            logger.error(f"Error aplicando normativa: {e}")
            raise
    
    def _normalize_building_type(self, building_type: str) -> str:
        """Normalizar tipo de edificio para búsqueda."""
        normalized = building_type.lower().strip()
        
        # Mapeo de tipos comunes
        type_mapping = {
            "residencial": "residencial",
            "terciario": "servicios terciarios",
            "comercial": "servicios terciarios",
            "industrial": "industrial",
            "garaje": "garaje-aparcamiento",
            "aparcamiento": "garaje-aparcamiento",
            "oficina": "servicios terciarios",
            "administracion": "dotacional administracion publica",
            "deportivo": "dotacional deportivo",
            "equipamiento": "dotacional equipamiento",
            "infraestructural": "dotacional infraestructural",
            "servicios publicos": "dotacional servicios publicos",
            "transporte": "dotacional transporte",
            "via publica": "dotacional via publica",
            "zona verde": "dotacional zona verde"
        }
        
        return type_mapping.get(normalized, normalized)
    
    def _assign_documents_to_floors(self, documents: List[NormativeDocument], 
                                  primary_use: str, secondary_uses: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Asignar documentos a plantas según la lógica correcta."""
        floor_assignments = {}
        
        # Obtener todas las plantas mencionadas en usos secundarios
        secondary_floors = set()
        for floors in secondary_uses.values():
            if isinstance(floors, list):
                secondary_floors.update(floors)
        
        # Para cada documento, determinar a qué plantas se aplica
        for doc in documents:
            doc_floors = []
            
            if doc.type in ["basic", "pgoum_general"]:
                # Documentos básicos y PGOUM general se aplican a todas las plantas
                doc_floors = ["all_floors"]
            elif doc.type == "pgoum_specific":
                # PGOUM específico se aplica según el uso
                building_type = doc.building_types[0] if doc.building_types else ""
                
                # Si es el tipo de uso principal
                if self._normalize_building_type(primary_use) == building_type:
                    # Se aplica a todas las plantas EXCEPTO las que tienen uso secundario
                    if secondary_floors:
                        doc_floors = ["primary_use_floors"]  # Planteas sin uso secundario
                    else:
                        doc_floors = ["all_floors"]
                else:
                    # Si es un tipo de uso secundario, se aplica solo a esas plantas
                    for use_type, floors in secondary_uses.items():
                        if self._normalize_building_type(use_type) == building_type:
                            doc_floors = floors if isinstance(floors, list) else []
                            break
            elif doc.type == "support":
                # Documentos de apoyo se aplican a todas las plantas
                doc_floors = ["all_floors"]
            
            # Asignar el documento a las plantas correspondientes
            for floor in doc_floors:
                if floor not in floor_assignments:
                    floor_assignments[floor] = []
                floor_assignments[floor].append(doc.name)
        
        return floor_assignments
    
    def _generate_compliance_requirements(self, documents: List[NormativeDocument], 
                                        primary_use: str, secondary_uses: Dict[str, List[str]], 
                                        is_existing_building: bool) -> Dict[str, List[Dict[str, Any]]]:
        """Generar requisitos de cumplimiento específicos."""
        requirements = {}
        
        for doc in documents:
            doc_requirements = []
            
            # Generar requisitos específicos según el tipo de documento
            if doc.type == "basic":
                doc_requirements = [
                    {
                        "requirement": f"Cumplimiento de {doc.description}",
                        "description": f"Aplicar normativa básica de {doc.description}",
                        "priority": "high",
                        "floors": ["all"],
                        "document_path": doc.path
                    }
                ]
            elif doc.type == "pgoum_general":
                doc_requirements = [
                    {
                        "requirement": "Cumplimiento PGOUM General Universal",
                        "description": "Aplicar normativa general del PGOUM",
                        "priority": "high",
                        "floors": ["all"],
                        "document_path": doc.path
                    }
                ]
            elif doc.type == "pgoum_specific":
                building_type = doc.building_types[0] if doc.building_types else ""
                doc_requirements = [
                    {
                        "requirement": f"Cumplimiento PGOUM {building_type}",
                        "description": f"Aplicar normativa específica para {building_type}",
                        "priority": "high",
                        "floors": ["specific"],
                        "document_path": doc.path
                    }
                ]
            elif doc.type == "support":
                doc_requirements = [
                    {
                        "requirement": f"Cumplimiento documento de apoyo",
                        "description": f"Aplicar normativa de apoyo {doc.description}",
                        "priority": "medium",
                        "floors": ["all"],
                        "document_path": doc.path,
                        "existing_building_only": True
                    }
                ]
            
            requirements[doc.name] = doc_requirements
        
        return requirements
    
    def get_normative_summary(self, application: NormativeApplication) -> Dict[str, Any]:
        """Generar resumen de la aplicación de normativa."""
        summary = {
            "project_id": application.project_id,
            "primary_use": application.primary_use,
            "secondary_uses": application.secondary_uses,
            "is_existing_building": application.is_existing_building,
            "total_documents": len(application.applicable_documents),
            "document_types": {
                "basic": len([d for d in application.applicable_documents if d.type == "basic"]),
                "pgoum_general": len([d for d in application.applicable_documents if d.type == "pgoum_general"]),
                "pgoum_specific": len([d for d in application.applicable_documents if d.type == "pgoum_specific"]),
                "support": len([d for d in application.applicable_documents if d.type == "support"])
            },
            "floor_assignments": len(application.floor_assignments),
            "compliance_requirements": sum(len(reqs) for reqs in application.compliance_requirements.values())
        }
        
        return summary