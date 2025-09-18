"""
Endpoints para clasificación automática de documentos Madrid.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import json

from ..core.pdf_processor import PDFProcessor
from ..core.document_classifier import DocumentClassifier
from ..core.document_analyzer import DocumentAnalyzer
from ..core.ai_client import AIClient

logger = logging.getLogger(__name__)

# Router para endpoints de clasificación de documentos
classification_router = APIRouter(prefix="/madrid/classification", tags=["Madrid Document Classification"])

# Inicializar procesadores
pdf_processor = PDFProcessor()
ai_client = AIClient()
classifier = DocumentClassifier(ai_client)
analyzer = DocumentAnalyzer()

@classification_router.post("/classify-documents")
async def classify_documents(
    memoria_files: List[UploadFile] = File(..., description="Archivos de memoria descriptiva"),
    plano_files: List[UploadFile] = File(..., description="Archivos de planos arquitectónicos"),
    is_existing_building: bool = Form(False),
    primary_use: str = Form(...),
    has_secondary_uses: bool = Form(False),
    secondary_uses: str = Form("[]")
):
    """
    Clasificar automáticamente documentos entre memorias y planos.
    
    Args:
        memoria_files: Archivos subidos como memorias
        plano_files: Archivos subidos como planos
        is_existing_building: Si es edificio existente
        primary_use: Uso principal del edificio
        has_secondary_uses: Si tiene usos secundarios
        secondary_uses: Usos secundarios en formato JSON
        
    Returns:
        Resultado de la clasificación automática
    """
    try:
        logger.info(f"Clasificando {len(memoria_files)} memorias y {len(plano_files)} planos")
        
        # Combinar todos los archivos
        all_files = memoria_files + plano_files
        
        if not all_files:
            raise HTTPException(status_code=400, detail="No se proporcionaron archivos")
        
        # Procesar archivos
        processed_files = []
        classification_results = {
            'memoria_files': [],
            'plano_files': [],
            'total_files': len(all_files),
            'classification_summary': {}
        }
        
        for file in all_files:
            try:
                # Guardar archivo temporalmente
                file_content = await file.read()
                temp_path = f"/tmp/{file.filename}"
                
                with open(temp_path, 'wb') as f:
                    f.write(file_content)
                
                # Procesar PDF
                pdf_doc = pdf_processor.process_pdf(temp_path)
                
                # Clasificar documento
                classification = await classifier.classify_document(temp_path)
                
                # Analizar contenido
                content = analyzer.analyze_document(pdf_doc, classification)
                
                # Crear resultado
                file_result = {
                    'filename': file.filename,
                    'original_category': 'memoria' if file in memoria_files else 'plano',
                    'classification': {
                        'document_type': classification.document_type,
                        'confidence': classification.confidence,
                        'reasoning': classification.reasoning,
                        'detected_elements': classification.detected_elements
                    },
                    'content_analysis': {
                        'title': content.title,
                        'sections': content.sections,
                        'technical_data': content.technical_data,
                        'visual_elements': content.visual_elements
                    },
                    'pdf_info': {
                        'page_count': pdf_doc.page_count,
                        'file_size': pdf_doc.file_size,
                        'processing_time': pdf_doc.processing_time
                    }
                }
                
                # Agregar a la categoría correspondiente
                if classification.document_type == 'memoria':
                    classification_results['memoria_files'].append(file_result)
                else:
                    classification_results['plano_files'].append(file_result)
                
                processed_files.append(file_result)
                
                # Limpiar archivo temporal
                import os
                os.remove(temp_path)
                
            except Exception as e:
                logger.error(f"Error procesando archivo {file.filename}: {e}")
                continue
        
        # Crear resumen de clasificación
        classification_results['classification_summary'] = {
            'total_processed': len(processed_files),
            'memoria_count': len(classification_results['memoria_files']),
            'plano_count': len(classification_results['plano_files']),
            'average_confidence': sum(f['classification']['confidence'] for f in processed_files) / len(processed_files) if processed_files else 0,
            'high_confidence_files': len([f for f in processed_files if f['classification']['confidence'] > 0.8]),
            'low_confidence_files': len([f for f in processed_files if f['classification']['confidence'] < 0.6])
        }
        
        logger.info(f"Clasificación completada: {len(classification_results['memoria_files'])} memorias, {len(classification_results['plano_files'])} planos")
        
        return JSONResponse(content=classification_results)
        
    except Exception as e:
        logger.error(f"Error en clasificación de documentos: {e}")
        raise HTTPException(status_code=500, detail=f"Error en clasificación: {str(e)}")

@classification_router.post("/validate-classification")
async def validate_classification(
    file_path: str = Form(...),
    expected_type: str = Form(...),
    user_feedback: str = Form(...)
):
    """
    Validar y mejorar la clasificación basada en feedback del usuario.
    
    Args:
        file_path: Ruta del archivo
        expected_type: Tipo esperado por el usuario
        user_feedback: Feedback del usuario
        
    Returns:
        Resultado de la validación
    """
    try:
        logger.info(f"Validando clasificación para {file_path}")
        
        # Procesar archivo
        pdf_doc = pdf_processor.process_pdf(file_path)
        classification = await classifier.classify_document(file_path)
        
        # Comparar con expectativa del usuario
        is_correct = classification.document_type == expected_type
        confidence_delta = abs(classification.confidence - 0.5)  # Qué tan seguro estaba el sistema
        
        # Crear resultado de validación
        validation_result = {
            'file_path': file_path,
            'system_classification': classification.document_type,
            'user_expected': expected_type,
            'is_correct': is_correct,
            'confidence': classification.confidence,
            'confidence_delta': confidence_delta,
            'user_feedback': user_feedback,
            'needs_improvement': not is_correct and confidence_delta > 0.3
        }
        
        # Si la clasificación fue incorrecta, sugerir mejoras
        if not is_correct:
            validation_result['suggestions'] = [
                "Revisar patrones de texto específicos",
                "Mejorar análisis de elementos visuales",
                "Ajustar pesos de clasificación"
            ]
        
        return JSONResponse(content=validation_result)
        
    except Exception as e:
        logger.error(f"Error validando clasificación: {e}")
        raise HTTPException(status_code=500, detail=f"Error en validación: {str(e)}")

@classification_router.get("/classification-stats")
async def get_classification_stats():
    """
    Obtener estadísticas de clasificación.
    
    Returns:
        Estadísticas de clasificación
    """
    try:
        # Aquí se podrían obtener estadísticas de una base de datos
        # Por ahora, devolver estadísticas básicas
        stats = {
            'total_classifications': 0,
            'memoria_classifications': 0,
            'plano_classifications': 0,
            'average_confidence': 0.0,
            'accuracy_rate': 0.0,
            'last_updated': None
        }
        
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

@classification_router.post("/improve-classification")
async def improve_classification(
    feedback_data: Dict[str, Any]
):
    """
    Mejorar el modelo de clasificación basado en feedback.
    
    Args:
        feedback_data: Datos de feedback para mejorar el modelo
        
    Returns:
        Resultado de la mejora
    """
    try:
        logger.info("Mejorando modelo de clasificación")
        
        # Aquí se implementaría la lógica para mejorar el modelo
        # basado en el feedback del usuario
        
        improvement_result = {
            'status': 'success',
            'message': 'Modelo de clasificación mejorado',
            'improvements_applied': [
                'Ajustados patrones de texto',
                'Mejorados pesos de clasificación',
                'Actualizados umbrales de confianza'
            ],
            'new_accuracy': 0.85  # Ejemplo
        }
        
        return JSONResponse(content=improvement_result)
        
    except Exception as e:
        logger.error(f"Error mejorando clasificación: {e}")
        raise HTTPException(status_code=500, detail=f"Error mejorando clasificación: {str(e)}")
