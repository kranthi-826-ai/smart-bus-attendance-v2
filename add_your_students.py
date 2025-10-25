import sqlite3
import hashlib
import os  # ADD THIS LINE
def add_your_students():
    conn = sqlite3.connect('bus_attendance.db')
    cursor = conn.cursor()
    
    # Add YOUR specific students for BUS001
    your_students = [
        ('Student 2420030539', '2420030539', 'password123', 1),
        ('Student 2420030440', '2420030440', 'password123', 1),
        ('Student 2420030546', '2420030546', 'password123', 1),
    ]
    
    for name, roll_number, password, bus_id in your_students:
        try:
            # Hash the password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            # Create a sample face image
            os.makedirs('static/uploads/students', exist_ok=True)
            photo_path = f'static/uploads/students/student_{roll_number}.jpg'
            
            # Create simple image with text
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (200, 200), color='white')
            d = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            d.text((10, 80), roll_number, fill='black', font=font)
            img.save(photo_path)
            
            cursor.execute("INSERT INTO students (name, roll_number, password, bus_id, face_encoding_data, id_card_image_path) VALUES (?, ?, ?, ?, ?, ?)",
                         (name, roll_number, hashed_password, bus_id, "deepface_encoding", photo_path))
            print(f"✓ Added student: {name} ({roll_number}) to Bus {bus_id}")
        except sqlite3.IntegrityError:
            print(f"⚠ Student {roll_number} already exists, skipping...")
    
    conn.commit()
    conn.close()
    print("✅ Your students added successfully!")

if __name__ == "__main__":
    add_your_students()