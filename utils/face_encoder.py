import cv2
import numpy as np
import os
import pickle
from datetime import datetime

class FaceEncoder:
    def __init__(self, encodings_file='face_encodings.pkl'):
        self.encodings_file = encodings_file
        self.known_faces = {}
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.load_encodings()
    
    def load_encodings(self):
        try:
            if os.path.exists(self.encodings_file):
                with open(self.encodings_file, 'rb') as f:
                    self.known_faces = pickle.load(f)
                print(f"✅ Loaded {len(self.known_faces)} face encodings")
            else:
                print("⚠️ No existing encodings file found")
                self.known_faces = {}
        except Exception as e:
            print(f"❌ Error loading encodings: {e}")
            self.known_faces = {}
    
    def save_encodings(self):
        try:
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(self.known_faces, f)
            print(f"💾 Saved {len(self.known_faces)} face encodings")
        except Exception as e:
            print(f"❌ Error saving encodings: {e}")
    
    def encode_face(self, image_path, university_id):
        try:
            print(f"🔄 Encoding face for {university_id} from {image_path}")
            
            # Read and process image
            image = cv2.imread(image_path)
            if image is None:
                return False, "Could not read image"
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(30, 30)
            )
            
            if len(faces) == 0:
                print(f"❌ No face detected in {image_path}")
                return False, "No face detected in image"
            
            if len(faces) > 1:
                print(f"⚠️ Multiple faces detected, using first face")
            
            # Use the first face
            x, y, w, h = faces[0]
            face_roi = gray[y:y+h, x:x+w]
            
            # Resize to standard size for consistency
            face_standard = cv2.resize(face_roi, (100, 100))
            
            # Flatten and normalize
            face_encoding = face_standard.flatten()
            face_encoding = face_encoding / 255.0  # Normalize
            
            # Store encoding
            self.known_faces[university_id] = face_encoding.tolist()
            self.save_encodings()
            
            print(f"✅ Face encoded successfully for {university_id}")
            return True, "Face encoded successfully"
            
        except Exception as e:
            print(f"❌ Error encoding face: {e}")
            return False, f"Error encoding face: {str(e)}"
    
    def recognize_face(self, image_path, threshold=0.7):
        try:
            print(f"🔄 Recognizing face from {image_path}")
            
            # Read and process unknown image
            unknown_image = cv2.imread(image_path)
            if unknown_image is None:
                return None, "Could not read image"
            
            gray = cv2.cvtColor(unknown_image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(30, 30)
            )
            
            if len(faces) == 0:
                print("❌ No face detected in the image")
                return None, "No face detected"
            
            # Use the first face
            x, y, w, h = faces[0]
            unknown_face_roi = gray[y:y+h, x:x+w]
            unknown_face_standard = cv2.resize(unknown_face_roi, (100, 100))
            unknown_encoding = unknown_face_standard.flatten() / 255.0
            
            best_match_id = None
            best_similarity = 0
            
            # Compare with known faces
            for uid, known_encoding in self.known_faces.items():
                known_array = np.array(known_encoding)
                
                # Calculate similarity (cosine similarity)
                similarity = np.dot(unknown_encoding, known_array) / (
                    np.linalg.norm(unknown_encoding) * np.linalg.norm(known_array)
                )
                
                if similarity > best_similarity and similarity > threshold:
                    best_similarity = similarity
                    best_match_id = uid
            
            if best_match_id:
                print(f"✅ Face recognized as {best_match_id} with similarity {best_similarity:.2f}")
                return best_match_id, best_similarity
            else:
                print("❌ No matching face found")
                return None, "No matching face found"
                
        except Exception as e:
            print(f"❌ Error recognizing face: {e}")
            return None, f"Error recognizing face: {str(e)}"

# Global instance
face_encoder = FaceEncoder()