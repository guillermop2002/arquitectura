"""
Aplicador de lógica de usos para el análisis de documentos.
Aplica el uso principal a todas las plantas excepto las que tienen uso secundario.
"""

import logging
from typing import Dict, List, Any, Set

logger = logging.getLogger(__name__)

class UsageApplicator:
    """Aplicador de lógica de usos."""
    
    def __init__(self, detailed_logger=None):
        self.detailed_logger = detailed_logger
    
    def apply_usage_logic(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aplica la lógica de usos correcta al proyecto.
        
        Lógica:
        - Uso principal se aplica a TODAS las plantas
        - EXCEPTO las plantas que tienen uso secundario
        - Las plantas con uso secundario SOLO tienen uso secundario
        
        Args:
            project_data: Datos del proyecto
            
        Returns:
            Datos del proyecto con usos aplicados correctamente
        """
        logger.info("Aplicando lógica de usos...")
        
        primary_use = project_data.get('primary_use')
        secondary_uses = project_data.get('secondary_uses', {})
        
        if not primary_use:
            logger.warning("No hay uso principal definido")
            return project_data
        
        # Obtener todas las plantas del proyecto
        all_floors = self._get_all_floors(project_data)
        logger.info(f"Plantas identificadas: {all_floors}")
        
        # Plantas con uso secundario
        floors_with_secondary = set()
        for use_type, use_data in secondary_uses.items():
            if use_data and 'floors' in use_data:
                floors_with_secondary.update(use_data['floors'])
                logger.info(f"Uso secundario '{use_type}' en plantas: {use_data['floors']}")
        
        # Aplicar lógica de usos
        applied_uses = {}
        
        for floor in all_floors:
            if floor in floors_with_secondary:
                # Planta con uso secundario - SOLO uso secundario
                secondary_use_for_floor = self._get_secondary_use_for_floor(floor, secondary_uses)
                applied_uses[floor] = {
                    'use_type': 'secondary',
                    'use_name': secondary_use_for_floor,
                    'applied_logic': 'secondary_only'
                }
                
                if self.detailed_logger:
                    self.detailed_logger.log_usage_application(
                        floor, primary_use, secondary_use_for_floor, secondary_use_for_floor
                    )
                    
            else:
                # Planta sin uso secundario - SOLO uso principal
                applied_uses[floor] = {
                    'use_type': 'primary',
                    'use_name': primary_use,
                    'applied_logic': 'primary_only'
                }
                
                if self.detailed_logger:
                    self.detailed_logger.log_usage_application(
                        floor, primary_use, None, primary_use
                    )
        
        # Actualizar datos del proyecto
        project_data['applied_uses'] = applied_uses
        project_data['usage_logic_applied'] = True
        
        logger.info(f"Lógica de usos aplicada: {len(applied_uses)} plantas procesadas")
        
        return project_data
    
    def _get_all_floors(self, project_data: Dict[str, Any]) -> List[str]:
        """Obtiene todas las plantas del proyecto."""
        floors = set()
        
        # Buscar plantas en usos secundarios
        secondary_uses = project_data.get('secondary_uses', {})
        for use_type, use_data in secondary_uses.items():
            if use_data and 'floors' in use_data:
                floors.update(use_data['floors'])
        
        # Si no hay plantas en usos secundarios, generar plantas por defecto
        if not floors:
            floors = self._generate_default_floors()
            logger.info(f"No se encontraron plantas en usos secundarios, usando plantas por defecto: {floors}")
        
        return sorted(list(floors))
    
    def _generate_default_floors(self) -> Set[str]:
        """Genera plantas por defecto si no se especifican."""
        return {
            'Planta Baja', 'Primera Planta', 'Segunda Planta', 
            'Tercera Planta', 'Cuarta Planta', 'Quinta Planta'
        }
    
    def _get_secondary_use_for_floor(self, floor: str, secondary_uses: Dict[str, Any]) -> str:
        """Obtiene el uso secundario para una planta específica."""
        for use_type, use_data in secondary_uses.items():
            if use_data and 'floors' in use_data and floor in use_data['floors']:
                return use_type
        return 'unknown'
    
    def validate_usage_logic(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida que la lógica de usos esté correctamente aplicada.
        
        Args:
            project_data: Datos del proyecto
            
        Returns:
            Resultado de la validación
        """
        logger.info("Validando lógica de usos...")
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'applied_uses': project_data.get('applied_uses', {}),
            'summary': {}
        }
        
        applied_uses = project_data.get('applied_uses', {})
        if not applied_uses:
            validation_result['errors'].append("No se han aplicado usos al proyecto")
            validation_result['is_valid'] = False
            return validation_result
        
        # Contar usos aplicados
        primary_count = 0
        secondary_count = 0
        
        for floor, use_info in applied_uses.items():
            if use_info['use_type'] == 'primary':
                primary_count += 1
            elif use_info['use_type'] == 'secondary':
                secondary_count += 1
        
        validation_result['summary'] = {
            'total_floors': len(applied_uses),
            'primary_use_floors': primary_count,
            'secondary_use_floors': secondary_count
        }
        
        # Validaciones
        if primary_count == 0:
            validation_result['warnings'].append("No hay plantas con uso principal")
        
        if secondary_count == 0:
            validation_result['warnings'].append("No hay plantas con uso secundario")
        
        logger.info(f"Validación completada: {validation_result['summary']}")
        
        return validation_result
    
    def get_usage_summary(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene un resumen de los usos aplicados.
        
        Args:
            project_data: Datos del proyecto
            
        Returns:
            Resumen de usos
        """
        applied_uses = project_data.get('applied_uses', {})
        
        summary = {
            'total_floors': len(applied_uses),
            'usage_distribution': {},
            'floor_details': {}
        }
        
        # Distribución de usos
        for floor, use_info in applied_uses.items():
            use_name = use_info['use_name']
            if use_name not in summary['usage_distribution']:
                summary['usage_distribution'][use_name] = 0
            summary['usage_distribution'][use_name] += 1
            
            summary['floor_details'][floor] = use_info
        
        return summary
