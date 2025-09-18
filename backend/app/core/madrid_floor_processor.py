"""
Procesador inteligente de plantas para el sistema Madrid.
Convierte descripciones de plantas en formato texto a números.
"""

import re
import logging
from typing import List, Union, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FloorMapping:
    """Mapeo de descripción de planta a número."""
    description: str
    number: float
    category: str  # 'special', 'basement', 'ground', 'floor'

class MadridFloorProcessor:
    """Procesador inteligente de plantas para Madrid."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MadridFloorProcessor")
        
        # Mapeos de plantas especiales
        self.special_floors = {
            'entresótano': -0.5,
            'entre-sótano': -0.5,
            'entre sotano': -0.5,
            'entresotano': -0.5,
            'planta baja': 0,
            'planta 0': 0,
            'pb': 0,
            'p.b.': 0,
            'entreplanta': 0.5,
            'entre-planta': 0.5,
            'entre planta': 0.5,
            'entresuelo': 0.5,
            'entresuelos': 0.5
        }
        
        # Patrones para sótanos
        self.basement_patterns = [
            r'sótano\s*(\d+)',
            r'sotano\s*(\d+)',
            r's\.\s*(\d+)',
            r's-\d+',
            r'subterraneo\s*(\d+)',
            r'subsuelo\s*(\d+)',
            r'planta\s*-(\d+)',
            r'p\.\s*-(\d+)',
            r'nivel\s*-(\d+)'
        ]
        
        # Patrones para plantas sobre rasante
        self.floor_patterns = [
            r'planta\s*(\d+)',
            r'piso\s*(\d+)',
            r'p\.\s*(\d+)',
            r'nivel\s*(\d+)',
            r'p\d+',
            r'(\d+)\s*º?\s*piso',
            r'(\d+)\s*º?\s*planta'
        ]
        
        # Números ordinales en español
        self.ordinal_numbers = {
            'primera': 1, 'primero': 1, '1ª': 1, '1º': 1, '1er': 1,
            'segunda': 2, 'segundo': 2, '2ª': 2, '2º': 2, '2do': 2,
            'tercera': 3, 'tercero': 3, '3ª': 3, '3º': 3, '3er': 3,
            'cuarta': 4, 'cuarto': 4, '4ª': 4, '4º': 4, '4to': 4,
            'quinta': 5, 'quinto': 5, '5ª': 5, '5º': 5, '5to': 5,
            'sexta': 6, 'sexto': 6, '6ª': 6, '6º': 6, '6to': 6,
            'séptima': 7, 'séptimo': 7, '7ª': 7, '7º': 7, '7mo': 7,
            'octava': 8, 'octavo': 8, '8ª': 8, '8º': 8, '8vo': 8,
            'novena': 9, 'noveno': 9, '9ª': 9, '9º': 9, '9no': 9,
            'décima': 10, 'décimo': 10, '10ª': 10, '10º': 10, '10mo': 10
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalizar texto para procesamiento."""
        if not text:
            return ""
        
        # Convertir a minúsculas y limpiar
        text = text.lower().strip()
        
        # Eliminar caracteres especiales excepto números y letras
        text = re.sub(r'[^\w\s\d\-\.]', ' ', text)
        
        # Normalizar espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_floor_number(self, floor_text: str) -> Union[float, None]:
        """
        Extraer número de planta de texto descriptivo.
        
        Args:
            floor_text: Texto descriptivo de la planta
            
        Returns:
            Número de planta o None si no se puede extraer
        """
        if not floor_text:
            return None
        
        normalized_text = self.normalize_text(floor_text)
        
        # 1. Verificar plantas especiales
        for desc, number in self.special_floors.items():
            if desc in normalized_text:
                self.logger.debug(f"Planta especial detectada: '{floor_text}' -> {number}")
                return number
        
        # 2. Verificar números ordinales
        for ordinal, number in self.ordinal_numbers.items():
            if ordinal in normalized_text:
                # Determinar si es sótano o planta
                if any(word in normalized_text for word in ['sótano', 'sotano', 'subterraneo', 'subsuelo']):
                    self.logger.debug(f"Sótano ordinal detectado: '{floor_text}' -> -{number}")
                    return -number
                else:
                    self.logger.debug(f"Planta ordinal detectada: '{floor_text}' -> {number}")
                    return number
        
        # 3. Verificar patrones de sótanos
        for pattern in self.basement_patterns:
            match = re.search(pattern, normalized_text)
            if match:
                number = int(match.group(1))
                self.logger.debug(f"Sótano detectado: '{floor_text}' -> -{number}")
                return -number
        
        # 4. Verificar patrones de plantas
        for pattern in self.floor_patterns:
            match = re.search(pattern, normalized_text)
            if match:
                number = int(match.group(1))
                self.logger.debug(f"Planta detectada: '{floor_text}' -> {number}")
                return number
        
        # 5. Verificar si es un número directo
        number_match = re.search(r'(-?\d+(?:\.\d+)?)', normalized_text)
        if number_match:
            number = float(number_match.group(1))
            # Validar rango
            if -100 <= number <= 100:
                self.logger.debug(f"Número directo detectado: '{floor_text}' -> {number}")
                return number
        
        self.logger.warning(f"No se pudo extraer número de planta de: '{floor_text}'")
        return None
    
    def process_floor_list(self, floor_descriptions: List[str]) -> List[float]:
        """
        Procesar lista de descripciones de plantas.
        
        Args:
            floor_descriptions: Lista de descripciones de plantas
            
        Returns:
            Lista de números de plantas procesados
        """
        processed_floors = []
        
        for desc in floor_descriptions:
            floor_number = self.extract_floor_number(desc)
            if floor_number is not None:
                processed_floors.append(floor_number)
            else:
                self.logger.warning(f"Descripción de planta no procesada: '{desc}'")
        
        # Eliminar duplicados y ordenar
        processed_floors = sorted(list(set(processed_floors)))
        
        self.logger.info(f"Plantas procesadas: {floor_descriptions} -> {processed_floors}")
        return processed_floors
    
    def get_floor_label(self, floor_number: float) -> str:
        """
        Obtener etiqueta legible para un número de planta.
        
        Args:
            floor_number: Número de planta
            
        Returns:
            Etiqueta legible de la planta
        """
        if floor_number == -0.5:
            return "Entresótano"
        elif floor_number == 0:
            return "Planta Baja"
        elif floor_number == 0.5:
            return "Entreplanta"
        elif floor_number < 0:
            return f"Sótano {abs(int(floor_number))}"
        elif floor_number == 1:
            return "Primer Piso"
        else:
            return f"Planta {int(floor_number)}"
    
    def validate_floor_range(self, floor_number: float) -> bool:
        """
        Validar que el número de planta esté en el rango permitido.
        
        Args:
            floor_number: Número de planta
            
        Returns:
            True si está en rango válido
        """
        return -100 <= floor_number <= 100
    
    def process_secondary_uses(self, secondary_uses_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Procesar usos secundarios con plantas en formato texto.
        
        Args:
            secondary_uses_data: Lista de usos secundarios con plantas en texto
            
        Returns:
            Lista procesada con plantas en formato numérico
        """
        processed_uses = []
        
        for use_data in secondary_uses_data:
            processed_use = use_data.copy()
            
            # Procesar plantas si están en formato texto
            if 'floors' in use_data and isinstance(use_data['floors'], list):
                if use_data['floors'] and isinstance(use_data['floors'][0], str):
                    # Plantas en formato texto, procesar
                    processed_floors = self.process_floor_list(use_data['floors'])
                    processed_use['floors'] = processed_floors
                else:
                    # Ya están en formato numérico, validar
                    valid_floors = [f for f in use_data['floors'] if self.validate_floor_range(f)]
                    processed_use['floors'] = valid_floors
            
            processed_uses.append(processed_use)
        
        return processed_uses
    
    def create_floor_mapping_report(self, original_data: Dict[str, Any], processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear reporte de mapeo de plantas procesadas.
        
        Args:
            original_data: Datos originales con plantas en texto
            processed_data: Datos procesados con plantas numéricas
            
        Returns:
            Reporte de mapeo
        """
        report = {
            'total_secondary_uses': len(processed_data.get('secondary_uses', [])),
            'floor_mappings': [],
            'unprocessed_floors': [],
            'validation_errors': []
        }
        
        for i, use in enumerate(processed_data.get('secondary_uses', [])):
            original_use = original_data.get('secondary_uses', [{}])[i] if i < len(original_data.get('secondary_uses', [])) else {}
            
            mapping = {
                'use_type': use.get('use_type', ''),
                'original_floors': original_use.get('floors', []),
                'processed_floors': use.get('floors', []),
                'floor_labels': [self.get_floor_label(f) for f in use.get('floors', [])]
            }
            
            report['floor_mappings'].append(mapping)
        
        return report
