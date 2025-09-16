"""
Enhanced main endpoints that integrate all verification capabilities.
"""

import os
import logging
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from .integrated_verification_system import IntegratedVerificationSystem
from .config import get_config
from .logging_config import get_logger

logger = get_logger(__name__)

class EnhancedMainEndpoints:
    """Enhanced main endpoints with integrated verification capabilities."""
    
    def __init__(self, app: FastAPI):
        """Initialize enhanced endpoints."""
        self.app = app
        self.config = get_config()
        self.verification_system = IntegratedVerificationSystem()
        
        # Add enhanced endpoints
        self._add_enhanced_endpoints()
        
        logger.info("Enhanced main endpoints initialized")
    
    def _add_enhanced_endpoints(self):
        """Add enhanced endpoints to the FastAPI app."""
        
        @self.app.post("/verify-comprehensive")
        async def verify_comprehensive(
            background_tasks: BackgroundTasks,
            files: List[UploadFile] = File(...),
            is_existing_building: bool = Form(False),
            include_plan_analysis: bool = Form(True),
            include_cross_validation: bool = Form(True)
        ):
            """
            Comprehensive verification using all available methods.
            Combines OCR, AI, Computer Vision, and NLP analysis.
            """
            try:
                # Validate files
                if not files or len(files) > self.config.file.max_files:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Maximum {self.config.file.max_files} files allowed"
                    )
                
                # Generate job ID
                job_id = str(uuid.uuid4())
                
                # Save uploaded files
                saved_files = []
                for file in files:
                    if file.filename and file.filename.lower().endswith('.pdf'):
                        file_path = Path(self.config.file.upload_folder) / f"{job_id}_{file.filename}"
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(file_path, "wb") as buffer:
                            content = await file.read()
                            buffer.write(content)
                        
                        saved_files.append(str(file_path))
                
                if not saved_files:
                    raise HTTPException(status_code=400, detail="No valid PDF files uploaded")
                
                # Perform comprehensive verification
                verification_results = self.verification_system.verify_project_comprehensive(
                    saved_files, is_existing_building
                )
                
                # Save results
                results_path = Path(self.config.file.upload_folder) / f"{job_id}_results.json"
                self.verification_system.export_verification_results(
                    verification_results, str(results_path)
                )
                
                # Clean up files in background
                background_tasks.add_task(self._cleanup_files, saved_files)
                
                return {
                    "job_id": job_id,
                    "status": "success",
                    "verification_results": verification_results,
                    "files_processed": len(saved_files),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in comprehensive verification: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/analyze-plans-only")
        async def analyze_plans_only(
            files: List[UploadFile] = File(...)
        ):
            """
            Analyze only plan files using computer vision.
            """
            try:
                # Validate files
                if not files:
                    raise HTTPException(status_code=400, detail="No files uploaded")
                
                # Save uploaded files
                saved_files = []
                for file in files:
                    if file.filename and file.filename.lower().endswith('.pdf'):
                        file_path = Path(self.config.file.upload_folder) / f"temp_{uuid.uuid4()}_{file.filename}"
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(file_path, "wb") as buffer:
                            content = await file.read()
                            buffer.write(content)
                        
                        saved_files.append(str(file_path))
                
                if not saved_files:
                    raise HTTPException(status_code=400, detail="No valid PDF files uploaded")
                
                # Analyze plans
                plan_analysis = self.verification_system._analyze_plans(saved_files, {})
                
                # Clean up files
                for file_path in saved_files:
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
                
                return {
                    "status": "success",
                    "plan_analysis": plan_analysis,
                    "files_analyzed": len(saved_files)
                }
                
            except Exception as e:
                logger.error(f"Error in plan analysis: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/verification/{job_id}/results")
        async def get_verification_results(job_id: str):
            """
            Get verification results for a specific job.
            """
            try:
                results_path = Path(self.config.file.upload_folder) / f"{job_id}_results.json"
                
                if not results_path.exists():
                    raise HTTPException(status_code=404, detail="Results not found")
                
                import json
                with open(results_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                
                return results
                
            except Exception as e:
                logger.error(f"Error getting verification results: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/verification/{job_id}/summary")
        async def get_verification_summary(job_id: str):
            """
            Get a summary of verification results.
            """
            try:
                results_path = Path(self.config.file.upload_folder) / f"{job_id}_results.json"
                
                if not results_path.exists():
                    raise HTTPException(status_code=404, detail="Results not found")
                
                import json
                with open(results_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                
                # Extract summary information
                summary = {
                    "job_id": job_id,
                    "success": results.get("success", False),
                    "files_processed": results.get("files_processed", 0),
                    "total_pages": results.get("integrated_analysis", {}).get("total_pages_processed", 0),
                    "total_elements": results.get("integrated_analysis", {}).get("total_elements_detected", 0),
                    "total_rooms": results.get("integrated_analysis", {}).get("total_rooms_detected", 0),
                    "total_issues": results.get("compliance_results", {}).get("total_issues", 0),
                    "high_severity_issues": results.get("compliance_results", {}).get("high_severity_issues", 0),
                    "medium_severity_issues": results.get("compliance_results", {}).get("medium_severity_issues", 0),
                    "low_severity_issues": results.get("compliance_results", {}).get("low_severity_issues", 0),
                    "overall_confidence": results.get("integrated_analysis", {}).get("confidence_scores", {}).get("overall_confidence", 0.0),
                    "questions_count": len(results.get("questions", [])),
                    "recommendations_count": len(results.get("recommendations", [])),
                    "timestamp": results.get("verification_timestamp", "")
                }
                
                return summary
                
            except Exception as e:
                logger.error(f"Error getting verification summary: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/verification/{job_id}/issues")
        async def get_verification_issues(job_id: str, severity: Optional[str] = None):
            """
            Get verification issues, optionally filtered by severity.
            """
            try:
                results_path = Path(self.config.file.upload_folder) / f"{job_id}_results.json"
                
                if not results_path.exists():
                    raise HTTPException(status_code=404, detail="Results not found")
                
                import json
                with open(results_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                
                # Extract all issues
                all_issues = []
                
                # Compliance issues
                compliance_results = results.get("compliance_results", {})
                if "issues" in compliance_results:
                    all_issues.extend(compliance_results["issues"])
                
                # Plan-based issues
                plan_analysis = results.get("plan_analysis", {})
                for plan_data in plan_analysis.values():
                    if isinstance(plan_data, dict) and "compliance_issues" in plan_data:
                        all_issues.extend(plan_data["compliance_issues"])
                
                # Cross-validation issues
                integrated_analysis = results.get("integrated_analysis", {})
                cross_validation_issues = integrated_analysis.get("cross_validation_issues", [])
                all_issues.extend(cross_validation_issues)
                
                # Filter by severity if specified
                if severity:
                    all_issues = [issue for issue in all_issues if issue.get("severity", "").lower() == severity.lower()]
                
                return {
                    "job_id": job_id,
                    "total_issues": len(all_issues),
                    "issues": all_issues,
                    "severity_filter": severity
                }
                
            except Exception as e:
                logger.error(f"Error getting verification issues: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/verification/{job_id}/recommendations")
        async def get_verification_recommendations(job_id: str):
            """
            Get verification recommendations.
            """
            try:
                results_path = Path(self.config.file.upload_folder) / f"{job_id}_results.json"
                
                if not results_path.exists():
                    raise HTTPException(status_code=404, detail="Results not found")
                
                import json
                with open(results_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                
                recommendations = results.get("recommendations", [])
                
                return {
                    "job_id": job_id,
                    "total_recommendations": len(recommendations),
                    "recommendations": recommendations
                }
                
            except Exception as e:
                logger.error(f"Error getting verification recommendations: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/verification/{job_id}/questions")
        async def get_verification_questions(job_id: str):
            """
            Get verification questions for user clarification.
            """
            try:
                results_path = Path(self.config.file.upload_folder) / f"{job_id}_results.json"
                
                if not results_path.exists():
                    raise HTTPException(status_code=404, detail="Results not found")
                
                import json
                with open(results_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                
                questions = results.get("questions", [])
                
                return {
                    "job_id": job_id,
                    "total_questions": len(questions),
                    "questions": questions
                }
                
            except Exception as e:
                logger.error(f"Error getting verification questions: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/verification/{job_id}/answer-questions")
        async def answer_verification_questions(
            job_id: str,
            answers: Dict[str, str]
        ):
            """
            Submit answers to verification questions.
            """
            try:
                results_path = Path(self.config.file.upload_folder) / f"{job_id}_results.json"
                
                if not results_path.exists():
                    raise HTTPException(status_code=404, detail="Results not found")
                
                import json
                with open(results_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                
                # Process answers (this would integrate with the existing answer processing)
                # For now, just store the answers
                results["user_answers"] = answers
                results["answers_timestamp"] = datetime.now().isoformat()
                
                # Save updated results
                with open(results_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False, default=str)
                
                return {
                    "job_id": job_id,
                    "status": "success",
                    "answers_received": len(answers),
                    "timestamp": results["answers_timestamp"]
                }
                
            except Exception as e:
                logger.error(f"Error processing answers: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _cleanup_files(self, file_paths: List[str]):
        """Clean up temporary files."""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Error cleaning up file {file_path}: {e}")
