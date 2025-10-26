import cv2
import numpy as np
import base64
import pickle
import os
from datetime import datetime

class FaceEncoder:
    def __init__(self):
        self.uploads_dir = "static/uploads/faces"
        os.makedirs(self.uploads_dir, exist_ok=True)
        
        # Load OpenCV face detector
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    def capture_face_encoding(self, image_path):
        """Extract face features using OpenCV"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return None, "Could not load image"
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) == 0:
                return None, "No face detected"
            
            if len(faces) > 1:
                return None, "Multiple faces detected"
            
            # Extract face region
            x, y, w, h = faces[0]
            face_region = gray[y:y+h, x:x+w]
            
            # Resize to standard size
            face_standard = cv2.resize(face_region, (100, 100))
            
            # Create simple encoding (flatten pixels)
            face_encoding = face_standard.flatten().astype(np.float32) / 255.0
            
            # Convert to base64 for storage
            encoding_bytes = pickle.dumps(face_encoding)
            encoding_base64 = base64.b64encode(encoding_bytes).decode('utf-8')
            
            return encoding_base64, "Face encoded successfully"
            
        except Exception as e:
            return None, f"Error in face encoding: {str(e)}"
    
    def verify_face_match(self, live_image_path, stored_encoding_base64):
        """Verify if live face matches stored encoding"""
        try:
            # Decode stored encoding
            encoding_bytes = base64.b64decode(stored_encoding_base64)
            stored_encoding = pickle.loads(encoding_bytes)
            
            # Process live image
            live_image = cv2.imread(live_image_path)
            if live_image is None:
                return False, "Could not load live image"
            
            gray = cv2.cvtColor(live_image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) == 0:
                return False, "No face detected in live image"
            
            # Extract face from live image
            x, y, w, h = faces[0]
            live_face_region = gray[y:y+h, x:x+w]
            live_face_standard = cv2.resize(live_face_region, (100, 100))
            live_encoding = live_face_standard.flatten().astype(np.float32) / 255.0
            
            # Calculate similarity (Euclidean distance)
            distance = np.linalg.norm(stored_encoding - live_encoding)
            
            # Consider it a match if distance is below threshold
            if distance < 0.3:
                return True, "Face matched successfully"
            else:
                return False, "Face does not match"
                
        except Exception as e:
            return False, f"Error in face matching: {str(e)}"
    
    def save_face_image(self, image_file, university_id):
        """Save face image for reference"""
        filename = f"{university_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(self.uploads_dir, filename)
        image_file.save(filepath)
        return filepath