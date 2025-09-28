import uuid
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import aiofiles

class BasicoSessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.sessions_dir = Path("sessions")
        self.sessions_dir.mkdir(exist_ok=True)
    
    def create_session(self, project_name: str) -> str:
        """Crear nueva sesión"""
        session_id = str(uuid.uuid4())[:8]
        
        session_data = {
            "session_id": session_id,
            "project_name": project_name,
            "created_at": datetime.now().isoformat(),
            "status": "created",
            "files": [],
            "phase_results": {}
        }
        
        self.sessions[session_id] = session_data
        self._save_session(session_id)
        return session_id
    
    async def upload_files(self, session_id: str, files: List) -> Dict[str, Any]:
        """Subir archivos a una sesión"""
        if session_id not in self.sessions:
            raise ValueError(f"Sesión {session_id} no encontrada")
        
        session_dir = self.sessions_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        uploaded_files = []
        for file in files:
            file_path = session_dir / file.filename
            
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            file_info = {
                "filename": file.filename,
                "path": str(file_path),
                "size": len(content),
                "uploaded_at": datetime.now().isoformat()
            }
            
            uploaded_files.append(file_info)
            self.sessions[session_id]["files"].append(file_info)
        
        self._save_session(session_id)
        return {"uploaded_files": uploaded_files, "total_files": len(uploaded_files)}
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Obtener datos de sesión"""
        if session_id not in self.sessions:
            raise ValueError(f"Sesión {session_id} no encontrada")
        return self.sessions[session_id]
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtener datos de sesión (alias para compatibilidad)"""
        try:
            return self.get_session(session_id)
        except ValueError:
            return None
    
    def save_phase_result(self, session_id: str, phase: int, result: Dict[str, Any]):
        """Guardar resultado de una fase"""
        if session_id not in self.sessions:
            raise ValueError(f"Sesión {session_id} no encontrada")
        
        if 'phase_results' not in self.sessions[session_id]:
            self.sessions[session_id]['phase_results'] = {}
        
        self.sessions[session_id]['phase_results'][f'fase{phase}'] = result
        self.sessions[session_id]['last_updated'] = datetime.now().isoformat()
        self._save_session(session_id)
    
    def get_phase_results(self, session_id: str) -> Dict[str, Any]:
        """Obtener resultados de todas las fases"""
        session = self.get_session(session_id)
        return session.get('phase_results', {})
    
    def get_complete_results(self, session_id: str) -> Dict[str, Any]:
        """Obtener resultados completos de la sesión"""
        session = self.get_session(session_id)
        return {
            "session_info": {
                "session_id": session["session_id"],
                "project_name": session["project_name"],
                "created_at": session["created_at"],
                "files_count": len(session["files"])
            },
            "phase_results": session.get("phase_results", {}),
            "files": session["files"]
        }
    
    def _save_session(self, session_id: str):
        """Guardar sesión en disco"""
        session_file = self.sessions_dir / f"{session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(self.sessions[session_id], f, indent=2, ensure_ascii=False)
