from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
import hashlib
from models.models import Database
from utils.face_encoder import FaceEncoder
import os
import base64
from datetime import datetime
import uuid
import re
import logging
import json   # <-- ADD THIS

logger = logging.getLogger(__name__)

# ===== VALIDATION FUNCTIONS =====
def validate_university_code(code):
    """Validate exactly 10-digit university code"""
    return bool(re.match(r'^\d{10}$', str(code)))

def validate_phone(phone):
    """Validate 10-digit phone number"""
    if not phone:
        return False
    return bool(re.match(r'^\d{10}$', str(phone)))

def validate_bus_number(bus_no):
    """Validate bus number (1-3 digits)"""
    try:
        bus_num = int(bus_no)
        return 1 <= bus_num <= 999
    except:
        return False

def validate_roll_number(roll_no):
    """Validate roll number (numbers only)"""
    return bool(re.match(r'^\d+$', str(roll_no)))

# ===== END VALIDATION FUNCTIONS =====

student_bp = Blueprint('student', __name__)
db = Database()
face_encoder = FaceEncoder()

@student_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            data = request.form
            university_id = data.get('university_id')
            password = data.get('password')
            name = data.get('name')
            bus_number = int(data.get('bus_number'))
            bus_password = data.get('bus_password')
            face_image_data = data.get('face_image_data')  # Base64 from camera
            
            # Validate university ID format (2420030___ - 10 digits)
            if not university_id.isdigit() or len(university_id) != 10:
                return jsonify({'success': False, 'message': 'Invalid University ID format. Must be 10 digits starting with 24200.'})
            
            # Check if university ID already exists
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE university_id = ?", (university_id,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'University ID already registered'})
            
            # Verify bus password
            cursor.execute("SELECT bus_password FROM bus_incharges WHERE bus_number = ?", (bus_number,))
            bus_data = cursor.fetchone()
            
            if not bus_data:
                conn.close()
                return jsonify({'success': False, 'message': f'Bus number {bus_number} not found. Please check with your bus incharge.'})
            
            if bus_data[0] != bus_password:
                conn.close()
                return jsonify({'success': False, 'message': 'Invalid bus password. Please ask your bus incharge for the correct password.'})
            
            # Process face image from camera
            if not face_image_data:
                return jsonify({'success': False, 'message': 'Please capture your face using the camera'})
            
            # Convert base64 image to file
            try:
                # Remove data:image/jpeg;base64, prefix if present
                if ',' in face_image_data:
                    face_image_data = face_image_data.split(',')[1]
                
                image_bytes = base64.b64decode(face_image_data)
                
                # Save temporary image
                temp_filename = f"temp_face_{university_id}.jpg"
                temp_image_path = os.path.join("static/uploads/faces", temp_filename)
                
                # Ensure directory exists
                os.makedirs("static/uploads/faces", exist_ok=True)
                
                with open(temp_image_path, 'wb') as f:
                    f.write(image_bytes)
                
                # Extract face encoding using dlib
                face_encoding = face_encoder.encode_face(temp_image_path)
                
                # Remove temp image
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                
                if face_encoding is None:
                    return jsonify({'success': False, 'message': 'No face found in the captured image. Please try again with a clearer face photo.'})
                
            except Exception as e:
                return jsonify({'success': False, 'message': f'Face processing error: {str(e)}'})
            
            # Hash password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            # Convert encoding to JSON before saving in DB
            encoding_str = json.dumps(face_encoding.tolist())
            
            # Insert student data
            cursor.execute('''
                INSERT INTO students (university_id, password, name, bus_number, bus_password, face_encoding)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (university_id, hashed_password, name, bus_number, bus_password, encoding_str))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True, 
                'message': f'Student {name} registered successfully! Face encoding stored. You can now login.'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Registration error: {str(e)}'})
    
    return render_template('student/signup.html')

# Keep the rest of the routes the same (login, dashboard, attendance)
@student_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        university_id = request.form.get('university_id')
        password = request.form.get('password')
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT university_id, name, bus_number FROM students 
            WHERE university_id = ? AND password = ?
        ''', (university_id, hashed_password))
        
        student = cursor.fetchone()
        conn.close()
        
        if student:
            session['student_id'] = student[0]
            session['student_name'] = student[1]
            session['bus_number'] = student[2]
            session['role'] = 'student'
            return jsonify({'success': True, 'message': 'Login successful!'})
        else:
            return jsonify({'success': False, 'message': 'Invalid University ID or password'})
    
    return render_template('student/login.html')

@student_bp.route('/dashboard')
def dashboard():
    if 'student_id' not in session or session.get('role') != 'student':
        return redirect(url_for('student.login'))
    
    return render_template('student/dashboard.html', 
                          student_name=session.get('student_name'),
                          university_id=session.get('student_id'),
                          bus_number=session.get('bus_number'))

@student_bp.route('/attendance-status')
def attendance_status():
    if 'student_id' not in session or session.get('role') != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        university_id = session.get('student_id')
        bus_number = session.get('bus_number')
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if attendance marked today
        cursor.execute('''
            SELECT * FROM attendance 
            WHERE university_id = ? AND date = DATE('now') AND bus_number = ?
        ''', (university_id, bus_number))
        
        attendance_record = cursor.fetchone()
        conn.close()
        
        if attendance_record:
            return jsonify({'success': True, 'status': 'Present'})
        else:
            return jsonify({'success': True, 'status': 'Not Marked'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error checking attendance: {str(e)}'})
