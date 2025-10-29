import face_recognition
import numpy as np
import cv2
import os
import pickle
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
            
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) == 0:
                print(f"❌ No face detected in {image_path}")
                return False, "No face detected in image"
            
            if len(face_encodings) > 1:
                print(f"⚠️ Multiple faces detected, using first face")
            
            face_encoding = face_encodings[0]
            encoding_list = face_encoding.tolist()
            
            self.known_encodings[university_id] = encoding_list
            self.save_encodings()
            
            print(f"✅ Face encoded successfully for {university_id}")
            return True, "Face encoded successfully"
            
        except Exception as e:
            print(f"❌ Error encoding face: {e}")
            return False, f"Error encoding face: {str(e)}"
    
    def recognize_face(self, image_path, tolerance=0.6):
        try:
            print(f"🔄 Recognizing face from {image_path}")
            
            unknown_image = face_recognition.load_image_file(image_path)
            unknown_encodings = face_recognition.face_encodings(unknown_image)
            
            if len(unknown_encodings) == 0:
                print("❌ No face detected in the image")
                return None, "No face detected"
            
            unknown_encoding = unknown_encodings[0]
            
            known_encodings_list = []
            known_ids = []
            
            for uid, encoding in self.known_encodings.items():
                known_encodings_list.append(np.array(encoding))
                known_ids.append(uid)
            
            if not known_encodings_list:
                print("❌ No known faces in database")
                return None, "No known faces in database"
            
            matches = face_recognition.compare_faces(
                known_encodings_list, 
                unknown_encoding, 
                tolerance=tolerance
            )
            
            face_distances = face_recognition.face_distance(
                known_encodings_list, 
                unknown_encoding
            )
            
            best_match_index = np.argmin(face_distances) if face_distances.size > 0 else -1
            
            if best_match_index != -1 and matches[best_match_index]:
                matched_id = known_ids[best_match_index]
                confidence = 1 - face_distances[best_match_index]
                print(f"✅ Face recognized as {matched_id} with confidence {confidence:.2f}")
                return matched_id, confidence
            else:
                print("❌ No matching face found")
                return None, "No matching face found"
                
        except Exception as e:
            print(f"❌ Error recognizing face: {e}")
            return None, f"Error recognizing face: {str(e)}"

# Global instance
face_encoder = FaceEncoder()