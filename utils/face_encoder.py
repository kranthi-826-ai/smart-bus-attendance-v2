import deepface
from deepface import DeepFace
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
    
    def capture_face_encoding(self, image_path):
        """Extract face encoding using DeepFace"""
        try:
            # Verify the image can be processed
            if not os.path.exists(image_path):
                return None, "Image file not found"
            
            # Use DeepFace for accurate face encoding
            try:
                result = DeepFace.represent(
                    img_path=image_path,
                    model_name='Facenet',
                    enforce_detection=True,
                    detector_backend='opencv'
                )
                
                if not result:
                    return None, "No face detected"
                
                # Get the face embedding
                face_embedding = result[0]['embedding']
                
                # Convert to base64 for storage
                encoding_bytes = pickle.dumps(face_embedding)
                encoding_base64 = base64.b64encode(encoding_bytes).decode('utf-8')
                
                return encoding_base64, "Face encoded successfully with DeepFace!"
                
            except Exception as deepface_error:
                return None, f"Face detection failed: {str(deepface_error)}"
            
        except Exception as e:
            return None, f"Face processing error: {str(e)}"
    
    def verify_face_match(self, live_image_path, stored_encoding_base64):
        """Verify if live face matches stored encoding using DeepFace"""
        try:
            # Decode stored encoding
            encoding_bytes = base64.b64decode(stored_encoding_base64)
            stored_embedding = pickle.loads(encoding_bytes)
            
            # Verify live image with DeepFace
            try:
                result = DeepFace.represent(
                    img_path=live_image_path,
                    model_name='Facenet',
                    enforce_detection=True,
                    detector_backend='opencv'
                )
                
                if not result:
                    return False, "No face detected in live image"
                
                live_embedding = result[0]['embedding']
                
                # Calculate cosine similarity
                from numpy import dot
                from numpy.linalg import norm
                
                cosine_similarity = dot(stored_embedding, live_embedding) / (norm(stored_embedding) * norm(live_embedding))
                
                # Consider it a match if similarity > 0.6
                if cosine_similarity > 0.6:
                    return True, f"Face matched successfully! Similarity: {cosine_similarity:.2f}"
                else:
                    return False, f"Face does not match. Similarity: {cosine_similarity:.2f}"
                    
            except Exception as deepface_error:
                return False, f"Live face verification failed: {str(deepface_error)}"
                
        except Exception as e:
            return False, f"Face matching error: {str(e)}"
    
    def save_face_image(self, image_file, university_id):
        """Save face image for reference"""
        filename = f"{university_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(self.uploads_dir, filename)
        image_file.save(filepath)
        return filepath