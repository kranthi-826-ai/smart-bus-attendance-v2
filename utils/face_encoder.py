import face_recognition
import numpy as np
import os
import pickle
import cv2
from datetime import datetime

class FaceEncoder:
    def __init__(self, encodings_file='face_encodings.pkl'):
        self.encodings_file = encodings_file
        self.known_encodings = {}
        self.load_encodings()
    
    def load_encodings(self):
        try:
            if os.path.exists(self.encodings_file):
                with open(self.encodings_file, 'rb') as f:
                    self.known_encodings = pickle.load(f)
                print(f"✅ Loaded {len(self.known_encodings)} face encodings")
            else:
                print("⚠️ No existing encodings file found")
                self.known_encodings = {}
        except Exception as e:
            print(f"❌ Error loading encodings: {e}")
            self.known_encodings = {}
    
    def save_encodings(self):
        try:
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(self.known_encodings, f)
            print(f"💾 Saved {len(self.known_encodings)} face encodings")
        except Exception as e:
            print(f"❌ Error saving encodings: {e}")
    
    def encode_face(self, image_path, university_id):
        try:
            print(f"🔄 Encoding face for {university_id} from {image_path}")
            
            # Load image using face_recognition (uses dlib)
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) == 0:
                return False, "No face detected in image"
            
            if len(face_encodings) > 1:
                print(f"⚠️ Multiple faces detected, using first face")
            
            # Store the 128-dimensional dlib encoding
            self.known_encodings[university_id] = face_encodings[0].tolist()
            self.save_encodings()
            
            print(f"✅ Face encoded successfully for {university_id}")
            return True, "Face encoded successfully"
            
        except Exception as e:
            print(f"❌ Error encoding face: {e}")
            return False, f"Error encoding face: {str(e)}"
    
    def recognize_face(self, image_path, tolerance=0.6):
        try:
            print(f"🔄 Recognizing face from {image_path}")
            
            # Load and encode unknown image
            unknown_image = face_recognition.load_image_file(image_path)
            unknown_encodings = face_recognition.face_encodings(unknown_image)
            
            if len(unknown_encodings) == 0:
                return None, "No face detected"
            
            unknown_encoding = unknown_encodings[0]
            
            # Convert stored encodings back to numpy
            known_encodings_list = []
            known_ids = []
            
            for uid, encoding in self.known_encodings.items():
                known_encodings_list.append(np.array(encoding))
                known_ids.append(uid)
            
            if not known_encodings_list:
                return None, "No registered faces"
            
            # Use dlib's face comparison
            matches = face_recognition.compare_faces(
                known_encodings_list, 
                unknown_encoding, 
                tolerance=tolerance
            )
            
            face_distances = face_recognition.face_distance(
                known_encodings_list, 
                unknown_encoding
            )
            
            # Find best match
            best_match_index = np.argmin(face_distances)
            
            if matches[best_match_index]:
                matched_id = known_ids[best_match_index]
                confidence = 1 - face_distances[best_match_index]
                print(f"✅ Face recognized as {matched_id} (confidence: {confidence:.2f})")
                return matched_id, confidence
            else:
                return None, "No matching face found"
                
        except Exception as e:
            print(f"❌ Error recognizing face: {e}")
            return None, f"Error recognizing face: {str(e)}"



def capture_face_encoding(self, image_path, university_id):
    """Fix for compatibility - redirect to encode_face"""
    return self.encode_face(image_path, university_id)

# Global instance
face_encoder = FaceEncoder()