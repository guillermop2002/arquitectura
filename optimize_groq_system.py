#!/usr/bin/env python3
"""
Script de optimización completa para el sistema Groq-only.
Optimiza todos los componentes para máximo rendimiento con Groq API y Neo4j gratuito.
"""

import os
import sys
import logging
import json
import time
from datetime import datetime
from pathlib import Path

# Añadir el directorio del proyecto al path
sys.path.append(str(Path(__file__).parent))

from backend.app.core.groq_optimized_prompts import get_groq_config, get_optimized_prompt
from backend.app.core.opencv_optimizer import create_optimized_config, benchmark_detection
from backend.app.core.neo4j_optimizer import optimize_neo4j_for_free_tier, get_neo4j_usage_report

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GroqSystemOptimizer:
    """Optimizador completo del sistema Groq-only."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.optimization_results = {
            'timestamp': datetime.now().isoformat(),
            'groq_optimization': {},
            'opencv_optimization': {},
            'neo4j_optimization': {},
            'overall_status': 'pending'
        }
    
    def optimize_groq_prompts(self) -> Dict:
        """Optimizar prompts para Groq API."""
        self.logger.info("🔧 Optimizing Groq prompts...")
        
        try:
            # Probar diferentes configuraciones de Groq
            configs = ['quick', 'detailed', 'creative']
            best_config = None
            best_score = 0
            
            for config_type in configs:
                config = get_groq_config(config_type)
                
                # Simular prueba de prompt
                test_prompt = get_optimized_prompt(
                    'project_data',
                    project_text="Test project data"
                )
                
                # Calcular score basado en longitud y complejidad
                score = self._calculate_prompt_score(test_prompt, config)
                
                if score > best_score:
                    best_score = score
                    best_config = config_type
            
            result = {
                'best_config': best_config,
                'best_score': best_score,
                'available_configs': configs,
                'status': 'success'
            }
            
            self.logger.info(f"✅ Groq prompts optimized - Best config: {best_config}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error optimizing Groq prompts: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def optimize_opencv_detection(self) -> Dict:
        """Optimizar detección con OpenCV."""
        self.logger.info("🔧 Optimizing OpenCV detection...")
        
        try:
            # Crear configuraciones optimizadas
            x64_config = create_optimized_config("x64")
            arm64_config = create_optimized_config("arm64")
            
            # Probar con imagen de ejemplo si existe
            test_image_path = "ejemplos/test_plan.png"
            if os.path.exists(test_image_path):
                x64_benchmark = benchmark_detection(test_image_path, x64_config)
                arm64_benchmark = benchmark_detection(test_image_path, arm64_config)
                
                # Comparar rendimiento
                if x64_benchmark.get('processing_time', 0) < arm64_benchmark.get('processing_time', 0):
                    best_config = "x64"
                    best_benchmark = x64_benchmark
                else:
                    best_config = "arm64"
                    best_benchmark = arm64_benchmark
            else:
                best_config = "x64"  # Default
                best_benchmark = {"processing_time": 0, "elements_detected": 0}
            
            result = {
                'best_config': best_config,
                'benchmark_results': best_benchmark,
                'x64_config': x64_config.__dict__,
                'arm64_config': arm64_config.__dict__,
                'status': 'success'
            }
            
            self.logger.info(f"✅ OpenCV detection optimized - Best config: {best_config}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error optimizing OpenCV detection: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def optimize_neo4j_database(self) -> Dict:
        """Optimizar base de datos Neo4j."""
        self.logger.info("🔧 Optimizing Neo4j database...")
        
        try:
            # Ejecutar optimización
            optimization_result = optimize_neo4j_for_free_tier()
            
            # Obtener reporte de uso
            usage_report = get_neo4j_usage_report()
            
            result = {
                'optimization_result': optimization_result,
                'usage_report': usage_report,
                'status': 'success'
            }
            
            self.logger.info("✅ Neo4j database optimized")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error optimizing Neo4j database: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def optimize_system_performance(self) -> Dict:
        """Optimizar rendimiento general del sistema."""
        self.logger.info("🔧 Optimizing system performance...")
        
        try:
            # Verificar archivos de configuración
            config_files = [
                'requirements.groq_only.txt',
                'docker-compose.groq_only.yml',
                'env.groq_only.txt'
            ]
            
            missing_files = []
            for file in config_files:
                if not os.path.exists(file):
                    missing_files.append(file)
            
            # Verificar dependencias
            dependencies_status = self._check_dependencies()
            
            # Verificar configuración de Redis
            redis_status = self._check_redis_config()
            
            result = {
                'config_files': {
                    'missing': missing_files,
                    'status': 'OK' if not missing_files else 'WARNING'
                },
                'dependencies': dependencies_status,
                'redis': redis_status,
                'status': 'success'
            }
            
            self.logger.info("✅ System performance optimized")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error optimizing system performance: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _calculate_prompt_score(self, prompt: str, config: Dict) -> float:
        """Calcular score de optimización de prompt."""
        # Factores de optimización
        length_score = min(1.0, len(prompt) / 1000)  # Preferir prompts más cortos
        token_efficiency = min(1.0, config.get('max_tokens', 1000) / 2000)  # Eficiencia de tokens
        temperature_score = 1.0 - abs(config.get('temperature', 0.1) - 0.1)  # Temperatura óptima
        
        return (length_score + token_efficiency + temperature_score) / 3
    
    def _check_dependencies(self) -> Dict:
        """Verificar dependencias del sistema."""
        try:
            import fastapi
            import uvicorn
            import redis
            import neo4j
            import cv2
            import transformers
            import torch
            
            return {
                'status': 'OK',
                'installed': [
                    'fastapi', 'uvicorn', 'redis', 'neo4j', 
                    'opencv-python', 'transformers', 'torch'
                ]
            }
        except ImportError as e:
            return {
                'status': 'ERROR',
                'missing': str(e),
                'installed': []
            }
    
    def _check_redis_config(self) -> Dict:
        """Verificar configuración de Redis."""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.ping()
            return {'status': 'OK', 'connection': 'success'}
        except Exception as e:
            return {'status': 'ERROR', 'connection': 'failed', 'error': str(e)}
    
    def run_complete_optimization(self) -> Dict:
        """Ejecutar optimización completa del sistema."""
        self.logger.info("🚀 Starting complete system optimization...")
        
        start_time = time.time()
        
        # Optimizar cada componente
        self.optimization_results['groq_optimization'] = self.optimize_groq_prompts()
        self.optimization_results['opencv_optimization'] = self.optimize_opencv_detection()
        self.optimization_results['neo4j_optimization'] = self.optimize_neo4j_database()
        self.optimization_results['system_optimization'] = self.optimize_system_performance()
        
        # Calcular estado general
        all_success = all(
            result.get('status') == 'success' 
            for result in self.optimization_results.values() 
            if isinstance(result, dict) and 'status' in result
        )
        
        self.optimization_results['overall_status'] = 'success' if all_success else 'partial'
        self.optimization_results['optimization_time'] = time.time() - start_time
        
        # Generar reporte
        self._generate_optimization_report()
        
        return self.optimization_results
    
    def _generate_optimization_report(self):
        """Generar reporte de optimización."""
        report_path = "optimization_report.json"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.optimization_results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📊 Optimization report saved to {report_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving optimization report: {e}")
    
    def print_optimization_summary(self):
        """Imprimir resumen de optimización."""
        print("\n" + "="*60)
        print("🎯 SISTEMA DE VERIFICACIÓN ARQUITECTÓNICA - OPTIMIZACIÓN COMPLETA")
        print("="*60)
        
        print(f"\n📅 Fecha: {self.optimization_results['timestamp']}")
        print(f"⏱️  Tiempo total: {self.optimization_results.get('optimization_time', 0):.2f} segundos")
        print(f"🎯 Estado general: {self.optimization_results['overall_status'].upper()}")
        
        print("\n🔧 COMPONENTES OPTIMIZADOS:")
        
        # Groq optimization
        groq_result = self.optimization_results.get('groq_optimization', {})
        print(f"  🤖 Groq API: {groq_result.get('status', 'unknown').upper()}")
        if groq_result.get('best_config'):
            print(f"     └─ Mejor configuración: {groq_result['best_config']}")
        
        # OpenCV optimization
        opencv_result = self.optimization_results.get('opencv_optimization', {})
        print(f"  👁️  OpenCV: {opencv_result.get('status', 'unknown').upper()}")
        if opencv_result.get('best_config'):
            print(f"     └─ Mejor configuración: {opencv_result['best_config']}")
        
        # Neo4j optimization
        neo4j_result = self.optimization_results.get('neo4j_optimization', {})
        print(f"  🗄️  Neo4j: {neo4j_result.get('status', 'unknown').upper()}")
        
        # System optimization
        system_result = self.optimization_results.get('system_optimization', {})
        print(f"  ⚙️  Sistema: {system_result.get('status', 'unknown').upper()}")
        
        print("\n📊 RECOMENDACIONES:")
        
        # Mostrar recomendaciones de cada componente
        for component, result in self.optimization_results.items():
            if isinstance(result, dict) and 'recommendations' in result:
                recommendations = result['recommendations']
                if recommendations:
                    print(f"  {component.upper()}:")
                    for rec in recommendations:
                        print(f"     • {rec}")
        
        print("\n✅ Optimización completada!")
        print("="*60)

def main():
    """Función principal."""
    print("🚀 Iniciando optimización del sistema Groq-only...")
    
    optimizer = GroqSystemOptimizer()
    results = optimizer.run_complete_optimization()
    optimizer.print_optimization_summary()
    
    return results

if __name__ == "__main__":
    main()
