import face_recognition
import cv2
import numpy as np
import pickle
import base64
from datetime import datetime
import os

class FaceEncoder:
    def __init__(self):
        self.uploads_dir = "static/uploads/faces"
        os.makedirs(self.uploads_dir, exist_ok=True)
    
    def capture_face_encoding(self, image_path):
        """Extract face encoding from image"""
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Find face locations
            face_locations = face_recognition.face_locations(image)
            
            if len(face_locations) == 0:
                return None, "No face detected"
            
            if len(face_locations) > 1:
                return None, "Multiple faces detected"
            
            # Extract face encoding
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if len(face_encodings) == 0:
                return None, "Could not extract face features"
            
            # Convert to base64 for storage
            encoding_bytes = pickle.dumps(face_encodings[0])
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
            live_image = face_recognition.load_image_file(live_image_path)
            live_face_locations = face_recognition.face_locations(live_image)
            
            if len(live_face_locations) == 0:
                return False, "No face detected in live image"
            
            live_face_encodings = face_recognition.face_encodings(live_image, live_face_locations)
            
            if len(live_face_encodings) == 0:
                return False, "Could not extract face features from live image"
            
            # Compare faces
            matches = face_recognition.compare_faces([stored_encoding], live_face_encodings[0])
            face_distance = face_recognition.face_distance([stored_encoding], live_face_encodings[0])
            
            # Consider it a match if distance is less than 0.6
            if matches[0] and face_distance[0] < 0.6:
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