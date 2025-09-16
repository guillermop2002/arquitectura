"""
Advanced Plan Analyzer with Computer Vision and Groq AI integration.
Detects architectural elements, builds connectivity graphs, and performs normative analysis.
Optimized for Groq API only - no paid services.
"""

import cv2
import numpy as np
import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import networkx as nx
from PIL import Image
import pdf2image
import pytesseract

# Import Groq AI client
from .ai_client import get_ai_client, AIResponse

logger = logging.getLogger(__name__)

@dataclass
class ArchitecturalElement:
    """Represents an architectural element found in a plan."""
    element_type: str  # 'wall', 'door', 'window', 'room', 'stair', 'elevator', 'furniture'
    coordinates: List[Tuple[int, int]]
    confidence: float
    dimensions: Optional[Dict[str, float]] = None
    properties: Optional[Dict[str, Any]] = None
    page_number: int = 0

@dataclass
class Room:
    """Represents a room with its properties and connections."""
    room_id: str
    room_type: str  # 'dormitorio', 'cocina', 'baño', 'salon', 'pasillo', 'garaje'
    area: float
    center: Tuple[float, float]
    boundaries: List[Tuple[int, int]]
    doors: List[str]  # IDs of connected doors
    windows: List[str]  # IDs of connected windows
    accessibility_features: List[str] = None

class AdvancedPlanAnalyzer:
    """
    Advanced plan analyzer that combines computer vision, Groq AI, and normative analysis.
    Optimized for Groq API only - no external paid services.
    """
    
    def __init__(self):
        """Initialize the analyzer with Groq AI client."""
        self.ai_client = get_ai_client()
        self.logger = logging.getLogger(__name__)
        
        # Element detection parameters
        self.min_contour_area = 100
        self.max_contour_area = 50000
        self.door_width_range = (60, 120)  # pixels
        self.window_width_range = (40, 200)  # pixels
        
        # Room classification using Groq
        self.room_types = [
            'dormitorio', 'cocina', 'baño', 'salon', 'pasillo', 
            'garaje', 'despacho', 'trastero', 'terraza', 'balcon'
        ]
        
        # Architectural element types
        self.element_types = [
            'wall', 'door', 'window', 'room', 'stair', 
            'elevator', 'furniture', 'column', 'beam'
        ]
        
        self.logger.info("AdvancedPlanAnalyzer initialized with Groq AI")
    
    def analyze_plan(self, plan_path: str, project_id: str) -> Dict[str, Any]:
        """
        Analyze a single plan file and extract architectural elements.
        
        Args:
            plan_path: Path to the plan file (PDF or image)
            project_id: Unique project identifier
            
        Returns:
            Dictionary with analysis results
        """
        try:
            self.logger.info(f"Analyzing plan: {plan_path}")
            
            # Convert PDF to images if needed
            if plan_path.lower().endswith('.pdf'):
                images = self._pdf_to_images(plan_path)
            else:
                images = [cv2.imread(plan_path)]
            
            all_elements = []
            all_rooms = []
            connectivity_graph = nx.Graph()
            
            # Process each page
            for page_num, image in enumerate(images):
                if image is None:
                    continue
                    
                # Detect architectural elements
                elements = self._detect_architectural_elements(image, page_num)
                all_elements.extend(elements)
                
                # Detect rooms
                rooms = self._detect_rooms(image, page_num)
                all_rooms.extend(rooms)
                
                # Build connectivity graph
                self._build_connectivity_graph(rooms, elements, connectivity_graph)
            
            # Classify elements using Groq AI
            classified_elements = self._classify_elements_with_groq(all_elements)
            
            # Analyze normative compliance
            compliance_analysis = self._analyze_normative_compliance(classified_elements, all_rooms)
            
            # Generate analysis report
            analysis_result = {
                'project_id': project_id,
                'plan_path': plan_path,
                'total_elements': len(classified_elements),
                'total_rooms': len(all_rooms),
                'elements': [elem.__dict__ for elem in classified_elements],
                'rooms': [room.__dict__ for room in all_rooms],
                'connectivity_graph': self._graph_to_dict(connectivity_graph),
                'compliance_analysis': compliance_analysis,
                'analysis_metadata': {
                    'pages_processed': len(images),
                    'analysis_timestamp': self._get_timestamp(),
                    'ai_model_used': 'groq-llama-3.3-70b'
                }
            }
            
            self.logger.info(f"Plan analysis completed: {len(classified_elements)} elements, {len(all_rooms)} rooms")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Error analyzing plan {plan_path}: {e}")
            return {
                'project_id': project_id,
                'plan_path': plan_path,
                'error': str(e),
                'elements': [],
                'rooms': [],
                'connectivity_graph': {},
                'compliance_analysis': {}
            }
    
    def _pdf_to_images(self, pdf_path: str) -> List[np.ndarray]:
        """Convert PDF to images using pdf2image."""
        try:
            images = pdf2image.convert_from_path(pdf_path, dpi=300)
            return [np.array(img) for img in images]
        except Exception as e:
            self.logger.error(f"Error converting PDF to images: {e}")
            return []
    
    def _detect_architectural_elements(self, image: np.ndarray, page_num: int) -> List[ArchitecturalElement]:
        """Detect architectural elements using computer vision."""
        elements = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if self.min_contour_area < area < self.max_contour_area:
                    # Get bounding rectangle
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Classify element type based on dimensions
                    element_type = self._classify_element_by_dimensions(w, h)
                    
                    if element_type:
                        element = ArchitecturalElement(
                            element_type=element_type,
                            coordinates=[(x, y), (x + w, y + h)],
                            confidence=0.7,  # Basic confidence
                            dimensions={'width': w, 'height': h},
                            page_number=page_num
                        )
                        elements.append(element)
            
            return elements
            
        except Exception as e:
            self.logger.error(f"Error detecting architectural elements: {e}")
            return []
    
    def _classify_element_by_dimensions(self, width: int, height: int) -> Optional[str]:
        """Classify element type based on dimensions."""
        aspect_ratio = width / height if height > 0 else 0
        
        # Door detection
        if self.door_width_range[0] <= width <= self.door_width_range[1] and 10 <= height <= 50:
            return 'door'
        
        # Window detection
        if self.window_width_range[0] <= width <= self.window_width_range[1] and 10 <= height <= 30:
            return 'window'
        
        # Wall detection
        if width > 100 and height > 20 and aspect_ratio > 3:
            return 'wall'
        
        # Column detection
        if 20 <= width <= 60 and 20 <= height <= 60 and 0.5 <= aspect_ratio <= 2:
            return 'column'
        
        return None
    
    def _detect_rooms(self, image: np.ndarray, page_num: int) -> List[Room]:
        """Detect rooms using computer vision."""
        rooms = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Threshold to get binary image
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
            
            # Find contours (potential rooms)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            room_id = 0
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # Minimum room area
                    # Get bounding rectangle
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Calculate center
                    center = (x + w/2, y + h/2)
                    
                    # Create room
                    room = Room(
                        room_id=f"room_{page_num}_{room_id}",
                        room_type="unknown",  # Will be classified by AI
                        area=area,
                        center=center,
                        boundaries=[(x, y), (x + w, y + h)],
                        doors=[],
                        windows=[]
                    )
                    rooms.append(room)
                    room_id += 1
            
            return rooms
            
        except Exception as e:
            self.logger.error(f"Error detecting rooms: {e}")
            return []
    
    def _build_connectivity_graph(self, rooms: List[Room], elements: List[ArchitecturalElement], graph: nx.Graph):
        """Build connectivity graph between rooms and elements."""
        try:
            # Add room nodes
            for room in rooms:
                graph.add_node(room.room_id, type='room', room_type=room.room_type)
            
            # Add element nodes
            for element in elements:
                element_id = f"{element.element_type}_{len(graph.nodes)}"
                graph.add_node(element_id, type=element.element_type, confidence=element.confidence)
            
            # Add edges based on spatial proximity
            for room in rooms:
                for element in elements:
                    if self._is_element_in_room(element, room):
                        element_id = f"{element.element_type}_{elements.index(element)}"
                        graph.add_edge(room.room_id, element_id, relationship='contains')
            
        except Exception as e:
            self.logger.error(f"Error building connectivity graph: {e}")
    
    def _is_element_in_room(self, element: ArchitecturalElement, room: Room) -> bool:
        """Check if an element is inside a room."""
        try:
            element_center = (
                (element.coordinates[0][0] + element.coordinates[1][0]) / 2,
                (element.coordinates[0][1] + element.coordinates[1][1]) / 2
            )
            
            room_x1, room_y1 = room.boundaries[0]
            room_x2, room_y2 = room.boundaries[1]
            
            return (room_x1 <= element_center[0] <= room_x2 and 
                    room_y1 <= element_center[1] <= room_y2)
        except:
            return False
    
    def _classify_elements_with_groq(self, elements: List[ArchitecturalElement]) -> List[ArchitecturalElement]:
        """Classify architectural elements using Groq AI."""
        if not self.ai_client.is_available():
            self.logger.warning("Groq AI client not available, using basic classification")
            return elements
        
        try:
            # Prepare context for AI classification
            context = self._prepare_classification_context(elements)
            
            # Create prompt for Groq
            prompt = f"""
            Eres un experto arquitecto. Clasifica los siguientes elementos arquitectónicos detectados en un plano:
            
            {context}
            
            Para cada elemento, determina:
            1. Tipo de elemento (wall, door, window, room, stair, elevator, furniture, column, beam)
            2. Confianza (0.0-1.0)
            3. Propiedades adicionales si las hay
            
            Responde en formato JSON:
            {{
                "elements": [
                    {{
                        "index": 0,
                        "element_type": "door",
                        "confidence": 0.9,
                        "properties": {{"width": 80, "height": 15}}
                    }}
                ]
            }}
            """
            
            # Get AI response
            response = self.ai_client.generate_response(prompt)
            
            if response.success:
                # Parse AI response
                ai_classification = json.loads(response.content)
                
                # Update elements with AI classification
                for ai_elem in ai_classification.get('elements', []):
                    idx = ai_elem.get('index', 0)
                    if 0 <= idx < len(elements):
                        elements[idx].element_type = ai_elem.get('element_type', elements[idx].element_type)
                        elements[idx].confidence = ai_elem.get('confidence', elements[idx].confidence)
                        elements[idx].properties = ai_elem.get('properties', elements[idx].properties)
            
            return elements
            
        except Exception as e:
            self.logger.error(f"Error classifying elements with Groq: {e}")
            return elements
    
    def _prepare_classification_context(self, elements: List[ArchitecturalElement]) -> str:
        """Prepare context for AI classification."""
        context_parts = []
        
        for i, element in enumerate(elements):
            context_parts.append(f"""
            Elemento {i}:
            - Tipo actual: {element.element_type}
            - Dimensiones: {element.dimensions}
            - Coordenadas: {element.coordinates}
            - Página: {element.page_number}
            """)
        
        return "\n".join(context_parts)
    
    def _analyze_normative_compliance(self, elements: List[ArchitecturalElement], rooms: List[Room]) -> Dict[str, Any]:
        """Analyze normative compliance using Groq AI."""
        if not self.ai_client.is_available():
            return {"error": "AI client not available"}
        
        try:
            # Prepare compliance analysis context
            context = self._prepare_compliance_context(elements, rooms)
            
            # Create prompt for compliance analysis
            prompt = f"""
            Eres un experto en normativa de construcción española (CTE). Analiza el cumplimiento normativo de los siguientes elementos:
            
            {context}
            
            Verifica:
            1. Cumplimiento de DB-SI (Seguridad en caso de incendio)
            2. Cumplimiento de DB-SUA (Seguridad de utilización y accesibilidad)
            3. Cumplimiento de DB-HE (Ahorro de energía)
            4. Cumplimiento de DB-HR (Protección frente al ruido)
            
            Responde en formato JSON:
            {{
                "compliance_issues": [
                    {{
                        "element_id": "door_1",
                        "regulation": "DB-SUA",
                        "issue": "Ancho insuficiente para accesibilidad",
                        "severity": "HIGH",
                        "recommendation": "Aumentar ancho a mínimo 80cm"
                    }}
                ],
                "overall_compliance": 0.85,
                "summary": "Se detectaron 3 incumplimientos menores"
            }}
            """
            
            # Get AI response
            response = self.ai_client.generate_response(prompt)
            
            if response.success:
                return json.loads(response.content)
            else:
                return {"error": "Failed to get AI response"}
                
        except Exception as e:
            self.logger.error(f"Error analyzing compliance: {e}")
            return {"error": str(e)}
    
    def _prepare_compliance_context(self, elements: List[ArchitecturalElement], rooms: List[Room]) -> str:
        """Prepare context for compliance analysis."""
        context_parts = []
        
        # Add elements context
        context_parts.append("ELEMENTOS ARQUITECTÓNICOS:")
        for element in elements:
            context_parts.append(f"- {element.element_type}: {element.dimensions}")
        
        # Add rooms context
        context_parts.append("\nHABITACIONES:")
        for room in rooms:
            context_parts.append(f"- {room.room_type}: {room.area:.2f} m²")
        
        return "\n".join(context_parts)
    
    def _graph_to_dict(self, graph: nx.Graph) -> Dict[str, Any]:
        """Convert NetworkX graph to dictionary."""
        try:
            return {
                'nodes': list(graph.nodes(data=True)),
                'edges': list(graph.edges(data=True))
            }
        except Exception as e:
            self.logger.error(f"Error converting graph to dict: {e}")
            return {'nodes': [], 'edges': []}
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def analyze_multiple_plans(self, plan_paths: List[str], project_id: str) -> Dict[str, Any]:
        """
        Analyze multiple plan files for a project.
        
        Args:
            plan_paths: List of paths to plan files
            project_id: Unique project identifier
            
        Returns:
            Dictionary with combined analysis results
        """
        try:
            all_results = []
            combined_elements = []
            combined_rooms = []
            combined_graph = nx.Graph()
            
            for plan_path in plan_paths:
                result = self.analyze_plan(plan_path, project_id)
                all_results.append(result)
                
                # Combine results
                combined_elements.extend(result.get('elements', []))
                combined_rooms.extend(result.get('rooms', []))
                
                # Merge graphs
                if 'connectivity_graph' in result:
                    graph_data = result['connectivity_graph']
                    for node in graph_data.get('nodes', []):
                        combined_graph.add_node(node[0], **node[1])
                    for edge in graph_data.get('edges', []):
                        combined_graph.add_edge(edge[0], edge[1], **edge[2])
            
            # Generate combined analysis
            combined_analysis = {
                'project_id': project_id,
                'total_plans': len(plan_paths),
                'total_elements': len(combined_elements),
                'total_rooms': len(combined_rooms),
                'elements': combined_elements,
                'rooms': combined_rooms,
                'connectivity_graph': self._graph_to_dict(combined_graph),
                'individual_results': all_results,
                'analysis_metadata': {
                    'analysis_timestamp': self._get_timestamp(),
                    'ai_model_used': 'groq-llama-3.3-70b',
                    'total_pages_processed': sum(r.get('analysis_metadata', {}).get('pages_processed', 0) for r in all_results)
                }
            }
            
            return combined_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing multiple plans: {e}")
            return {
                'project_id': project_id,
                'error': str(e),
                'elements': [],
                'rooms': [],
                'connectivity_graph': {}
            }
