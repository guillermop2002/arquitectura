#!/usr/bin/env python3
"""
Script para verificar errores específicos en el código.
"""

import os
import re
from pathlib import Path

def check_ocr_errors():
    """Verificar errores de OCR."""
    print("🔍 Verificando errores de OCR...")
    
    ocr_file = Path("backend/app/core/enhanced_ocr_processor.py")
    if not ocr_file.exists():
        print("❌ Archivo OCR no encontrado")
        return False
    
    content = ocr_file.read_text(encoding='utf-8')
    
    # Buscar líneas problemáticas
    int_pattern = r'confidence = int\(data\[\'conf\'\]\[i\]\)'
    float_pattern = r'confidence = float\(data\[\'conf\'\]\[i\]\)'
    
    int_matches = re.findall(int_pattern, content)
    float_matches = re.findall(float_pattern, content)
    
    print(f"   📍 Líneas con int(): {len(int_matches)}")
    print(f"   📍 Líneas con float(): {len(float_matches)}")
    
    if int_matches and not float_matches:
        print("❌ ERROR: Todavía hay conversiones int() que causan errores")
        return False
    elif float_matches:
        print("✅ OK: Conversiones float() encontradas")
        return True
    else:
        print("⚠️ ADVERTENCIA: No se encontraron conversiones de confianza")
        return False

def check_ai_client_errors():
    """Verificar errores de AI Client."""
    print("🔍 Verificando errores de AI Client...")
    
    # Archivos que usan AIClient
    files_to_check = [
        "backend/app/core/document_classifier.py",
        "backend/app/core/report_generator.py",
        "backend/app/core/conversational_ai.py",
        "backend/app/core/enhanced_project_analyzer_v2.py",
        "backend/app/core/ambiguity_resolver.py",
        "backend/app/core/advanced_plan_analyzer_groq.py",
        "backend/app/core/advanced_plan_analyzer.py",
        "backend/app/core/madrid_compliance_checker.py"
    ]
    
    errors_found = []
    
    for file_path in files_to_check:
        if not Path(file_path).exists():
            continue
            
        content = Path(file_path).read_text(encoding='utf-8')
        
        # Buscar generate_response
        generate_response_matches = re.findall(r'\.generate_response\(', content)
        generate_completion_matches = re.findall(r'\.generate_completion\(', content)
        
        if generate_response_matches:
            errors_found.append({
                'file': file_path,
                'generate_response': len(generate_response_matches),
                'generate_completion': len(generate_completion_matches)
            })
    
    if errors_found:
        print("❌ ERRORES ENCONTRADOS:")
        for error in errors_found:
            print(f"   📍 {error['file']}: {error['generate_response']} generate_response, {error['generate_completion']} generate_completion")
        return False
    else:
        print("✅ OK: No se encontraron errores de AI Client")
        return True

def check_document_analyzer_errors():
    """Verificar errores de Document Analyzer."""
    print("🔍 Verificando errores de Document Analyzer...")
    
    # Verificar el archivo de análisis de documentos
    analysis_file = Path("backend/app/api/madrid_document_analysis_endpoints.py")
    if not analysis_file.exists():
        print("❌ Archivo de análisis no encontrado")
        return False
    
    content = analysis_file.read_text(encoding='utf-8')
    
    # Buscar llamadas problemáticas
    content_matches = re.findall(r'content=', content)
    pdf_doc_matches = re.findall(r'pdf_doc=', content)
    classification_matches = re.findall(r'classification=', content)
    
    print(f"   📍 Llamadas con 'content=': {len(content_matches)}")
    print(f"   📍 Llamadas con 'pdf_doc=': {len(pdf_doc_matches)}")
    print(f"   📍 Llamadas con 'classification=': {len(classification_matches)}")
    
    if content_matches and not (pdf_doc_matches and classification_matches):
        print("❌ ERROR: Todavía hay llamadas con 'content=' que causan errores")
        return False
    elif pdf_doc_matches and classification_matches:
        print("✅ OK: Llamadas correctas encontradas")
        return True
    else:
        print("⚠️ ADVERTENCIA: No se encontraron llamadas al Document Analyzer")
        return False

def check_session_errors():
    """Verificar errores de sesión."""
    print("🔍 Verificando errores de sesión...")
    
    # Verificar que el session_file_manager existe
    session_file = Path("backend/app/core/session_file_manager.py")
    if not session_file.exists():
        print("❌ SessionFileManager no encontrado")
        return False
    
    # Verificar que se está usando correctamente
    analysis_file = Path("backend/app/api/madrid_document_analysis_endpoints.py")
    if not analysis_file.exists():
        print("❌ Archivo de análisis no encontrado")
        return False
    
    content = analysis_file.read_text(encoding='utf-8')
    
    # Buscar uso correcto del session_file_manager
    session_manager_matches = re.findall(r'session_file_manager\.', content)
    session_id_matches = re.findall(r'session_id', content)
    
    print(f"   📍 Usos de session_file_manager: {len(session_manager_matches)}")
    print(f"   📍 Referencias a session_id: {len(session_id_matches)}")
    
    if session_manager_matches and session_id_matches:
        print("✅ OK: SessionFileManager se está usando correctamente")
        return True
    else:
        print("❌ ERROR: SessionFileManager no se está usando correctamente")
        return False

def check_scikit_learn_removal():
    """Verificar que scikit-learn se ha eliminado correctamente."""
    print("🔍 Verificando eliminación de scikit-learn...")
    
    # Verificar requirements
    requirements_file = Path("requirements.oracle_arm64.txt")
    if requirements_file.exists():
        content = requirements_file.read_text(encoding='utf-8')
        if 'scikit-learn' in content and not content.strip().startswith('#'):
            print("❌ ERROR: scikit-learn todavía está en requirements.oracle_arm64.txt")
            return False
    
    # Verificar archivos Python
    files_to_check = [
        "backend/app/core/intelligent_question_engine_arm64.py"
    ]
    
    for file_path in files_to_check:
        if not Path(file_path).exists():
            continue
            
        content = Path(file_path).read_text(encoding='utf-8')
        
        # Buscar imports de scikit-learn (solo si no están comentados)
        sklearn_imports = re.findall(r'^[^#]*from sklearn\.|^[^#]*import sklearn', content, re.MULTILINE)
        if sklearn_imports:
            print(f"❌ ERROR: scikit-learn todavía se importa en {file_path}")
            print(f"   📍 Imports encontrados: {sklearn_imports}")
            return False
    
    print("✅ OK: scikit-learn se ha eliminado correctamente")
    return True

def main():
    """Función principal."""
    print("🔍 VERIFICACIÓN DE ERRORES ESPECÍFICOS")
    print("=" * 50)
    
    checks = [
        ("OCR Errors", check_ocr_errors),
        ("AI Client Errors", check_ai_client_errors),
        ("Document Analyzer Errors", check_document_analyzer_errors),
        ("Session Errors", check_session_errors),
        ("Scikit-learn Removal", check_scikit_learn_removal)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"❌ ERROR al ejecutar {check_name}: {e}")
            results[check_name] = False
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE VERIFICACIONES:")
    
    passed = 0
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {check_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 RESULTADO: {passed}/{total} verificaciones pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las verificaciones pasaron! El código está listo para reconstruir.")
    else:
        print("⚠️ Algunas verificaciones fallaron. Revisar los errores antes de reconstruir.")
    
    return passed == total

if __name__ == "__main__":
    main()
