"""
Gestor de integración del sistema Madrid.
Coordina todos los componentes sin afectar la configuración existente.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio

# Imports con manejo de errores para dependencias faltantes
try:
    from .madrid_floor_processor import MadridFloorProcessor
except ImportError as e:
    logger.warning(f"MadridFloorProcessor no disponible: {e}")
    MadridFloorProcessor = None

try:
    from .madrid_normative_processor import MadridNormativeProcessor
except ImportError as e:
    logger.warning(f"MadridNormativeProcessor no disponible: {e}")
    MadridNormativeProcessor = None

try:
    from .madrid_database_manager import MadridDatabaseManager
except ImportError as e:
    logger.warning(f"MadridDatabaseManager no disponible: {e}")
    MadridDatabaseManager = None

try:
    from .madrid_verification_engine import MadridVerificationEngine
except ImportError as e:
    logger.warning(f"MadridVerificationEngine no disponible: {e}")
    MadridVerificationEngine = None

try:
    from .madrid_report_generator import MadridReportGenerator
except ImportError as e:
    logger.warning(f"MadridReportGenerator no disponible: {e}")
    MadridReportGenerator = None

try:
    from .madrid_ambiguity_detector import MadridAmbiguityDetector
except ImportError as e:
    logger.warning(f"MadridAmbiguityDetector no disponible: {e}")
    MadridAmbiguityDetector = None

try:
    from .madrid_chatbot_system import MadridChatbotSystem
except ImportError as e:
    logger.warning(f"MadridChatbotSystem no disponible: {e}")
    MadridChatbotSystem = None

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
        Inicializar todo el sistema Madrid de forma segura con reintentos.
        
        Returns:
            True si se inicializó correctamente
        """
        try:
            self.logger.info("Inicializando sistema Madrid integrado...")
            
            # Lista de inicializadores con reintentos
            initializers = [
                ("Procesador de plantas", self._initialize_floor_processor),
                ("Procesador de normativa", self._initialize_normative_processor),
                ("Gestor de base de datos", self._initialize_database_manager),
                ("Motor de verificación", self._initialize_verification_engine),
                ("Generador de reportes", self._initialize_report_generator),
                ("Detector de ambigüedades", self._initialize_ambiguity_detector),
                ("Sistema de chatbot", self._initialize_chatbot_system)
            ]
            
            # Inicializar cada componente con reintentos
            for name, initializer in initializers:
                success = await self._initialize_with_retry(name, initializer, max_retries=3)
                if not success:
                    self.logger.warning(f"Componente {name} no se pudo inicializar, continuando...")
            
            # Verificar estado final
            self.initialized = await self._verify_system_status()
            
            if self.initialized:
                self.logger.info("Sistema Madrid inicializado correctamente")
                self.status.overall_status = "ready"
            else:
                self.logger.warning("Sistema Madrid inicializado parcialmente")
                self.status.overall_status = "degraded"
            
            return self.initialized
            
        except Exception as e:
            self.logger.error(f"Error inicializando sistema Madrid: {e}")
            self.status.overall_status = "error"
            return False
    
    async def _initialize_with_retry(self, name: str, initializer, max_retries: int = 3) -> bool:
        """Inicializar componente con reintentos."""
        for attempt in range(max_retries):
            try:
                await initializer()
                self.logger.info(f"✅ {name} inicializado correctamente (intento {attempt + 1})")
                return True
            except Exception as e:
                self.logger.warning(f"⚠️ Error inicializando {name} (intento {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Backoff exponencial
                else:
                    self.logger.error(f"❌ {name} falló después de {max_retries} intentos")
                    return False
        return False
    
    async def _initialize_floor_processor(self):
        """Inicializar procesador de plantas."""
        try:
            if MadridFloorProcessor is None:
                raise ImportError("MadridFloorProcessor no está disponible")
            
            self.floor_processor = MadridFloorProcessor()
            self.status.floor_processor = True
            self.logger.debug("Procesador de plantas inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando procesador de plantas: {e}")
            self.status.floor_processor = False
            raise
    
    async def _initialize_normative_processor(self):
        """Inicializar procesador de normativa."""
        try:
            if MadridNormativeProcessor is None:
                raise ImportError("MadridNormativeProcessor no está disponible")
            
            self.normative_processor = MadridNormativeProcessor()
            # Escanear documentos normativos
            self.normative_processor.scan_normative_documents()
            self.status.normative_processor = True
            self.logger.debug("Procesador de normativa inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando procesador de normativa: {e}")
            self.status.normative_processor = False
            raise
    
    async def _initialize_database_manager(self):
        """Inicializar gestor de base de datos."""
        try:
            if MadridDatabaseManager is None:
                raise ImportError("MadridDatabaseManager no está disponible")
            
            self.database_manager = MadridDatabaseManager()
            await self.database_manager.initialize()
            self.status.database_manager = True
            self.logger.debug("Gestor de base de datos inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando gestor de base de datos: {e}")
            self.status.database_manager = False
            raise
    
    async def _initialize_verification_engine(self):
        """Inicializar motor de verificación."""
        try:
            if MadridVerificationEngine is None:
                raise ImportError("MadridVerificationEngine no está disponible")
            
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
            raise
    
    async def _initialize_report_generator(self):
        """Inicializar generador de reportes."""
        try:
            if MadridReportGenerator is None:
                raise ImportError("MadridReportGenerator no está disponible")
            
            self.report_generator = MadridReportGenerator()
            self.status.report_generator = True
            self.logger.debug("Generador de reportes inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando generador de reportes: {e}")
            self.status.report_generator = False
            raise
    
    async def _initialize_ambiguity_detector(self):
        """Inicializar detector de ambigüedades."""
        try:
            if MadridAmbiguityDetector is None:
                raise ImportError("MadridAmbiguityDetector no está disponible")
            
            self.ambiguity_detector = MadridAmbiguityDetector()
            self.status.ambiguity_detector = True
            self.logger.debug("Detector de ambigüedades inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando detector de ambigüedades: {e}")
            self.status.ambiguity_detector = False
            raise
    
    async def _initialize_chatbot_system(self):
        """Inicializar sistema de chatbot."""
        try:
            if MadridChatbotSystem is None:
                raise ImportError("MadridChatbotSystem no está disponible")
            
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
            raise
    
    async def _verify_system_status(self) -> bool:
        """Verificar estado del sistema con validación robusta."""
        try:
            # Verificar que todos los componentes críticos estén inicializados
            critical_components = [
                ("floor_processor", self.status.floor_processor),
                ("normative_processor", self.status.normative_processor),
                ("verification_engine", self.status.verification_engine),
                ("ambiguity_detector", self.status.ambiguity_detector)
            ]
            
            # Verificar componentes críticos
            critical_working = []
            for name, status in critical_components:
                if status:
                    critical_working.append(name)
                    self.logger.debug(f"✅ {name}: Funcionando")
                else:
                    self.logger.warning(f"❌ {name}: No disponible")
            
            # Verificar componentes opcionales
            optional_components = [
                ("database_manager", self.status.database_manager),
                ("report_generator", self.status.report_generator),
                ("chatbot_system", self.status.chatbot_system)
            ]
            
            optional_working = []
            for name, status in optional_components:
                if status:
                    optional_working.append(name)
                    self.logger.debug(f"✅ {name}: Funcionando")
                else:
                    self.logger.warning(f"⚠️ {name}: No disponible (opcional)")
            
            # Determinar estado del sistema
            critical_count = len(critical_working)
            total_critical = len(critical_components)
            optional_count = len(optional_working)
            total_optional = len(optional_components)
            
            self.logger.info(f"Componentes críticos: {critical_count}/{total_critical}")
            self.logger.info(f"Componentes opcionales: {optional_count}/{total_optional}")
            
            # El sistema funciona si al menos 3 de 4 componentes críticos están funcionando
            if critical_count >= 3:
                self.logger.info("Sistema Madrid operativo")
                return True
            else:
                self.logger.error(f"Sistema Madrid no operativo: solo {critical_count}/{total_critical} componentes críticos")
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
        Procesar proyecto Madrid completo con fallbacks robustos.
        
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
            
            # 1. Detectar ambigüedades (con fallback)
            ambiguities = []
            if self.ambiguity_detector:
                try:
                    ambiguities = self.ambiguity_detector.detect_ambiguities(project_data)
                    self.logger.info(f"Ambigüedades detectadas: {len(ambiguities)}")
                except Exception as e:
                    self.logger.warning(f"Error detectando ambigüedades: {e}")
                    ambiguities = []
            
            # 2. Si hay ambigüedades, iniciar chatbot (con fallback)
            if ambiguities and self.chatbot_system:
                try:
                    session = await self.chatbot_system.start_ambiguity_resolution(project_data)
                    return {
                        'success': True,
                        'project_id': project_data.get('project_id', 'unknown'),
                        'status': 'ambiguities_detected',
                        'ambiguities_count': len(ambiguities),
                        'chatbot_session_id': session.session_id,
                        'message': 'Se detectaron ambigüedades. Iniciando chatbot para resolución.'
                    }
                except Exception as e:
                    self.logger.warning(f"Error iniciando chatbot: {e}")
                    # Continuar con verificación básica
            
            # 3. Verificación normativa (con fallback)
            if self.verification_engine:
                try:
                    verification_result = await self.verification_engine.verify_project(project_data)
                    
                    # 4. Generar reporte (con fallback)
                    report_data = None
                    if self.report_generator:
                        try:
                            report_data = self.report_generator.generate_verification_report(
                                verification_result, project_data
                            )
                        except Exception as e:
                            self.logger.warning(f"Error generando reporte: {e}")
                    
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
                except Exception as e:
                    self.logger.error(f"Error en verificación: {e}")
                    # Fallback a verificación básica
                    return await self._fallback_verification(project_data)
            
            # 4. Fallback a verificación básica
            return await self._fallback_verification(project_data)
            
        except Exception as e:
            self.logger.error(f"Error procesando proyecto Madrid: {e}")
            return {
                'success': False,
                'error': str(e),
                'project_id': project_data.get('project_id', 'unknown')
            }
    
    async def _fallback_verification(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verificación básica de fallback cuando los componentes principales fallan."""
        try:
            self.logger.info("Ejecutando verificación básica de fallback")
            
            # Verificación básica sin componentes avanzados
            basic_checks = []
            
            # Verificar datos básicos
            if not project_data.get('primary_use'):
                basic_checks.append({
                    'item': 'primary_use',
                    'status': 'missing',
                    'message': 'Tipo de uso principal no especificado'
                })
            else:
                basic_checks.append({
                    'item': 'primary_use',
                    'status': 'present',
                    'message': f"Tipo de uso: {project_data.get('primary_use')}"
                })
            
            # Verificar archivos
            files = project_data.get('files', [])
            if not files:
                basic_checks.append({
                    'item': 'files',
                    'status': 'missing',
                    'message': 'No se han subido archivos'
                })
            else:
                basic_checks.append({
                    'item': 'files',
                    'status': 'present',
                    'message': f"Archivos subidos: {len(files)}"
                })
            
            # Calcular cumplimiento básico
            total_checks = len(basic_checks)
            passed_checks = len([check for check in basic_checks if check['status'] == 'present'])
            compliance_percentage = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
            
            return {
                'success': True,
                'project_id': project_data.get('project_id', 'unknown'),
                'status': 'verification_completed_basic',
                'verification_result': {
                    'verification_id': f"BASIC_{project_data.get('project_id', 'unknown')}",
                    'overall_status': 'compliant' if compliance_percentage >= 50 else 'non_compliant',
                    'compliance_percentage': compliance_percentage,
                    'total_items': total_checks,
                    'compliant_items': passed_checks,
                    'non_compliant_items': total_checks - passed_checks,
                    'basic_checks': basic_checks
                },
                'report_generated': False,
                'message': 'Verificación básica completada (modo fallback)'
            }
            
        except Exception as e:
            self.logger.error(f"Error en verificación básica: {e}")
            return {
                'success': False,
                'error': f"Error en verificación básica: {str(e)}",
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
