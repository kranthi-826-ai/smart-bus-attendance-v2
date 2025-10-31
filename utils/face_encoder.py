from deepface import DeepFace
import cv2
import numpy as np
import os
import pickle
from datetime import datetime

class FaceEncoder:
    def __init__(self, encodings_file='face_encodings.pkl'):
        self.encodings_file = encodings_file
        self.known_faces = {}
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
            
            # Use DeepFace to get face embedding
            embedding_objs = DeepFace.represent(
                img_path=image_path,
                model_name="Facenet",
                enforce_detection=True,
                detector_backend="opencv"
            )
            
            if not embedding_objs:
                return False, "No face detected in image"
            
            # Get the first face embedding
            face_embedding = embedding_objs[0]["embedding"]
            
            # Store encoding
            self.known_faces[university_id] = face_embedding
            self.save_encodings()
            
            print(f"✅ Face encoded successfully for {university_id}")
            return True, "Face encoded successfully"
            
        except Exception as e:
            print(f"❌ Error encoding face: {e}")
            return False, f"Error encoding face: {str(e)}"
    
    def recognize_face(self, image_path, threshold=0.6):
        try:
            print(f"🔄 Recognizing face from {image_path}")
            
            if not self.known_faces:
                return None, "No known faces in database"
            
            # Get embedding of current face
            current_embedding_objs = DeepFace.represent(
                img_path=image_path,
                model_name="Facenet", 
                enforce_detection=True,
                detector_backend="opencv"
            )
            
            if not current_embedding_objs:
                return None, "No face detected"
            
            current_embedding = np.array(current_embedding_objs[0]["embedding"])
            
            best_match_id = None
            best_similarity = 0
            
            # Compare with all known faces
            for uid, known_embedding in self.known_faces.items():
                known_array = np.array(known_embedding)
                
                # Calculate cosine similarity
                similarity = np.dot(current_embedding, known_array) / (
                    np.linalg.norm(current_embedding) * np.linalg.norm(known_array)
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