import face_recognition
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

class FaceEncoder:
    """Lightweight face encoding using face_recognition (dlib-based)"""
    
    def __init__(self, model='hog'):
        """
        Initialize face encoder
        model: 'hog' (fast, CPU-friendly) or 'cnn' (accurate, requires more resources)
        For PythonAnywhere free tier, use 'hog'
        """
        self.model = model
        self.known_encodings = []
        self.known_names = []
    
    def encode_face(self, image_path):
        """
        Encode a single face from an image file
        Returns: face encoding (numpy array) or None if no face found
        """
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Get face encodings (returns list of encodings)
            face_encodings = face_recognition.face_encodings(image, model=self.model)
            
            if face_encodings:
                return face_encodings[0]  # Return first face encoding
            else:
                logger.warning(f"No face found in {image_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error encoding face from {image_path}: {str(e)}")
            return None
    
    def compare_faces(self, known_encoding, unknown_encoding, tolerance=0.6):
        """
        Compare two face encodings
        Returns: True if faces match, False otherwise
        tolerance: 0.6 is default, lower = stricter matching
        """
        try:
            distance = face_recognition.face_distance([known_encoding], unknown_encoding)
            return distance[0] < tolerance
        except Exception as e:
            logger.error(f"Error comparing faces: {str(e)}")
            return False
    
    def get_distance(self, known_encoding, unknown_encoding):
        """Get Euclidean distance between two face encodings"""
        try:
            distance = face_recognition.face_distance([known_encoding], unknown_encoding)
            return float(distance[0])
        except Exception as e:
            logger.error(f"Error calculating distance: {str(e)}")
            return 1.0
    
    def detect_face(self, image_path):
        """
        Detect face and return coordinates and encoding
        Returns: dict with 'face_locations' and 'encoding', or None
        """
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image, model=self.model)
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if face_locations and face_encodings:
                return {
                    'face_locations': face_locations,
                    'encoding': face_encodings[0]
                }
            return None
        except Exception as e:
            logger.error(f"Error detecting face: {str(e)}")
            return None
    
    def encode_list_to_json(self, encoding):
        """Convert numpy array encoding to JSON-serializable list"""
        return encoding.tolist() if isinstance(encoding, np.ndarray) else encoding
    
    def encode_json_to_array(self, json_encoding):
        """Convert JSON list encoding back to numpy array"""
        return np.array(json_encoding) if isinstance(json_encoding, list) else json_encoding
