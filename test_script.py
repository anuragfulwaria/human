# tests/test_system.py
"""
System test suite
"""

import sys
sys.path.append('../src')

from detector import HumanDetector
from zone_manager import ZoneManager
import cv2
import numpy as np

def test_detector():
    """Test human detection"""
    print("Testing Human Detector...")
    
    detector = HumanDetector()
    
    # Create test image with a person (you need a sample image)
    # For now, just test initialization
    print("✓ Detector initialized")
    
def test_zone_manager():
    """Test zone management"""
    print("Testing Zone Manager...")
    
    zone_points = [[100, 100], [200, 100], [200, 200], [100, 200]]
    zone_manager = ZoneManager(zone_points)
    
    # Test point inside
    assert zone_manager.is_point_in_zone((150, 150)) == True
    print("✓ Point inside zone detected correctly")
    
    # Test point outside
    assert zone_manager.is_point_in_zone((50, 50)) == False
    print("✓ Point outside zone detected correctly")
    
def test_camera():
    """Test camera connection"""
    print("Testing Camera...")
    
    cap = cv2.VideoCapture(0)
    
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"✓ Camera working - Frame size: {frame.shape}")
        else:
            print("✗ Failed to read frame")
    else:
        print("✗ Camera connection failed")
    
    cap.release()

if __name__ == "__main__":
    print("=" * 50)
    print("Running System Tests")
    print("=" * 50)
    
    test_detector()
    test_zone_manager()
    test_camera()
    
    print("=" * 50)
    print("Tests Complete")