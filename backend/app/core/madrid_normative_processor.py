"""
Procesador de normativa Madrid (PGOUM) para el sistema de verificación.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class NormativeDocument:
    """Documento normativo procesado."""
    id: str
    name: str
    path: str
    category: str  # 'cte', 'pgoum_general', 'pgoum_specific', 'support'
    building_type: Optional[str] = None
    pages: int = 0
    sections: List[str] = None
    processed_at: str = None
    file_size: int = 0
    checksum: str = None
    
    def __post_init__(self):
        if self.sections is None:
            self.sections = []
        if self.processed_at is None:
            self.processed_at = datetime.now().isoformat()

@dataclass
class NormativeSection:
    """Sección de documento normativo."""
    section_id: str
    title: str
    content: str
    page_number: int
    document_id: str
    building_types: List[str] = None
    floor_applicability: List[float] = None
    
    def __post_init__(self):
        if self.building_types is None:
            self.building_types = []
        if self.floor_applicability is None:
            self.floor_applicability = []

class MadridNormativeProcessor:
    """Procesador de normativa Madrid."""
    
    def __init__(self, normative_path: str = "Normativa"):
        self.logger = logging.getLogger(f"{__name__}.MadridNormativeProcessor")
        self.normative_path = Path(normative_path)
        self.processed_documents = {}
        self.normative_sections = {}
        
        # Configuración de categorías
        self.categories = {
            'cte': {
                'path': 'DOCUMENTOS_BASICOS',
                'always_applicable': True,
                'building_types': None  # Aplicable a todos
            },
            'pgoum_general': {
                'path': 'PGOUM',
                'file': 'pgoum_general_universal.pdf',
                'always_applicable': True,
                'building_types': None
            },
            'pgoum_specific': {
                'path': 'PGOUM',
                'always_applicable': False,
                'building_types': [
                    'residencial', 'industrial', 'garaje-aparcamiento',
                    'servicios_terciarios', 'dotacional_zona_verde',
                    'dotacional_deportivo', 'dotacional_equipamiento',
                    'dotacional_servicios_publicos', 'dotacional_administracion_publica',
                    'dotacional_infraestructural', 'dotacional_via_publica',
                    'dotacional_transporte'
                ]
            },
            'support': {
                'path': 'DOCUMENTOS_APOYO',
                'always_applicable': False,
                'building_types': None,  # Solo para edificios existentes
                'requires_existing_building': True
            }
        }
    
    def scan_normative_documents(self) -> Dict[str, NormativeDocument]:
        """Escanear y catalogar documentos normativos."""
        self.logger.info("Escaneando documentos normativos...")
        
        documents = {}
        
        for category, config in self.categories.items():
            category_path = self.normative_path / config['path']
            
            if not category_path.exists():
                self.logger.warning(f"Directorio no encontrado: {category_path}")
                continue
            
            # Procesar archivos PDF
            for pdf_file in category_path.glob("*.pdf"):
                doc_id = self._generate_document_id(pdf_file)
                
                # Determinar tipo de edificio para documentos específicos
                building_type = None
                if category == 'pgoum_specific':
                    building_type = self._extract_building_type_from_filename(pdf_file.name)
                
                document = NormativeDocument(
                    id=doc_id,
                    name=pdf_file.stem,
                    path=str(pdf_file),
                    category=category,
                    building_type=building_type,
                    file_size=pdf_file.stat().st_size,
                    checksum=self._calculate_checksum(pdf_file)
                )
                
                documents[doc_id] = document
                self.logger.debug(f"Documento catalogado: {document.name} ({category})")
        
        self.processed_documents = documents
        self.logger.info(f"Total documentos catalogados: {len(documents)}")
        return documents
    
    def _generate_document_id(self, file_path: Path) -> str:
        """Generar ID único para documento."""
        relative_path = file_path.relative_to(self.normative_path)
        path_str = str(relative_path).replace(os.sep, '_').replace('.pdf', '')
        return hashlib.md5(path_str.encode()).hexdigest()[:12]
    
    def _extract_building_type_from_filename(self, filename: str) -> Optional[str]:
        """Extraer tipo de edificio del nombre del archivo."""
        filename_lower = filename.lower().replace('.pdf', '')
        
        # Mapeo de nombres de archivo a tipos de edificio
        building_type_mapping = {
            'pgoum_residencial': 'residencial',
            'pgoum_industrial': 'industrial',
            'pgoum_garaje-aparcamiento': 'garaje-aparcamiento',
            'pgoum_servicios_terciarios': 'servicios_terciarios',
            'pgoum_dotacional_zona_verde': 'dotacional_zona_verde',
            'pgoum_dotacional_deportivo': 'dotacional_deportivo',
            'pgoum_dotacional_equipamiento': 'dotacional_equipamiento',
            'pgoum_dotacional_servicios_publicos': 'dotacional_servicios_publicos',
            'pgoum_dotacional_administracion_publica': 'dotacional_administracion_publica',
            'pgoum_dotacional_infraestructural': 'dotacional_infraestructural',
            'pgoum_dotacional_via_publica': 'dotacional_via_publica',
            'pgoum_dotacional_transporte': 'dotacional_transporte'
        }
        
        return building_type_mapping.get(filename_lower)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calcular checksum del archivo."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_applicable_documents(self, project_data: Dict[str, Any]) -> List[NormativeDocument]:
        """
        Obtener documentos normativos aplicables a un proyecto.
        
        Args:
            project_data: Datos del proyecto Madrid
            
        Returns:
            Lista de documentos aplicables
        """
        applicable_docs = []
        
        for doc in self.processed_documents.values():
            if self._is_document_applicable(doc, project_data):
                applicable_docs.append(doc)
        
        self.logger.info(f"Documentos aplicables encontrados: {len(applicable_docs)}")
        return applicable_docs
    
    def _is_document_applicable(self, document: NormativeDocument, project_data: Dict[str, Any]) -> bool:
        """Verificar si un documento es aplicable al proyecto."""
        category_config = self.categories[document.category]
        
        # Documentos siempre aplicables
        if category_config['always_applicable']:
            return True
        
        # Documentos específicos por tipo de edificio
        if document.building_type:
            primary_use = project_data.get('primary_use')
            secondary_uses = project_data.get('secondary_uses', [])
            
            # Verificar uso principal
            if primary_use == document.building_type:
                return True
            
            # Verificar usos secundarios
            for secondary_use in secondary_uses:
                if secondary_use.get('use_type') == document.building_type:
                    return True
        
        # Documentos de apoyo (solo para edificios existentes)
        if document.category == 'support':
            return project_data.get('is_existing_building', False)
        
        return False
    
    def create_normative_index(self) -> Dict[str, Any]:
        """Crear índice de normativa para consultas rápidas."""
        index = {
            'by_category': {},
            'by_building_type': {},
            'by_floor': {},
            'metadata': {
                'total_documents': len(self.processed_documents),
                'created_at': datetime.now().isoformat(),
                'categories': list(self.categories.keys())
            }
        }
        
        # Indexar por categoría
        for doc in self.processed_documents.values():
            if doc.category not in index['by_category']:
                index['by_category'][doc.category] = []
            index['by_category'][doc.category].append(doc.id)
        
        # Indexar por tipo de edificio
        for doc in self.processed_documents.values():
            if doc.building_type:
                if doc.building_type not in index['by_building_type']:
                    index['by_building_type'][doc.building_type] = []
                index['by_building_type'][doc.building_type].append(doc.id)
        
        return index
    
    def save_processed_data(self, output_path: str = "data/normative_processed.json"):
        """Guardar datos procesados."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'documents': {doc_id: {
                'id': doc.id,
                'name': doc.name,
                'path': doc.path,
                'category': doc.category,
                'building_type': doc.building_type,
                'pages': doc.pages,
                'sections': doc.sections,
                'processed_at': doc.processed_at,
                'file_size': doc.file_size,
                'checksum': doc.checksum
            } for doc_id, doc in self.processed_documents.items()},
            'index': self.create_normative_index(),
            'metadata': {
                'processed_at': datetime.now().isoformat(),
                'total_documents': len(self.processed_documents)
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Datos procesados guardados en: {output_file}")
    
    def load_processed_data(self, input_path: str = "data/normative_processed.json") -> bool:
        """Cargar datos procesados."""
        input_file = Path(input_path)
        
        if not input_file.exists():
            self.logger.warning(f"Archivo de datos procesados no encontrado: {input_file}")
            return False
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruir documentos
            self.processed_documents = {}
            for doc_id, doc_data in data['documents'].items():
                document = NormativeDocument(
                    id=doc_data['id'],
                    name=doc_data['name'],
                    path=doc_data['path'],
                    category=doc_data['category'],
                    building_type=doc_data.get('building_type'),
                    pages=doc_data.get('pages', 0),
                    sections=doc_data.get('sections', []),
                    processed_at=doc_data.get('processed_at'),
                    file_size=doc_data.get('file_size', 0),
                    checksum=doc_data.get('checksum')
                )
                self.processed_documents[doc_id] = document
            
            self.logger.info(f"Datos procesados cargados: {len(self.processed_documents)} documentos")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cargando datos procesados: {e}")
            return False
