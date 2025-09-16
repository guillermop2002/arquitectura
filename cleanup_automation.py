#!/usr/bin/env python3
"""
Script de limpieza automática para el sistema de verificación arquitectónica.
Se ejecuta periódicamente para mantener el sistema optimizado.
"""

import os
import sys
import time
import logging
import schedule
from pathlib import Path
from datetime import datetime, timedelta

# Añadir el directorio raíz al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.app.core.cleanup_manager import CleanupManager
from backend.app.core.config import get_config
from backend.app.core.logging_config import get_logger

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/cleanup_automation.log'),
        logging.StreamHandler()
    ]
)
logger = get_logger(__name__)

class CleanupAutomation:
    """Automatización de limpieza del sistema."""
    
    def __init__(self):
        self.cleanup_manager = CleanupManager()
        self.config = get_config()
        self.running = False
        
        # Configuración de limpieza automática
        self.cleanup_schedule = {
            'every_hour': True,  # Limpieza cada hora
            'every_6_hours': True,  # Limpieza cada 6 horas
            'daily': True,  # Limpieza diaria
            'weekly': True  # Limpieza semanal
        }
        
        logger.info("CleanupAutomation initialized")
    
    def setup_schedule(self):
        """Configurar horarios de limpieza."""
        try:
            # Limpieza cada hora (datos temporales)
            if self.cleanup_schedule['every_hour']:
                schedule.every().hour.do(self.hourly_cleanup)
                logger.info("✅ Limpieza cada hora configurada")
            
            # Limpieza cada 6 horas (cache y archivos temp)
            if self.cleanup_schedule['every_6_hours']:
                schedule.every(6).hours.do(self.periodic_cleanup)
                logger.info("✅ Limpieza cada 6 horas configurada")
            
            # Limpieza diaria (proyectos antiguos)
            if self.cleanup_schedule['daily']:
                schedule.every().day.at("02:00").do(self.daily_cleanup)
                logger.info("✅ Limpieza diaria configurada (02:00)")
            
            # Limpieza semanal (limpieza completa)
            if self.cleanup_schedule['weekly']:
                schedule.every().sunday.at("03:00").do(self.weekly_cleanup)
                logger.info("✅ Limpieza semanal configurada (Domingo 03:00)")
            
            logger.info("📅 Horarios de limpieza configurados correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error configurando horarios: {e}")
    
    def hourly_cleanup(self):
        """Limpieza cada hora - archivos temporales."""
        try:
            logger.info("🕐 Iniciando limpieza cada hora")
            
            # Limpiar archivos temporales antiguos
            result = self.cleanup_manager._cleanup_old_temp_files()
            
            if result['success']:
                logger.info(f"✅ Limpieza cada hora completada: {result['files_deleted']} archivos, {result['space_freed_mb']:.2f}MB")
            else:
                logger.warning(f"⚠️ Limpieza cada hora con errores: {result.get('error', 'Error desconocido')}")
            
        except Exception as e:
            logger.error(f"❌ Error en limpieza cada hora: {e}")
    
    def periodic_cleanup(self):
        """Limpieza cada 6 horas - cache y datos intermedios."""
        try:
            logger.info("🕕 Iniciando limpieza cada 6 horas")
            
            # Limpiar cache antiguo
            cache_result = self.cleanup_manager._cleanup_old_cache()
            
            # Limpiar archivos temporales
            temp_result = self.cleanup_manager._cleanup_old_temp_files()
            
            total_space_freed = cache_result.get('space_freed_mb', 0) + temp_result.get('space_freed_mb', 0)
            total_files_deleted = cache_result.get('files_deleted', 0) + temp_result.get('files_deleted', 0)
            
            logger.info(f"✅ Limpieza cada 6 horas completada: {total_files_deleted} archivos, {total_space_freed:.2f}MB")
            
        except Exception as e:
            logger.error(f"❌ Error en limpieza cada 6 horas: {e}")
    
    def daily_cleanup(self):
        """Limpieza diaria - proyectos antiguos."""
        try:
            logger.info("🌅 Iniciando limpieza diaria")
            
            # Limpiar datos antiguos
            result = self.cleanup_manager.cleanup_old_data(force=False)
            
            if result['projects_deleted'] > 0 or result['space_freed_mb'] > 0:
                logger.info(f"✅ Limpieza diaria completada: {result['projects_deleted']} proyectos, {result['space_freed_mb']:.2f}MB")
            else:
                logger.info("✅ Limpieza diaria completada: No hay datos antiguos para limpiar")
            
        except Exception as e:
            logger.error(f"❌ Error en limpieza diaria: {e}")
    
    def weekly_cleanup(self):
        """Limpieza semanal - limpieza completa."""
        try:
            logger.info("📅 Iniciando limpieza semanal")
            
            # Obtener estado antes de la limpieza
            status_before = self.cleanup_manager.get_cleanup_status()
            
            # Limpieza completa
            result = self.cleanup_manager.force_cleanup_all()
            
            # Obtener estado después de la limpieza
            status_after = self.cleanup_manager.get_cleanup_status()
            
            logger.info(f"✅ Limpieza semanal completada:")
            logger.info(f"   - Proyectos eliminados: {result['projects_deleted']}")
            logger.info(f"   - Espacio liberado: {result['space_freed_mb']:.2f}MB")
            logger.info(f"   - Neo4j limpio: {result['neo4j_cleaned']}")
            logger.info(f"   - Cache limpio: {result['cache_cleaned']}")
            logger.info(f"   - Archivos temp limpios: {result['temp_files_cleaned']}")
            
        except Exception as e:
            logger.error(f"❌ Error en limpieza semanal: {e}")
    
    def run_cleanup_now(self, cleanup_type: str = "all"):
        """Ejecutar limpieza inmediatamente."""
        try:
            logger.info(f"🚀 Ejecutando limpieza inmediata: {cleanup_type}")
            
            if cleanup_type == "hourly":
                self.hourly_cleanup()
            elif cleanup_type == "periodic":
                self.periodic_cleanup()
            elif cleanup_type == "daily":
                self.daily_cleanup()
            elif cleanup_type == "weekly":
                self.weekly_cleanup()
            elif cleanup_type == "all":
                self.weekly_cleanup()
            else:
                logger.error(f"❌ Tipo de limpieza no válido: {cleanup_type}")
                return False
            
            logger.info("✅ Limpieza inmediata completada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en limpieza inmediata: {e}")
            return False
    
    def get_status(self):
        """Obtener estado del sistema de limpieza."""
        try:
            status = self.cleanup_manager.get_cleanup_status()
            
            logger.info("📊 ESTADO DEL SISTEMA DE LIMPIEZA")
            logger.info(f"   - Última limpieza: {status.get('last_cleanup', 'Nunca')}")
            logger.info(f"   - Próxima limpieza: {status.get('next_cleanup_due', 'N/A')}")
            logger.info(f"   - Total de limpiezas: {status['cleanup_metrics']['total_cleanups']}")
            logger.info(f"   - Proyectos eliminados: {status['cleanup_metrics']['projects_deleted']}")
            logger.info(f"   - Espacio liberado: {status['cleanup_metrics']['space_freed_mb']:.2f}MB")
            
            # Estadísticas de Neo4j
            neo4j_stats = status.get('neo4j_stats', {})
            if neo4j_stats.get('connected'):
                logger.info(f"   - Neo4j proyectos: {neo4j_stats.get('project_count', 0)}")
                logger.info(f"   - Neo4j nodos: {neo4j_stats.get('total_nodes', 0)}")
                logger.info(f"   - Neo4j relaciones: {neo4j_stats.get('total_relationships', 0)}")
                logger.info(f"   - Neo4j tamaño estimado: {neo4j_stats.get('estimated_size_mb', 0):.2f}MB")
            
            # Estadísticas de cache
            cache_stats = status.get('cache_stats', {})
            if cache_stats.get('exists'):
                logger.info(f"   - Cache archivos: {cache_stats.get('file_count', 0)}")
                logger.info(f"   - Cache tamaño: {cache_stats.get('size_mb', 0):.2f}MB")
            
            # Estadísticas de archivos temp
            temp_stats = status.get('temp_stats', {})
            if temp_stats.get('exists'):
                logger.info(f"   - Temp archivos: {temp_stats.get('file_count', 0)}")
                logger.info(f"   - Temp tamaño: {temp_stats.get('size_mb', 0):.2f}MB")
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado: {e}")
            return None
    
    def run_scheduler(self):
        """Ejecutar el programador de limpieza."""
        try:
            logger.info("🚀 Iniciando programador de limpieza automática")
            self.running = True
            
            # Configurar horarios
            self.setup_schedule()
            
            # Mostrar estado inicial
            self.get_status()
            
            logger.info("⏰ Programador de limpieza ejecutándose...")
            logger.info("   Presiona Ctrl+C para detener")
            
            # Ejecutar programador
            while self.running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # Verificar cada minuto
                except KeyboardInterrupt:
                    logger.info("🛑 Deteniendo programador de limpieza...")
                    self.running = False
                    break
                except Exception as e:
                    logger.error(f"❌ Error en programador: {e}")
                    time.sleep(60)  # Esperar antes de reintentar
            
            logger.info("✅ Programador de limpieza detenido")
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando programador: {e}")

def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sistema de limpieza automática')
    parser.add_argument('--type', choices=['hourly', 'periodic', 'daily', 'weekly', 'all'], 
                       default='all', help='Tipo de limpieza a ejecutar')
    parser.add_argument('--now', action='store_true', help='Ejecutar limpieza inmediatamente')
    parser.add_argument('--status', action='store_true', help='Mostrar estado del sistema')
    parser.add_argument('--schedule', action='store_true', help='Ejecutar programador automático')
    
    args = parser.parse_args()
    
    # Crear directorio de logs si no existe
    os.makedirs('logs', exist_ok=True)
    
    automation = CleanupAutomation()
    
    if args.status:
        automation.get_status()
    elif args.now:
        automation.run_cleanup_now(args.type)
    elif args.schedule:
        automation.run_scheduler()
    else:
        # Por defecto, ejecutar limpieza inmediata
        automation.run_cleanup_now(args.type)

if __name__ == "__main__":
    main()
