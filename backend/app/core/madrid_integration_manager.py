"""
Gestor de integración del sistema Madrid.
Coordina todos los componentes sin afectar la configuración existente.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio

from .madrid_floor_processor import MadridFloorProcessor
from .madrid_normative_processor import MadridNormativeProcessor
from .madrid_database_manager import MadridDatabaseManager
from .madrid_verification_engine import MadridVerificationEngine
from .madrid_report_generator import MadridReportGenerator
from .madrid_ambiguity_detector import MadridAmbiguityDetector
from .madrid_chatbot_system import MadridChatbotSystem

logger = logging.getLogger(__name__)

@dataclass
class MadridSystemStatus:
    """Estado del sistema Madrid integrado."""
    floor_processor: bool = False
    normative_processor: bool = False
    database_manager: bool = False
    verification_engine: bool = False
    report_generator: bool = False
    ambiguity_detector: bool = False
    chatbot_system: bool = False
    overall_status: str = "initializing"
    last_check: str = field(default_factory=lambda: datetime.now().isoformat())

class MadridIntegrationManager:
    """Gestor de integración del sistema Madrid."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MadridIntegrationManager")
        
        # Componentes del sistema Madrid
        self.floor_processor = None
        self.normative_processor = None
        self.database_manager = None
        self.verification_engine = None
        self.report_generator = None
        self.ambiguity_detector = None
        self.chatbot_system = None
        
        # Estado del sistema
        self.status = MadridSystemStatus()
        self.initialized = False
    
    async def initialize_system(self) -> bool:
        """
        Inicializar todo el sistema Madrid de forma segura.
        
        Returns:
            True si se inicializó correctamente
        """
        try:
            self.logger.info("Inicializando sistema Madrid integrado...")
            
            # 1. Inicializar procesador de plantas
            await self._initialize_floor_processor()
            
            # 2. Inicializar procesador de normativa
            await self._initialize_normative_processor()
            
            # 3. Inicializar gestor de base de datos
            await self._initialize_database_manager()
            
            # 4. Inicializar motor de verificación
            await self._initialize_verification_engine()
            
            # 5. Inicializar generador de reportes
            await self._initialize_report_generator()
            
            # 6. Inicializar detector de ambigüedades
            await self._initialize_ambiguity_detector()
            
            # 7. Inicializar sistema de chatbot
            await self._initialize_chatbot_system()
            
            # Verificar estado final
            self.initialized = await self._verify_system_status()
            
            if self.initialized:
                self.logger.info("Sistema Madrid inicializado correctamente")
                self.status.overall_status = "ready"
            else:
                self.logger.error("Error en la inicialización del sistema Madrid")
                self.status.overall_status = "error"
            
            return self.initialized
            
        except Exception as e:
            self.logger.error(f"Error inicializando sistema Madrid: {e}")
            self.status.overall_status = "error"
            return False
    
    async def _initialize_floor_processor(self):
        """Inicializar procesador de plantas."""
        try:
            self.floor_processor = MadridFloorProcessor()
            self.status.floor_processor = True
            self.logger.debug("Procesador de plantas inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando procesador de plantas: {e}")
            self.status.floor_processor = False
    
    async def _initialize_normative_processor(self):
        """Inicializar procesador de normativa."""
        try:
            self.normative_processor = MadridNormativeProcessor()
            # Escanear documentos normativos
            self.normative_processor.scan_normative_documents()
            self.status.normative_processor = True
            self.logger.debug("Procesador de normativa inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando procesador de normativa: {e}")
            self.status.normative_processor = False
    
    async def _initialize_database_manager(self):
        """Inicializar gestor de base de datos."""
        try:
            self.database_manager = MadridDatabaseManager()
            await self.database_manager.initialize()
            self.status.database_manager = True
            self.logger.debug("Gestor de base de datos inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando gestor de base de datos: {e}")
            self.status.database_manager = False
    
    async def _initialize_verification_engine(self):
        """Inicializar motor de verificación."""
        try:
            self.verification_engine = MadridVerificationEngine(
                floor_processor=self.floor_processor,
                normative_processor=self.normative_processor,
                db_manager=self.database_manager
            )
            self.status.verification_engine = True
            self.logger.debug("Motor de verificación inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando motor de verificación: {e}")
            self.status.verification_engine = False
    
    async def _initialize_report_generator(self):
        """Inicializar generador de reportes."""
        try:
            self.report_generator = MadridReportGenerator()
            self.status.report_generator = True
            self.logger.debug("Generador de reportes inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando generador de reportes: {e}")
            self.status.report_generator = False
    
    async def _initialize_ambiguity_detector(self):
        """Inicializar detector de ambigüedades."""
        try:
            self.ambiguity_detector = MadridAmbiguityDetector()
            self.status.ambiguity_detector = True
            self.logger.debug("Detector de ambigüedades inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando detector de ambigüedades: {e}")
            self.status.ambiguity_detector = False
    
    async def _initialize_chatbot_system(self):
        """Inicializar sistema de chatbot."""
        try:
            self.chatbot_system = MadridChatbotSystem(
                ambiguity_detector=self.ambiguity_detector,
                verification_engine=self.verification_engine,
                floor_processor=self.floor_processor,
                normative_processor=self.normative_processor
            )
            self.status.chatbot_system = True
            self.logger.debug("Sistema de chatbot inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando sistema de chatbot: {e}")
            self.status.chatbot_system = False
    
    async def _verify_system_status(self) -> bool:
        """Verificar estado del sistema."""
        try:
            # Verificar que todos los componentes críticos estén inicializados
            critical_components = [
                self.status.floor_processor,
                self.status.normative_processor,
                self.status.verification_engine,
                self.status.ambiguity_detector
            ]
            
            all_critical = all(critical_components)
            
            if all_critical:
                self.logger.info("Todos los componentes críticos están funcionando")
                return True
            else:
                self.logger.warning("Algunos componentes críticos no están funcionando")
                return False
                
        except Exception as e:
            self.logger.error(f"Error verificando estado del sistema: {e}")
            return False
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado actual del sistema."""
        self.status.last_check = datetime.now().isoformat()
        
        return {
            'overall_status': self.status.overall_status,
            'initialized': self.initialized,
            'components': {
                'floor_processor': self.status.floor_processor,
                'normative_processor': self.status.normative_processor,
                'database_manager': self.status.database_manager,
                'verification_engine': self.status.verification_engine,
                'report_generator': self.status.report_generator,
                'ambiguity_detector': self.status.ambiguity_detector,
                'chatbot_system': self.status.chatbot_system
            },
            'last_check': self.status.last_check
        }
    
    async def process_madrid_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesar proyecto Madrid completo.
        
        Args:
            project_data: Datos del proyecto Madrid
            
        Returns:
            Resultado del procesamiento completo
        """
        try:
            if not self.initialized:
                await self.initialize_system()
            
            if not self.initialized:
                return {
                    'success': False,
                    'error': 'Sistema Madrid no inicializado',
                    'project_id': project_data.get('project_id', 'unknown')
                }
            
            self.logger.info(f"Procesando proyecto Madrid: {project_data.get('project_id', 'unknown')}")
            
            # 1. Detectar ambigüedades
            ambiguities = []
            if self.ambiguity_detector:
                ambiguities = self.ambiguity_detector.detect_ambiguities(project_data)
            
            # 2. Si hay ambigüedades, iniciar chatbot
            if ambiguities and self.chatbot_system:
                session = await self.chatbot_system.start_ambiguity_resolution(project_data)
                return {
                    'success': True,
                    'project_id': project_data.get('project_id', 'unknown'),
                    'status': 'ambiguities_detected',
                    'ambiguities_count': len(ambiguities),
                    'chatbot_session_id': session.session_id,
                    'message': 'Se detectaron ambigüedades. Iniciando chatbot para resolución.'
                }
            
            # 3. Si no hay ambigüedades, proceder con verificación
            if self.verification_engine:
                verification_result = await self.verification_engine.verify_project(project_data)
                
                # 4. Generar reporte
                report_data = None
                if self.report_generator:
                    report_data = self.report_generator.generate_verification_report(
                        verification_result, project_data
                    )
                
                return {
                    'success': True,
                    'project_id': project_data.get('project_id', 'unknown'),
                    'status': 'verification_completed',
                    'verification_result': {
                        'verification_id': verification_result.verification_id,
                        'overall_status': verification_result.overall_status.value,
                        'compliance_percentage': verification_result.compliance_percentage,
                        'total_items': verification_result.total_items,
                        'compliant_items': verification_result.compliant_items,
                        'non_compliant_items': verification_result.non_compliant_items
                    },
                    'report_generated': report_data is not None,
                    'message': 'Verificación completada exitosamente'
                }
            
            return {
                'success': False,
                'error': 'Motor de verificación no disponible',
                'project_id': project_data.get('project_id', 'unknown')
            }
            
        except Exception as e:
            self.logger.error(f"Error procesando proyecto Madrid: {e}")
            return {
                'success': False,
                'error': str(e),
                'project_id': project_data.get('project_id', 'unknown')
            }
    
    async def cleanup(self):
        """Limpiar recursos del sistema."""
        try:
            if self.database_manager:
                await self.database_manager.close()
            
            self.logger.info("Sistema Madrid limpiado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error limpiando sistema Madrid: {e}")

# Instancia global del gestor de integración
madrid_integration_manager = MadridIntegrationManager()
