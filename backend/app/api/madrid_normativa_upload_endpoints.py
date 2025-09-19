"""
Endpoints para subir y gestionar archivos de normativa Madrid.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import zipfile
import tempfile

logger = logging.getLogger(__name__)

# Router para endpoints de normativa
normativa_upload_router = APIRouter(prefix="/api/madrid/normativa", tags=["Normativa Upload"])

class NormativaUploadManager:
    """Gestor de subida de archivos de normativa."""
    
    def __init__(self, normative_path: str = "Normativa"):
        """
        Inicializar el gestor de normativa.
        
        Args:
            normative_path: Ruta a la carpeta de normativa
        """
        self.normative_path = Path(normative_path)
        self.normative_path.mkdir(exist_ok=True)
        
        # Estructura esperada de normativa
        self.expected_structure = {
            "DOCUMENTOS BASICOS": {
                "DBHE": ["DBHE.pdf"],
                "DBHR": ["DBHR.pdf"],
                "DBHS": ["DBHS.pdf"],
                "DBSE": ["DBSE.pdf", "DBSE-A.pdf", "DBSE-AE.pdf", "DBSE-C.pdf", "DBSE-F.pdf", "DBSE-M.pdf"],
                "DBSI": ["DBSI.pdf", "REGLAMENTO INSTALACIONES.pdf"],
                "DBSUA": ["DBSUA.pdf"]
            },
            "DOCUMENTOS DE APOYO": {
                "DBHE": [],
                "DBHR": [],
                "DBSI": [],
                "DBSUA": []
            },
            "PGOUM": [
                "pgoum_general universal.pdf",
                "pgoum_residencial.pdf",
                "pgoum_industrial.pdf",
                "pgoum_servicios terciarios.pdf",
                "pgoum_garaje-aparcamiento.pdf",
                "pgoum_dotacional administracion publica.pdf",
                "pgoum_dotacional deportivo.pdf",
                "pgoum_dotacional equipamiento.pdf",
                "pgoum_dotacional infraestructural.pdf",
                "pgoum_dotacional servicios publicos.pdf",
                "pgoum_dotacional transporte.pdf",
                "pgoum_dotacional via publica.pdf",
                "pgoum_dotacional zona verde.pdf"
            ]
        }
    
    def validate_normative_structure(self) -> Dict[str, Any]:
        """
        Validar estructura de normativa.
        
        Returns:
            Estado de la estructura de normativa
        """
        try:
            status = {
                "valid": True,
                "missing_files": [],
                "extra_files": [],
                "structure_ok": True,
                "total_files": 0,
                "categories": {}
            }
            
            # Verificar estructura básica
            for category, subcategories in self.expected_structure.items():
                category_path = self.normative_path / category
                if not category_path.exists():
                    status["missing_files"].append(f"Categoría faltante: {category}")
                    status["valid"] = False
                    continue
                
                category_info = {
                    "exists": True,
                    "files": [],
                    "missing_files": [],
                    "extra_files": []
                }
                
                if isinstance(subcategories, dict):
                    # Documentos básicos y de apoyo
                    for subcategory, expected_files in subcategories.items():
                        subcategory_path = category_path / subcategory
                        if subcategory_path.exists():
                            actual_files = [f.name for f in subcategory_path.iterdir() if f.is_file()]
                            category_info["files"].extend(actual_files)
                            status["total_files"] += len(actual_files)
                            
                            # Verificar archivos esperados
                            for expected_file in expected_files:
                                if expected_file not in actual_files:
                                    category_info["missing_files"].append(f"{subcategory}/{expected_file}")
                                    status["missing_files"].append(f"{category}/{subcategory}/{expected_file}")
                                    status["valid"] = False
                        else:
                            category_info["missing_files"].extend([f"{subcategory}/{f}" for f in expected_files])
                            status["missing_files"].extend([f"{category}/{subcategory}/{f}" for f in expected_files])
                            status["valid"] = False
                else:
                    # PGOUM
                    actual_files = [f.name for f in category_path.iterdir() if f.is_file()]
                    category_info["files"] = actual_files
                    status["total_files"] += len(actual_files)
                    
                    # Verificar archivos esperados
                    for expected_file in subcategories:
                        if expected_file not in actual_files:
                            category_info["missing_files"].append(expected_file)
                            status["missing_files"].append(f"{category}/{expected_file}")
                            status["valid"] = False
                
                status["categories"][category] = category_info
            
            logger.info(f"Estructura de normativa validada: {status['total_files']} archivos")
            return status
            
        except Exception as e:
            logger.error(f"Error validando estructura de normativa: {e}")
            return {
                "valid": False,
                "error": str(e),
                "missing_files": [],
                "extra_files": [],
                "structure_ok": False,
                "total_files": 0,
                "categories": {}
            }
    
    def upload_normative_zip(self, zip_file: UploadFile) -> Dict[str, Any]:
        """
        Subir archivo ZIP con normativa.
        
        Args:
            zip_file: Archivo ZIP con normativa
            
        Returns:
            Resultado de la subida
        """
        try:
            # Crear directorio temporal
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                zip_path = temp_path / zip_file.filename
                
                # Guardar archivo ZIP
                with open(zip_path, "wb") as f:
                    content = zip_file.file.read()
                    f.write(content)
                
                # Extraer ZIP
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_path)
                
                # Verificar estructura extraída
                extracted_path = temp_path / "Normativa"
                if not extracted_path.exists():
                    # Buscar carpeta Normativa en subdirectorios
                    for item in temp_path.iterdir():
                        if item.is_dir() and "normativa" in item.name.lower():
                            extracted_path = item
                            break
                
                if not extracted_path.exists():
                    raise HTTPException(status_code=400, detail="No se encontró carpeta Normativa en el ZIP")
                
                # Copiar archivos a la carpeta de normativa
                copied_files = []
                for root, dirs, files in os.walk(extracted_path):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            src_path = Path(root) / file
                            rel_path = src_path.relative_to(extracted_path)
                            dst_path = self.normative_path / rel_path
                            
                            # Crear directorio de destino
                            dst_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            # Copiar archivo
                            shutil.copy2(src_path, dst_path)
                            copied_files.append(str(rel_path))
                
                logger.info(f"Normativa subida: {len(copied_files)} archivos")
                
                # Validar estructura después de la subida
                validation = self.validate_normative_structure()
                
                return {
                    "status": "success",
                    "uploaded_files": len(copied_files),
                    "files": copied_files,
                    "validation": validation,
                    "message": f"Normativa subida exitosamente: {len(copied_files)} archivos"
                }
                
        except Exception as e:
            logger.error(f"Error subiendo normativa: {e}")
            raise HTTPException(status_code=500, detail=f"Error subiendo normativa: {str(e)}")
    
    def get_normative_status(self) -> Dict[str, Any]:
        """
        Obtener estado actual de la normativa.
        
        Returns:
            Estado de la normativa
        """
        try:
            validation = self.validate_normative_structure()
            
            # Obtener información adicional
            total_size = 0
            file_details = []
            
            for root, dirs, files in os.walk(self.normative_path):
                for file in files:
                    file_path = Path(root) / file
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    
                    rel_path = file_path.relative_to(self.normative_path)
                    file_details.append({
                        "path": str(rel_path),
                        "size": file_size,
                        "size_mb": round(file_size / (1024 * 1024), 2)
                    })
            
            return {
                "validation": validation,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_details": file_details,
                "normative_path": str(self.normative_path.absolute())
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de normativa: {e}")
            raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")

# Instancia global
normativa_manager = NormativaUploadManager()

@normativa_upload_router.post("/upload-zip")
async def upload_normative_zip(zip_file: UploadFile = File(...)):
    """
    Subir archivo ZIP con normativa Madrid.
    
    El ZIP debe contener una carpeta 'Normativa' con la estructura:
    - DOCUMENTOS BASICOS/
      - DBHE/, DBHR/, DBHS/, DBSE/, DBSI/, DBSUA/
    - DOCUMENTOS DE APOYO/
      - DBHE/, DBHR/, DBSI/, DBSUA/
    - PGOUM/
      - Archivos pgoum_*.pdf
    """
    try:
        if not zip_file.filename.lower().endswith('.zip'):
            raise HTTPException(status_code=400, detail="El archivo debe ser un ZIP")
        
        result = normativa_manager.upload_normative_zip(zip_file)
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en upload de normativa: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@normativa_upload_router.get("/status")
async def get_normative_status():
    """
    Obtener estado actual de la normativa.
    """
    try:
        status = normativa_manager.get_normative_status()
        return JSONResponse(content=status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estado de normativa: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@normativa_upload_router.get("/validate")
async def validate_normative_structure():
    """
    Validar estructura de normativa.
    """
    try:
        validation = normativa_manager.validate_normative_structure()
        return JSONResponse(content=validation)
        
    except Exception as e:
        logger.error(f"Error validando normativa: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@normativa_upload_router.post("/reset")
async def reset_normative_structure():
    """
    Resetear estructura de normativa (eliminar archivos existentes).
    """
    try:
        # Crear backup de la normativa actual
        backup_path = self.normative_path.parent / "Normativa_backup"
        if self.normative_path.exists():
            shutil.move(str(self.normative_path), str(backup_path))
        
        # Recrear directorio vacío
        self.normative_path.mkdir(exist_ok=True)
        
        logger.info("Estructura de normativa reseteada")
        return JSONResponse(content={
            "status": "success",
            "message": "Estructura de normativa reseteada",
            "backup_created": str(backup_path)
        })
        
    except Exception as e:
        logger.error(f"Error reseteando normativa: {e}")
        raise HTTPException(status_code=500, detail=str(e))
