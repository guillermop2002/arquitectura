#!/usr/bin/env python3
"""
Validador de configuración para el sistema Groq-only.
Verifica que todos los archivos de configuración estén correctos.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GroqConfigValidator:
    """Validador de configuración para el sistema Groq-only."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_results = {
            'timestamp': None,
            'files_checked': {},
            'configurations_valid': {},
            'recommendations': [],
            'overall_status': 'pending'
        }
    
    def validate_file_structure(self) -> Dict:
        """Validar estructura de archivos del proyecto."""
        self.logger.info("🔍 Validating file structure...")
        
        required_files = {
            'core_files': [
                'main.py',
                'requirements.groq_only.txt',
                'docker-compose.groq_only.yml',
                'env.groq_only.txt'
            ],
            'backend_files': [
                'backend/app/core/ai_client.py',
                'backend/app/core/groq_optimized_prompts.py',
                'backend/app/core/opencv_optimizer.py',
                'backend/app/core/neo4j_optimizer.py',
                'backend/app/core/advanced_plan_analyzer.py'
            ],
            'backup_files': [
                'backup_paid_services/README_PAID_SERVICES.md',
                'backup_paid_services/restoration_guide.md'
            ],
            'test_files': [
                'test_groq_system_complete.py',
                'optimize_groq_system.py'
            ]
        }
        
        results = {}
        missing_files = []
        
        for category, files in required_files.items():
            category_results = {}
            for file_path in files:
                exists = os.path.exists(file_path)
                category_results[file_path] = exists
                if not exists:
                    missing_files.append(file_path)
            results[category] = category_results
        
        result = {
            'file_structure': results,
            'missing_files': missing_files,
            'status': 'success' if not missing_files else 'warning'
        }
        
        self.logger.info(f"✅ File structure validated - Missing: {len(missing_files)}")
        return result
    
    def validate_groq_only_files(self) -> Dict:
        """Validar archivos específicos de Groq-only."""
        self.logger.info("🔍 Validating Groq-only files...")
        
        results = {}
        
        # Validar requirements.groq_only.txt
        try:
            with open('requirements.groq_only.txt', 'r') as f:
                content = f.read()
            
            # Verificar que no hay dependencias de APIs pagas
            has_openai = 'openai==' in content and not content.strip().startswith('#')
            has_google = 'google-cloud-storage==' in content and not content.strip().startswith('#')
            
            results['requirements.groq_only.txt'] = {
                'exists': True,
                'no_openai': not has_openai,
                'no_google': not has_google,
                'groq_ready': not has_openai and not has_google
            }
        except Exception as e:
            results['requirements.groq_only.txt'] = {
                'exists': False,
                'error': str(e)
            }
        
        # Validar docker-compose.groq_only.yml
        try:
            with open('docker-compose.groq_only.yml', 'r') as f:
                content = f.read()
            
            # Verificar que solo tiene variables de Groq
            has_openai_env = 'OPENAI_API_KEY' in content
            has_google_env = 'GOOGLE_VISION_API_KEY' in content
            has_groq_env = 'GROQ_API_KEY' in content
            
            results['docker-compose.groq_only.yml'] = {
                'exists': True,
                'no_openai_env': not has_openai_env,
                'no_google_env': not has_google_env,
                'has_groq_env': has_groq_env,
                'groq_ready': not has_openai_env and not has_google_env and has_groq_env
            }
        except Exception as e:
            results['docker-compose.groq_only.yml'] = {
                'exists': False,
                'error': str(e)
            }
        
        # Validar env.groq_only.txt
        try:
            with open('env.groq_only.txt', 'r') as f:
                content = f.read()
            
            # Verificar configuración
            has_groq_key = 'GROQ_API_KEY=' in content
            has_openai_commented = '# OPENAI_API_KEY=' in content
            has_google_commented = '# GOOGLE_VISION_API_KEY=' in content
            has_neo4j_config = 'NEO4J_URI=' in content
            
            results['env.groq_only.txt'] = {
                'exists': True,
                'has_groq_key': has_groq_key,
                'openai_commented': has_openai_commented,
                'google_commented': has_google_commented,
                'has_neo4j': has_neo4j_config,
                'groq_ready': has_groq_key and has_openai_commented and has_google_commented and has_neo4j_config
            }
        except Exception as e:
            results['env.groq_only.txt'] = {
                'exists': False,
                'error': str(e)
            }
        
        # Calcular estado general
        all_groq_ready = all(
            file_result.get('groq_ready', False) 
            for file_result in results.values() 
            if file_result.get('exists', False)
        )
        
        result = {
            'groq_files': results,
            'all_groq_ready': all_groq_ready,
            'status': 'success' if all_groq_ready else 'warning'
        }
        
        self.logger.info(f"✅ Groq-only files validated - Ready: {all_groq_ready}")
        return result
    
    def validate_backup_integrity(self) -> Dict:
        """Validar integridad de los archivos de backup."""
        self.logger.info("🔍 Validating backup integrity...")
        
        backup_dir = 'backup_paid_services'
        results = {}
        
        if not os.path.exists(backup_dir):
            return {
                'backup_exists': False,
                'status': 'error',
                'error': 'Backup directory not found'
            }
        
        # Verificar archivos de backup
        backup_files = [
            'README_PAID_SERVICES.md',
            'restoration_guide.md',
            'backup_script.ps1',
            'restore_script.ps1',
            'core/advanced_plan_analyzer_openai.py',
            'config/docker-compose.paid.yml',
            'config/env_production.paid.txt'
        ]
        
        existing_backups = []
        missing_backups = []
        
        for backup_file in backup_files:
            file_path = os.path.join(backup_dir, backup_file)
            if os.path.exists(file_path):
                existing_backups.append(backup_file)
            else:
                missing_backups.append(backup_file)
        
        result = {
            'backup_exists': True,
            'existing_backups': existing_backups,
            'missing_backups': missing_backups,
            'backup_completeness': len(existing_backups) / len(backup_files),
            'status': 'success' if len(missing_backups) == 0 else 'warning'
        }
        
        self.logger.info(f"✅ Backup integrity validated - Complete: {result['backup_completeness']:.2%}")
        return result
    
    def validate_code_consistency(self) -> Dict:
        """Validar consistencia del código."""
        self.logger.info("🔍 Validating code consistency...")
        
        results = {}
        
        # Verificar que no hay referencias a APIs pagas en el código principal
        code_files = [
            'backend/app/core/advanced_plan_analyzer.py',
            'backend/app/core/ai_client.py',
            'backend/app/core/enhanced_prompts.py'
        ]
        
        for code_file in code_files:
            if os.path.exists(code_file):
                try:
                    with open(code_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Verificar referencias a APIs pagas
                    has_openai_refs = 'openai' in content.lower() and 'import' in content.lower()
                    has_google_refs = 'google' in content.lower() and 'vision' in content.lower()
                    
                    results[code_file] = {
                        'exists': True,
                        'no_openai_refs': not has_openai_refs,
                        'no_google_refs': not has_google_refs,
                        'clean': not has_openai_refs and not has_google_refs
                    }
                except Exception as e:
                    results[code_file] = {
                        'exists': True,
                        'error': str(e)
                    }
            else:
                results[code_file] = {
                    'exists': False,
                    'error': 'File not found'
                }
        
        # Calcular estado general
        all_clean = all(
            file_result.get('clean', False) 
            for file_result in results.values() 
            if file_result.get('exists', False)
        )
        
        result = {
            'code_files': results,
            'all_clean': all_clean,
            'status': 'success' if all_clean else 'warning'
        }
        
        self.logger.info(f"✅ Code consistency validated - Clean: {all_clean}")
        return result
    
    def validate_arm64_compatibility(self) -> Dict:
        """Validar compatibilidad con ARM64."""
        self.logger.info("🔍 Validating ARM64 compatibility...")
        
        results = {}
        
        # Verificar archivos específicos de ARM64
        arm64_files = [
            'requirements.arm64.txt',
            'docker-compose.arm64.yml',
            'Dockerfile.arm64',
            'user_data_arm64.sh',
            'deploy_arm64.sh',
            'INSTRUCCIONES_ARM64.md'
        ]
        
        existing_arm64_files = []
        missing_arm64_files = []
        
        for arm64_file in arm64_files:
            if os.path.exists(arm64_file):
                existing_arm64_files.append(arm64_file)
            else:
                missing_arm64_files.append(arm64_file)
        
        # Verificar que requirements.arm64.txt no tiene FAISS
        faiss_free = True
        if os.path.exists('requirements.arm64.txt'):
            try:
                with open('requirements.arm64.txt', 'r') as f:
                    content = f.read()
                faiss_free = 'faiss-cpu' not in content
            except:
                faiss_free = False
        
        result = {
            'arm64_files': {
                'existing': existing_arm64_files,
                'missing': missing_arm64_files,
                'completeness': len(existing_arm64_files) / len(arm64_files)
            },
            'faiss_free': faiss_free,
            'arm64_ready': len(missing_arm64_files) == 0 and faiss_free,
            'status': 'success' if len(missing_arm64_files) == 0 and faiss_free else 'warning'
        }
        
        self.logger.info(f"✅ ARM64 compatibility validated - Ready: {result['arm64_ready']}")
        return result
    
    def generate_recommendations(self) -> List[str]:
        """Generar recomendaciones basadas en la validación."""
        recommendations = []
        
        # Recomendaciones basadas en archivos faltantes
        file_structure = self.validation_results.get('files_checked', {}).get('file_structure', {})
        missing_files = file_structure.get('missing_files', [])
        
        if missing_files:
            recommendations.append(f"📁 Crear archivos faltantes: {', '.join(missing_files[:3])}{'...' if len(missing_files) > 3 else ''}")
        
        # Recomendaciones basadas en configuración Groq
        groq_files = self.validation_results.get('configurations_valid', {}).get('groq_only_files', {})
        if not groq_files.get('all_groq_ready', False):
            recommendations.append("🔧 Revisar configuración de archivos Groq-only")
        
        # Recomendaciones basadas en backup
        backup_result = self.validation_results.get('configurations_valid', {}).get('backup_integrity', {})
        if not backup_result.get('backup_exists', False):
            recommendations.append("💾 Crear backup de servicios pagos")
        elif backup_result.get('backup_completeness', 1.0) < 0.8:
            recommendations.append("💾 Completar backup de servicios pagos")
        
        # Recomendaciones basadas en consistencia de código
        code_consistency = self.validation_results.get('configurations_valid', {}).get('code_consistency', {})
        if not code_consistency.get('all_clean', False):
            recommendations.append("🧹 Limpiar referencias a APIs pagas en el código")
        
        # Recomendaciones basadas en ARM64
        arm64_compatibility = self.validation_results.get('configurations_valid', {}).get('arm64_compatibility', {})
        if not arm64_compatibility.get('arm64_ready', False):
            recommendations.append("🏗️ Completar configuración para ARM64")
        
        if not recommendations:
            recommendations.append("🎉 Configuración completa y lista para producción!")
        
        return recommendations
    
    def run_complete_validation(self) -> Dict:
        """Ejecutar validación completa."""
        self.logger.info("🚀 Starting complete configuration validation...")
        
        from datetime import datetime
        self.validation_results['timestamp'] = datetime.now().isoformat()
        
        # Ejecutar todas las validaciones
        self.validation_results['files_checked'] = {
            'file_structure': self.validate_file_structure()
        }
        
        self.validation_results['configurations_valid'] = {
            'groq_only_files': self.validate_groq_only_files(),
            'backup_integrity': self.validate_backup_integrity(),
            'code_consistency': self.validate_code_consistency(),
            'arm64_compatibility': self.validate_arm64_compatibility()
        }
        
        # Generar recomendaciones
        self.validation_results['recommendations'] = self.generate_recommendations()
        
        # Calcular estado general
        all_validations = []
        for category in self.validation_results['configurations_valid'].values():
            if isinstance(category, dict) and 'status' in category:
                all_validations.append(category['status'])
        
        if all(status == 'success' for status in all_validations):
            self.validation_results['overall_status'] = 'success'
        elif any(status == 'error' for status in all_validations):
            self.validation_results['overall_status'] = 'error'
        else:
            self.validation_results['overall_status'] = 'warning'
        
        # Generar reporte
        self._generate_validation_report()
        
        return self.validation_results
    
    def _generate_validation_report(self):
        """Generar reporte de validación."""
        report_path = "validation_report_groq_config.json"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.validation_results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📊 Validation report saved to {report_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving validation report: {e}")
    
    def print_validation_summary(self):
        """Imprimir resumen de validación."""
        print("\n" + "="*70)
        print("🔍 VALIDACIÓN DE CONFIGURACIÓN GROQ-ONLY")
        print("="*70)
        
        print(f"\n📅 Fecha: {self.validation_results['timestamp']}")
        print(f"🎯 Estado general: {self.validation_results['overall_status'].upper()}")
        
        print("\n📁 ARCHIVOS VERIFICADOS:")
        
        # Mostrar resultados de estructura de archivos
        file_structure = self.validation_results.get('files_checked', {}).get('file_structure', {})
        missing_files = file_structure.get('missing_files', [])
        
        if missing_files:
            print(f"  ⚠️  Archivos faltantes: {len(missing_files)}")
            for file in missing_files[:5]:  # Mostrar solo los primeros 5
                print(f"     • {file}")
            if len(missing_files) > 5:
                print(f"     • ... y {len(missing_files) - 5} más")
        else:
            print("  ✅ Todos los archivos necesarios están presentes")
        
        print("\n🔧 CONFIGURACIONES VALIDADAS:")
        
        # Mostrar resultados de configuraciones
        configs = self.validation_results.get('configurations_valid', {})
        
        config_names = {
            'groq_only_files': 'Archivos Groq-only',
            'backup_integrity': 'Integridad de Backup',
            'code_consistency': 'Consistencia de Código',
            'arm64_compatibility': 'Compatibilidad ARM64'
        }
        
        for config_key, config_name in config_names.items():
            config_result = configs.get(config_key, {})
            status = config_result.get('status', 'unknown')
            
            if status == 'success':
                icon = "✅"
            elif status == 'warning':
                icon = "⚠️"
            elif status == 'error':
                icon = "❌"
            else:
                icon = "❓"
            
            print(f"  {icon} {config_name}: {status.upper()}")
        
        print("\n📋 RECOMENDACIONES:")
        
        recommendations = self.validation_results.get('recommendations', [])
        for rec in recommendations:
            print(f"  • {rec}")
        
        print("\n✅ Validación completada!")
        print("="*70)

def main():
    """Función principal."""
    print("🔍 Iniciando validación de configuración Groq-only...")
    
    validator = GroqConfigValidator()
    results = validator.run_complete_validation()
    validator.print_validation_summary()
    
    return results

if __name__ == "__main__":
    main()
