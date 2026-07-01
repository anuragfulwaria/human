"""
Human Detection Module
Handles YOLO-based person detection
"""

import cv2
import numpy as np
from ultralytics import YOLO
import logging

class HumanDetector:
    """
    Detects humans in video frames using YOLO
    """
    
    def __init__(self, model_path='yolov8n.pt', confidence_threshold=0.5):
        """
        Initialize the detector
        
        Args:
            model_path: Path to YOLO model
            confidence_threshold: Minimum confidence for detection (0-1)
        """
        self.logger = logging.getLogger(__name__)
        self.confidence_threshold = confidence_threshold
        
        try:
            self.logger.info(f"Loading YOLO model: {model_path}")
            self.model = YOLO(model_path)
            self.logger.info("Model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise
        
        # COCO dataset class ID for 'person' is 0
        self.PERSON_CLASS_ID = 0
        
    def detect(self, frame):
        """
        Detect humans in a frame
        
        Args:
            frame: OpenCV image (BGR)
            
        Returns:
            List of detections, each containing:
            {
                'bbox': [x1, y1, x2, y2],
                'confidence': float,
                'center': (cx, cy)
            }
        """
        detections = []
        
        try:
            # Run inference
            results = self.model(frame, verbose=False)
            
            # Process results
            for result in results:
                boxes = result.boxes
                
                for box in boxes:
                    # Get class ID
                    class_id = int(box.cls[0])
                    
                    # Filter for person class only
                    if class_id == self.PERSON_CLASS_ID:
                        confidence = float(box.conf[0])
                        
                        # Apply confidence threshold
                        if confidence >= self.confidence_threshold:
                            # Get bounding box coordinates
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            
                            # Calculate center point
                            center_x = int((x1 + x2) / 2)
                            center_y = int((y1 + y2) / 2)
                            
                            detection = {
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'confidence': confidence,
                                'center': (center_x, center_y)
                            }
                            
                            detections.append(detection)
                            
            self.logger.debug(f"Detected {len(detections)} person(s)")
            
        except Exception as e:
            self.logger.error(f"Detection error: {e}")
            
        return detections
    
    def draw_detections(self, frame, detections):
        """
        Draw bounding boxes on frame
        
        Args:
            frame: OpenCV image
            detections: List of detection dictionaries
            
        Returns:
            Annotated frame
        """
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            confidence = detection['confidence']
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            label = f"Person {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            
            # Background for text
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), (0, 255, 0), -1)
            
            # Text
            cv2.putText(frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            # Draw center point
            cv2.circle(frame, detection['center'], 5, (0, 255, 0), -1)
            
        return frame