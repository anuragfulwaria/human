import cv2
import yaml
import logging
from logging.handlers import RotatingFileHandler
import time
import os
import sys
from datetime import datetime

from detector import HumanDetector
from zone_manager import ZoneManager
from alert_system import AlertSystem


class SafetySystem:
    """
    Main safety monitoring system
    """
    
    def __init__(self, config_path='config/config.yaml'):
        """
        Initialize the safety system
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Setup logging
        self._setup_logging()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 60)
        self.logger.info("Manufacturing Safety System Starting")
        self.logger.info("=" * 60)
        
        # Initialize components
        self.detector = None
        self.zone_manager = None
        self.alert_system = None
        self.camera = None
        
        # Performance metrics
        self.frame_count = 0
        self.fps = 0
        self.start_time = time.time()
        
        # System state
        self.running = False
        
    def _load_config(self, config_path):
        """Load YAML configuration"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)
    
    def _setup_logging(self):
        """Configure logging system"""
        log_config = self.config.get('logging', {})
        log_file = log_config.get('file', 'logs/safety_system.log')
        log_level = log_config.get('level', 'INFO')
        
        # Create logs directory
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Configure root logger
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, log_level))
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=log_config.get('max_bytes', 10485760),
            backupCount=log_config.get('backup_count', 5)
        )
        file_handler.setLevel(getattr(logging, log_level))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    def initialize(self):
        """Initialize all system components"""
        try:
            # Initialize detector
            self.logger.info("Initializing human detector...")
            detection_config = self.config['detection']
            self.detector = HumanDetector(
                model_path=detection_config['model'],
                confidence_threshold=detection_config['confidence_threshold']
            )
            
            # Initialize zone manager
            self.logger.info("Initializing zone manager...")
            zone_config = self.config['restricted_zone']
            self.zone_manager = ZoneManager(
                zone_points=zone_config['points'],
                zone_color=tuple(zone_config['color']),
                thickness=zone_config['thickness']
            )
            
            # Initialize alert system
            self.logger.info("Initializing alert system...")
            self.alert_system = AlertSystem(self.config['alerts'])
            
            # Initialize camera
            self.logger.info("Initializing camera...")
            self._initialize_camera()
            
            self.logger.info("All systems initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False
    
    def _initialize_camera(self):
        """Initialize camera connection"""
        camera_config = self.config['camera']
        source = camera_config['source']
        
        # Try to open camera
        max_retries = 5
        for attempt in range(max_retries):
            self.logger.info(f"Connecting to camera (attempt {attempt + 1}/{max_retries})...")
            
            self.camera = cv2.VideoCapture(source)
            
            if self.camera.isOpened():
                # Set camera properties
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, camera_config['width'])
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_config['height'])
                self.camera.set(cv2.CAP_PROP_FPS, camera_config['fps'])
                
                self.logger.info("Camera connected successfully")
                return True
            
            time.sleep(2)
        
        raise Exception("Failed to connect to camera")
    
    def process_frame(self, frame):
        """
        Process a single frame
        
        Args:
            frame: OpenCV image
            
        Returns:
            Processed frame
        """
        display_frame = frame.copy()
        
        # Detect humans
        detections = self.detector.detect(frame)
        
        # Check for violations
        violations = self.zone_manager.check_violations(detections)
        
        # Draw zone
        display_frame = self.zone_manager.draw_zone(
            display_frame, 
            violations_detected=len(violations) > 0
        )
        
        # Draw detections
        if self.config['display']['show_detection_boxes']:
            display_frame = self.detector.draw_detections(display_frame, detections)
        
        # Handle violations
        if violations:
            display_frame = self.zone_manager.draw_violations(display_frame, violations)
            self.alert_system.trigger_alert(display_frame, violations)
        else:
            self.alert_system.reset()
        
        # Add system info
        self._add_system_info(display_frame, len(detections), len(violations))
        
        return display_frame
    
    def _add_system_info(self, frame, num_detections, num_violations):
        """Add system information overlay"""
        display_config = self.config['display']
        
        # System status
        status_color = (0, 0, 255) if num_violations > 0 else (0, 255, 0)
        status_text = "⚠ VIOLATION" if num_violations > 0 else "✓ SAFE"
        
        cv2.rectangle(frame, (10, 10), (300, 120), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (300, 120), status_color, 2)
        
        cv2.putText(frame, f"Status: {status_text}", (20, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
        cv2.putText(frame, f"Persons Detected: {num_detections}", (20, 65), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Violations: {num_violations}", (20, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # FPS
        if display_config['show_fps']:
            cv2.putText(frame, f"FPS: {self.fps:.1f}", (20, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (frame.shape[1] - 250, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    def calculate_fps(self):
        """Calculate current FPS"""
        self.frame_count += 1
        elapsed_time = time.time() - self.start_time
        
        if elapsed_time > 1.0:
            self.fps = self.frame_count / elapsed_time
            self.frame_count = 0
            self.start_time = time.time()
    
    def run(self):
        """Main system loop"""
        if not self.initialize():
            self.logger.error("System initialization failed")
            return
        
        self.running = True
        self.logger.info("System running - Press 'Q' to quit")
        
        process_every = self.config['detection']['process_every_n_frames']
        frame_counter = 0
        processed_frame = None
        
        try:
            while self.running:
                # Read frame
                ret, frame = self.camera.read()
                
                if not ret:
                    self.logger.error("Failed to read frame")
                    time.sleep(0.1)
                    continue
                
                frame_counter += 1
                
                # Process frame (skip frames for performance)
                if frame_counter % process_every == 0:
                    processed_frame = self.process_frame(frame)
                    frame_counter = 0
                
                # Display
                if processed_frame is not None:
                    cv2.imshow(self.config['display']['window_name'], processed_frame)
                
                # Calculate FPS
                self.calculate_fps()
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    self.logger.info("Shutdown requested by user")
                    break
                elif key == ord('r') or key == ord('R'):
                    self.logger.info("Resetting alert system")
                    self.alert_system.reset()
                
        except KeyboardInterrupt:
            self.logger.info("Shutdown requested (Ctrl+C)")
        except Exception as e:
            self.logger.error(f"Runtime error: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown"""
        self.logger.info("Shutting down system...")
        self.running = False
        
        if self.camera is not None:
            self.camera.release()
        
        cv2.destroyAllWindows()
        
        self.logger.info("System shutdown complete")
        logging.shutdown()


def main():
    """Entry point"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     Manufacturing Safety Monitoring System v1.0          ║
    ║     Human Detection for Restricted Areas                 ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Create and run system
    system = SafetySystem()
    system.run()


if __name__ == "__main__":
    main()