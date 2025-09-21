"""
Sistema de logging detallado para monitorear el proceso de análisis.
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

class DetailedLogger:
    """Logger detallado para el proceso de análisis."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, mode=0o755)
        
        # Configurar logger principal
        self.logger = logging.getLogger("detailed_analysis")
        self.logger.setLevel(logging.DEBUG)
        
        # Handler para archivo (con manejo de errores)
        try:
            file_handler = logging.FileHandler(self.log_dir / "detailed_analysis.log")
            file_handler.setLevel(logging.DEBUG)
        except PermissionError:
            # Si no se puede escribir al archivo, usar solo consola
            file_handler = None
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formato detallado
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        if file_handler:
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Almacén de eventos
        self.events: List[Dict[str, Any]] = []
        
    def log_event(self, event_type: str, message: str, data: Dict[str, Any] = None, level: str = "INFO"):
        """
        Registra un evento detallado.
        
        Args:
            event_type: Tipo de evento (PDF_PROCESSING, CLASSIFICATION, ANALYSIS, etc.)
            message: Mensaje descriptivo
            data: Datos adicionales
            level: Nivel de log (DEBUG, INFO, WARNING, ERROR)
        """
        timestamp = datetime.now().isoformat()
        
        event = {
            "timestamp": timestamp,
            "event_type": event_type,
            "message": message,
            "level": level,
            "data": data or {}
        }
        
        self.events.append(event)
        
        # Log al archivo
        log_message = f"[{event_type}] {message}"
        if data:
            log_message += f" | Data: {json.dumps(data, indent=2)}"
        
        if level == "DEBUG":
            self.logger.debug(log_message)
        elif level == "INFO":
            self.logger.info(log_message)
        elif level == "WARNING":
            self.logger.warning(log_message)
        elif level == "ERROR":
            self.logger.error(log_message)
    
    def log_pdf_processing(self, filename: str, pages: int, processing_time: float, success: bool):
        """Log específico para procesamiento de PDFs."""
        self.log_event(
            "PDF_PROCESSING",
            f"PDF procesado: {filename}",
            {
                "filename": filename,
                "pages": pages,
                "processing_time_seconds": processing_time,
                "success": success
            },
            "INFO" if success else "ERROR"
        )
    
    def log_classification(self, filename: str, document_type: str, confidence: float, classification_data: Dict):
        """Log específico para clasificación de documentos."""
        self.log_event(
            "DOCUMENT_CLASSIFICATION",
            f"Documento clasificado: {filename} como {document_type}",
            {
                "filename": filename,
                "document_type": document_type,
                "confidence": confidence,
                "classification_data": classification_data
            },
            "INFO"
        )
    
    def log_analysis(self, filename: str, analysis_type: str, findings: List[str], processing_time: float):
        """Log específico para análisis de documentos."""
        self.log_event(
            "DOCUMENT_ANALYSIS",
            f"Análisis completado: {filename}",
            {
                "filename": filename,
                "analysis_type": analysis_type,
                "findings": findings,
                "processing_time_seconds": processing_time
            },
            "INFO"
        )
    
    def log_usage_application(self, floor: str, primary_use: str, secondary_use: str = None, final_use: str = None):
        """Log específico para aplicación de usos."""
        self.log_event(
            "USAGE_APPLICATION",
            f"Uso aplicado a planta {floor}",
            {
                "floor": floor,
                "primary_use": primary_use,
                "secondary_use": secondary_use,
                "final_use": final_use,
                "logic": "secondary_use if secondary_use else primary_use"
            },
            "INFO"
        )
    
    def log_ambiguity_detection(self, ambiguity_type: str, description: str, affected_floors: List[str]):
        """Log específico para detección de ambigüedades."""
        self.log_event(
            "AMBIGUITY_DETECTION",
            f"Ambigüedad detectada: {ambiguity_type}",
            {
                "ambiguity_type": ambiguity_type,
                "description": description,
                "affected_floors": affected_floors
            },
            "WARNING"
        )
    
    def log_compliance_check(self, floor: str, use_type: str, compliance_result: Dict):
        """Log específico para verificación de cumplimiento."""
        self.log_event(
            "COMPLIANCE_CHECK",
            f"Verificación de cumplimiento: {floor} - {use_type}",
            {
                "floor": floor,
                "use_type": use_type,
                "compliance_result": compliance_result
            },
            "INFO"
        )
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen de la sesión actual."""
        if not self.events:
            return {"message": "No hay eventos registrados"}
        
        # Estadísticas por tipo de evento
        event_stats = {}
        for event in self.events:
            event_type = event["event_type"]
            if event_type not in event_stats:
                event_stats[event_type] = {"count": 0, "errors": 0}
            event_stats[event_type]["count"] += 1
            if event["level"] == "ERROR":
                event_stats[event_type]["errors"] += 1
        
        # Tiempo total de procesamiento
        total_time = 0
        for event in self.events:
            if "processing_time_seconds" in event.get("data", {}):
                total_time += event["data"]["processing_time_seconds"]
        
        return {
            "total_events": len(self.events),
            "event_stats": event_stats,
            "total_processing_time_seconds": total_time,
            "session_start": self.events[0]["timestamp"] if self.events else None,
            "session_end": self.events[-1]["timestamp"] if self.events else None,
            "recent_events": self.events[-10:]  # Últimos 10 eventos
        }
    
    def save_session_log(self, session_id: str = None):
        """Guarda el log de la sesión actual."""
        if not session_id:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        log_file = self.log_dir / f"session_{session_id}.json"
        
        session_data = {
            "session_id": session_id,
            "summary": self.get_session_summary(),
            "events": self.events
        }
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Log de sesión guardado: {log_file}")
        return str(log_file)
    
    def clear_session(self):
        """Limpia los eventos de la sesión actual."""
        self.events.clear()
        self.logger.info("Sesión de logging limpiada")

# Instancia global
detailed_logger = DetailedLogger()
