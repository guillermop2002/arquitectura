"""
Endpoints para subir archivos de documentos (memorias y planos).
"""

import logging
import os
import uuid
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Router para endpoints de upload de archivos
file_upload_router = APIRouter(prefix="/api/madrid/upload", tags=["File Upload"])

class FileUploadResponse(BaseModel):
    status: str
    uploaded_files: List[Dict[str, Any]]
    project_id: str
    message: str

class FileUploadManager:
    """Gestor de subida de archivos de documentos."""
    
    def __init__(self, upload_path: str = "uploads"):
        """
        Inicializar el gestor de uploads.
        
        Args:
            upload_path: Ruta donde se guardarán los archivos
        """
        self.upload_path = Path(upload_path)
        self.upload_path.mkdir(exist_ok=True)
        
        logger.info(f"FileUploadManager inicializado - Ruta: {self.upload_path}")
    
    async def upload_files(self, 
                          memoria_files: List[UploadFile] = None,
                          plano_files: List[UploadFile] = None,
                          project_id: str = None) -> Dict[str, Any]:
        """
        Subir archivos de memoria y planos.
        
        Args:
            memoria_files: Archivos de memoria
            plano_files: Archivos de planos
            project_id: ID del proyecto
            
        Returns:
            Resultado de la subida
        """
        try:
            if not project_id:
                project_id = f"project_{uuid.uuid4().hex[:8]}"
            
            # Crear directorio del proyecto
            project_dir = self.upload_path / project_id
            project_dir.mkdir(exist_ok=True)
            
            uploaded_files = []
            
            # Procesar archivos de memoria
            if memoria_files:
                for file in memoria_files:
                    if file.filename and file.filename.lower().endswith('.pdf'):
                        file_path = project_dir / f"memoria_{file.filename}"
                        content = await file.read()
                        
                        with open(file_path, 'wb') as f:
                            f.write(content)
                        
                        uploaded_files.append({
                            'filename': file.filename,
                            'type': 'memoria',
                            'path': str(file_path),
                            'size': len(content)
                        })
                        
                        logger.info(f"Archivo de memoria subido: {file.filename}")
            
            # Procesar archivos de planos
            if plano_files:
                for file in plano_files:
                    if file.filename and file.filename.lower().endswith('.pdf'):
                        file_path = project_dir / f"plano_{file.filename}"
                        content = await file.read()
                        
                        with open(file_path, 'wb') as f:
                            f.write(content)
                        
                        uploaded_files.append({
                            'filename': file.filename,
                            'type': 'plano',
                            'path': str(file_path),
                            'size': len(content)
                        })
                        
                        logger.info(f"Archivo de plano subido: {file.filename}")
            
            return {
                'status': 'success',
                'uploaded_files': uploaded_files,
                'project_id': project_id,
                'message': f'Subidos {len(uploaded_files)} archivos correctamente'
            }
            
        except Exception as e:
            logger.error(f"Error subiendo archivos: {e}")
            raise HTTPException(status_code=500, detail=f"Error subiendo archivos: {str(e)}")
    
    def get_uploaded_files(self, project_id: str) -> Dict[str, Any]:
        """
        Obtener archivos subidos para un proyecto.
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            Lista de archivos subidos
        """
        try:
            project_dir = self.upload_path / project_id
            
            if not project_dir.exists():
                return {
                    'status': 'success',
                    'files': [],
                    'message': 'No hay archivos subidos para este proyecto'
                }
            
            files = []
            for file_path in project_dir.glob("*.pdf"):
                files.append({
                    'filename': file_path.name,
                    'path': str(file_path),
                    'size': file_path.stat().st_size,
                    'type': 'memoria' if file_path.name.startswith('memoria_') else 'plano'
                })
            
            return {
                'status': 'success',
                'files': files,
                'project_id': project_id,
                'message': f'Encontrados {len(files)} archivos'
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo archivos: {e}")
            raise HTTPException(status_code=500, detail=f"Error obteniendo archivos: {str(e)}")

# Instancia global
file_upload_manager = FileUploadManager()

@file_upload_router.post("/documents", response_model=FileUploadResponse)
async def upload_documents(
    memoria_files: List[UploadFile] = File(default=[], description="Archivos de memoria descriptiva"),
    plano_files: List[UploadFile] = File(default=[], description="Archivos de planos arquitectónicos"),
    project_id: str = Form(default="", description="ID del proyecto")
):
    """
    Subir archivos de documentos (memorias y planos).
    
    Args:
        memoria_files: Archivos de memoria descriptiva
        plano_files: Archivos de planos arquitectónicos
        project_id: ID del proyecto (opcional)
        
    Returns:
        Resultado de la subida
    """
    try:
        if not memoria_files and not plano_files:
            raise HTTPException(status_code=400, detail="No se proporcionaron archivos")
        
        result = await file_upload_manager.upload_files(
            memoria_files=memoria_files,
            plano_files=plano_files,
            project_id=project_id
        )
        
        return FileUploadResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en upload de documentos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@file_upload_router.get("/documents/{project_id}")
async def get_uploaded_documents(project_id: str):
    """
    Obtener archivos subidos para un proyecto.
    
    Args:
        project_id: ID del proyecto
        
    Returns:
        Lista de archivos subidos
    """
    try:
        result = file_upload_manager.get_uploaded_files(project_id)
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo documentos: {e}")
        raise HTTPException(status_code=500, detail=str(e))
