#!/usr/bin/env python3
"""
Script de diagnóstico de errores para el sistema de verificación arquitectónica.
Analiza los logs y proporciona información detallada sobre los errores.
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict, Counter

class ErrorDiagnostic:
    """Diagnóstico de errores del sistema."""
    
    def __init__(self):
        self.errors = []
        self.error_patterns = {
            'ocr_error': r'Error in OCR processing: invalid literal for int\(\) with base 10:',
            'ai_client_error': r"'AIClient' object has no attribute 'generate_response'",
            'document_analyzer_error': r"DocumentAnalyzer\.analyze_document\(\) got an unexpected keyword argument 'content'",
            'session_error': r'Sesión no encontrada:',
            'unknown_error': r'Error en Unknown: <function.*at 0x[0-9a-f]+>',
            'traceback_none': r'Traceback: NoneType: None'
        }
        
    def analyze_log_line(self, line: str) -> Dict[str, Any]:
        """Analizar una línea de log."""
        error_info = {
            'timestamp': None,
            'level': None,
            'component': None,
            'error_type': None,
            'message': None,
            'details': {}
        }
        
        # Extraer timestamp
        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
        if timestamp_match:
            error_info['timestamp'] = timestamp_match.group(1)
        
        # Extraer nivel de log
        level_match = re.search(r'(ERROR|WARNING|INFO|CRITICAL)', line)
        if level_match:
            error_info['level'] = level_match.group(1)
        
        # Extraer componente
        component_match = re.search(r'backend\.app\.core\.(\w+)', line)
        if component_match:
            error_info['component'] = component_match.group(1)
        
        # Identificar tipo de error
        for error_type, pattern in self.error_patterns.items():
            if re.search(pattern, line):
                error_info['error_type'] = error_type
                error_info['message'] = line.strip()
                break
        
        return error_info
    
    def analyze_logs(self, log_content: str) -> Dict[str, Any]:
        """Analizar logs completos."""
        lines = log_content.split('\n')
        analysis = {
            'total_lines': len(lines),
            'error_lines': 0,
            'error_types': Counter(),
            'components': Counter(),
            'timeline': [],
            'critical_errors': [],
            'recommendations': []
        }
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
                
            error_info = self.analyze_log_line(line)
            
            if error_info['error_type']:
                analysis['error_lines'] += 1
                analysis['error_types'][error_info['error_type']] += 1
                
                if error_info['component']:
                    analysis['components'][error_info['component']] += 1
                
                if error_info['timestamp']:
                    analysis['timeline'].append({
                        'timestamp': error_info['timestamp'],
                        'error_type': error_info['error_type'],
                        'component': error_info['component'],
                        'line_number': i + 1
                    })
                
                if error_info['level'] == 'CRITICAL':
                    analysis['critical_errors'].append({
                        'line': i + 1,
                        'message': error_info['message'],
                        'component': error_info['component']
                    })
        
        # Generar recomendaciones
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones basadas en el análisis."""
        recommendations = []
        
        # OCR errors
        if analysis['error_types']['ocr_error'] > 0:
            recommendations.append(
                "🔧 ERROR OCR: El procesador OCR está intentando convertir valores float a int. "
                "Necesita actualizar enhanced_ocr_processor.py para usar float() en lugar de int()."
            )
        
        # AI Client errors
        if analysis['error_types']['ai_client_error'] > 0:
            recommendations.append(
                "🔧 ERROR AI CLIENT: El cliente de IA está usando el método incorrecto 'generate_response'. "
                "Necesita cambiar a 'generate_completion' en todos los archivos que usan AIClient."
            )
        
        # Document Analyzer errors
        if analysis['error_types']['document_analyzer_error'] > 0:
            recommendations.append(
                "🔧 ERROR DOCUMENT ANALYZER: El analizador de documentos está recibiendo argumentos incorrectos. "
                "Necesita actualizar las llamadas para usar 'pdf_doc' y 'classification' en lugar de 'content'."
            )
        
        # Session errors
        if analysis['error_types']['session_error'] > 0:
            recommendations.append(
                "🔧 ERROR SESIÓN: Las sesiones no se están encontrando correctamente. "
                "Verificar que el session_file_manager esté funcionando correctamente."
            )
        
        # Unknown errors
        if analysis['error_types']['unknown_error'] > 0:
            recommendations.append(
                "🔧 ERROR DESCONOCIDO: Hay errores en funciones que no se pueden identificar. "
                "Esto sugiere problemas de inicialización o configuración de componentes."
            )
        
        # General recommendations
        if analysis['error_lines'] > 100:
            recommendations.append(
                "⚠️ ALTO VOLUMEN DE ERRORES: Hay muchos errores en los logs. "
                "Considerar reconstruir el contenedor Docker para aplicar todas las correcciones."
            )
        
        return recommendations
    
    def generate_report(self, analysis: Dict[str, Any]) -> str:
        """Generar reporte de diagnóstico."""
        report = []
        report.append("=" * 80)
        report.append("🔍 DIAGNÓSTICO DE ERRORES - SISTEMA DE VERIFICACIÓN ARQUITECTÓNICA")
        report.append("=" * 80)
        report.append(f"📅 Fecha de análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Resumen general
        report.append("📊 RESUMEN GENERAL:")
        report.append(f"   • Total de líneas analizadas: {analysis['total_lines']}")
        report.append(f"   • Líneas con errores: {analysis['error_lines']}")
        report.append(f"   • Porcentaje de errores: {(analysis['error_lines']/analysis['total_lines']*100):.2f}%")
        report.append("")
        
        # Tipos de errores
        report.append("🚨 TIPOS DE ERRORES DETECTADOS:")
        for error_type, count in analysis['error_types'].most_common():
            report.append(f"   • {error_type}: {count} ocurrencias")
        report.append("")
        
        # Componentes con errores
        report.append("🔧 COMPONENTES CON ERRORES:")
        for component, count in analysis['components'].most_common():
            report.append(f"   • {component}: {count} errores")
        report.append("")
        
        # Errores críticos
        if analysis['critical_errors']:
            report.append("🚨 ERRORES CRÍTICOS:")
            for error in analysis['critical_errors'][:5]:  # Mostrar solo los primeros 5
                report.append(f"   • Línea {error['line']}: {error['message'][:100]}...")
            report.append("")
        
        # Recomendaciones
        report.append("💡 RECOMENDACIONES:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            report.append(f"   {i}. {rec}")
        report.append("")
        
        # Timeline de errores (últimos 10)
        if analysis['timeline']:
            report.append("⏰ TIMELINE DE ERRORES (últimos 10):")
            for error in analysis['timeline'][-10:]:
                report.append(f"   • {error['timestamp']} - {error['error_type']} en {error['component']}")
            report.append("")
        
        report.append("=" * 80)
        report.append("🎯 PRÓXIMOS PASOS:")
        report.append("1. Revisar las recomendaciones específicas")
        report.append("2. Aplicar las correcciones necesarias")
        report.append("3. Reconstruir el contenedor Docker")
        report.append("4. Verificar que los errores se hayan resuelto")
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    """Función principal."""
    print("🔍 Iniciando diagnóstico de errores...")
    
    # Simular análisis de logs (en producción se leerían de un archivo)
    diagnostic = ErrorDiagnostic()
    
    # Ejemplo de análisis
    sample_logs = """
    2025-09-22 15:41:28 - backend.app.core.enhanced_ocr_processor - ERROR - Error in OCR processing: invalid literal for int() with base 10: '96.380676'
    2025-09-22 15:41:28 - backend.app.core.document_classifier - ERROR - Error en clasificación con IA: 'AIClient' object has no attribute 'generate_response'
    2025-09-22 15:41:28 - backend.app.api.madrid_document_analysis_endpoints - ERROR - Error procesando memoria: DocumentAnalyzer.analyze_document() got an unexpected keyword argument 'content'
    """
    
    analysis = diagnostic.analyze_logs(sample_logs)
    report = diagnostic.generate_report(analysis)
    
    print(report)
    
    # Guardar reporte
    with open('error_diagnostic_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n✅ Reporte guardado en: error_diagnostic_report.txt")

if __name__ == "__main__":
    main()
