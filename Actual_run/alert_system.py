import cv2
import pygame
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
import os

class AlertSystem:
    """
    Manages all alert mechanisms
    """
    
    def __init__(self, config):
        """
        Initialize alert system
        
        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Alert state
        self.last_alert_time = None
        self.cooldown = config.get('cooldown_seconds', 5)
        self.alert_active = False
        
        # Initialize audio
        if config.get('enable_audio', True):
            try:
                pygame.mixer.init()
                
                # Create alarm sound if not exists
                alarm_path = 'sounds/alarm.wav'
                if not os.path.exists(alarm_path):
                    self.logger.warning("Alarm sound not found, creating default")
                    self._create_default_alarm(alarm_path)
                
                self.alarm_sound = pygame.mixer.Sound(alarm_path)
                self.logger.info("Audio alerts enabled")
            except Exception as e:
                self.logger.error(f"Failed to initialize audio: {e}")
                config['enable_audio'] = False
        
        # Create violations directory
        os.makedirs('violations/snapshots', exist_ok=True)
        
    def _create_default_alarm(self, path):
        """Create a simple beep sound"""
        import numpy as np
        from scipy.io import wavfile
        
        try:
            sample_rate = 44100
            duration = 0.5
            frequency = 800
            
            t = np.linspace(0, duration, int(sample_rate * duration))
            wave = np.sin(2 * np.pi * frequency * t) * 32767
            wave = wave.astype(np.int16)
            
            os.makedirs('sounds', exist_ok=True)
            wavfile.write(path, sample_rate, wave)
        except:
            self.logger.warning("Could not create default alarm sound")
    
    def should_alert(self):
        """
        Check if enough time has passed since last alert
        
        Returns:
            Boolean
        """
        if self.last_alert_time is None:
            return True
        
        time_since_last = (datetime.now() - self.last_alert_time).total_seconds()
        return time_since_last >= self.cooldown
    
    def trigger_alert(self, frame, violations):
        """
        Trigger all enabled alerts
        
        Args:
            frame: Current video frame
            violations: List of violation detections
        """
        if not self.should_alert():
            return
        
        self.alert_active = True
        self.last_alert_time = datetime.now()
        timestamp = self.last_alert_time.strftime("%Y-%m-%d %H:%M:%S")
        
        self.logger.critical(f"SAFETY VIOLATION at {timestamp} - {len(violations)} person(s) in restricted zone")
        
        # Visual alert
        if self.config.get('enable_visual', True):
            self._visual_alert(frame, violations, timestamp)
        
        # Audio alert
        if self.config.get('enable_audio', True):
            self._audio_alert()
        
        # Save snapshot
        if self.config.get('enable_snapshots', True):
            snapshot_path = self._save_snapshot(frame, timestamp)
        
        # Email alert
        if self.config.get('enable_email', False):
            self._email_alert(violations, timestamp, snapshot_path)
    
    def _visual_alert(self, frame, violations, timestamp):
        """Draw alert on frame"""
        # Full screen flash effect
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), 
                     (0, 0, 255), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        
        # Alert message
        message = f"⚠ SAFETY ALERT - {len(violations)} PERSON(S) IN RESTRICTED ZONE ⚠"
        cv2.putText(frame, message, (50, 50), 
                   cv2.FONT_HERSHEY_BOLD, 1, (255, 255, 255), 3)
        cv2.putText(frame, timestamp, (50, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    def _audio_alert(self):
        """Play alarm sound"""
        try:
            self.alarm_sound.play()
        except Exception as e:
            self.logger.error(f"Audio alert failed: {e}")
    
    def _save_snapshot(self, frame, timestamp):
        """
        Save violation snapshot
        
        Returns:
            Path to saved image
        """
        filename = f"violation_{timestamp.replace(':', '-').replace(' ', '_')}.jpg"
        filepath = os.path.join('violations/snapshots', filename)
        
        try:
            cv2.imwrite(filepath, frame)
            self.logger.info(f"Snapshot saved: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to save snapshot: {e}")
            return None
    
    def _email_alert(self, violations, timestamp, image_path):
        """Send email notification"""
        email_config = self.config.get('email', {})
        
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['sender_email']
            msg['To'] = email_config['recipient_email']
            msg['Subject'] = f"⚠ SAFETY ALERT - Restricted Area Violation - {timestamp}"
            
            # Email body
            body = f"""
            SAFETY VIOLATION DETECTED
            
            Time: {timestamp}
            Number of persons in restricted zone: {len(violations)}
            
            Immediate action required!
            
            This is an automated alert from the Manufacturing Safety System.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach image
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    img = MIMEImage(f.read())
                    msg.attach(img)
            
            # Send email
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['sender_email'], email_config['sender_password'])
            server.send_message(msg)
            server.quit()
            
            self.logger.info("Email alert sent successfully")
            
        except Exception as e:
            self.logger.error(f"Email alert failed: {e}")
    
    def reset(self):
        """Reset alert state"""
        self.alert_active = False