#!/usr/bin/env python3
"""
Script para ejecutar auditoría completa del sistema básico
"""

import sys
import json
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from backend.app.basico.audit_checker import BasicoAuditChecker

def main():
    print("🔍 EJECUTANDO AUDITORÍA COMPLETA DEL SISTEMA BÁSICO")
    print("=" * 60)
    
    try:
        # Crear auditor
        auditor = BasicoAuditChecker()
        
        # Ejecutar auditoría
        results = auditor.run_complete_audit()
        
        # Mostrar resultados
        print(f"📊 RESULTADOS DE AUDITORÍA")
        print(f"Timestamp: {results['audit_timestamp']}")
        print(f"Estado del sistema: {results['system_status']}")
        print()
        
        # Acceder a los checks detallados
        checks = results['detailed_checks']
        
        # Componentes
        comp = checks['components']
        working_count = comp.get('working_count', 0)
        total_count = comp.get('total_count', 0)
        print(f"🔧 COMPONENTES: {working_count}/{total_count} funcionando")
        if 'component_details' in comp:
            for name, status in comp['component_details'].items():
                icon = "✅" if status.get('status') == 'working' else "❌"
                print(f"  {icon} {name}: {status.get('status', 'unknown')}")
        print()
        
        # Dependencias
        deps = checks['dependencies']
        working_count = deps.get('working_count', 0)
        total_count = deps.get('total_count', 0)
        print(f"📦 DEPENDENCIAS: {working_count}/{total_count} instaladas")
        if 'dependency_details' in deps:
            for name, status in deps['dependency_details'].items():
                icon = "✅" if status.get('status') == 'installed' else "❌"
                print(f"  {icon} {name}: {status.get('status', 'unknown')}")
        print()
        
        # Configuración
        config = checks['configuration']
        working_count = config.get('working_count', 0)
        total_count = config.get('total_count', 0)
        print(f"⚙️ CONFIGURACIÓN: {working_count}/{total_count} correctas")
        if 'checks' in config:
            for name, status in config['checks'].items():
                icon = "✅" if status.get('status') == 'good' else "❌"
                print(f"  {icon} {name}: {status.get('status', 'unknown')}")
        print()
        
        # Archivos normativos
        norm = checks['normative_files']
        print(f"📋 ARCHIVOS NORMATIVOS: {norm.get('status', 'unknown')}")
        print(f"  📁 Directorio existe: {'✅' if norm.get('directory_exists', False) else '❌'}")
        if norm.get('directory_exists', False):
            print(f"  📄 PDFs: {norm.get('pdf_files_count', 0)}")
            print(f"  📄 JSONs: {norm.get('json_files_count', 0)}")
            print(f"  📋 anexo1.json: {'✅' if norm.get('anexo1_exists', False) else '❌'}")
        print()
        
        # IA
        ai = checks['ai_integration']
        print(f"🤖 INTEGRACIÓN IA: {ai.get('status', 'unknown')}")
        if ai.get('status') == 'good':
            print(f"  ✅ Prompts disponibles: {ai.get('prompts_available', False)}")
            print(f"  ✅ Configuración disponible: {ai.get('config_available', False)}")
        print()
        
        # OCR
        ocr = checks['ocr_processing']
        print(f"🔍 PROCESAMIENTO OCR: {ocr.get('status', 'unknown')}")
        if ocr.get('status') == 'good':
            print(f"  ✅ OCR disponible: {ocr.get('ocr_available', False)}")
            print(f"  ✅ Método extracción: {ocr.get('extract_method', 'unknown')}")
            print(f"  ✅ Método búsqueda: {ocr.get('search_method', 'unknown')}")
        print()
        
        # Preparación para producción
        print(f"🚀 PREPARACIÓN PARA PRODUCCIÓN")
        print(f"Puntuación general: {results['overall_score']:.1f}%")
        print(f"Nivel de preparación: {results['readiness_level']}")
        print(f"Listo para producción: {'✅' if results['production_ready'] else '❌'}")
        print()
        
        # Puntuaciones individuales
        print("📊 PUNTUACIONES DETALLADAS:")
        for category, score in results['individual_scores'].items():
            icon = "✅" if score >= 90 else "⚠️" if score >= 70 else "❌"
            print(f"  {icon} {category}: {score:.1f}%")
        print()
        
        # Recomendaciones
        print("💡 RECOMENDACIONES:")
        for rec in results['recommendations']:
            print(f"  • {rec}")
        print()
        
        # Resumen final
        if results['system_status'] == 'production_ready':
            print("🎉 ¡SISTEMA LISTO PARA PRODUCCIÓN!")
        elif results['system_status'] == 'needs_minor_fixes':
            print("⚠️ Sistema necesita ajustes menores")
        else:
            print("❌ Sistema necesita reparaciones importantes")
        
        print("=" * 60)
        
        # Guardar resultados
        with open('audit_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print("💾 Resultados guardados en audit_results.json")
        
        return 0 if results['system_status'] == 'production_ready' else 1
        
    except Exception as e:
        print(f"❌ Error ejecutando auditoría: {e}")
        return 1

if __name__ == "__main__":
    exit(main())