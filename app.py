import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import get_db_connection, init_db
import cv2
import numpy as np
from deepface import DeepFace
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'static/uploads/students'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/uploads/temp', exist_ok=True)

# Initialize database
init_db()

@app.route('/')
def index():
    return render_template('index.html')

# Student Signup with Photo Upload
@app.route('/student_signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        name = request.form['name']
        roll_number = request.form['roll_number']
        university_id = request.form['university_id']
        password = request.form['password']
        bus_number = request.form['bus_number']
        
        # Handle photo upload
        if 'photo' not in request.files:
            flash('No photo uploaded', 'error')
            return render_template('student_signup.html')
        
        photo = request.files['photo']
        
        if photo.filename == '':
            flash('No photo selected', 'error')
            return render_template('student_signup.html')
        
        if photo and allowed_file(photo.filename):
            # Generate unique filename
            filename = f"student_{roll_number}_{uuid.uuid4().hex[:8]}.jpg"
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the photo
            photo.save(photo_path)
            
            # Verify the image is valid
            try:
                img = cv2.imread(photo_path)
                if img is None:
                    raise ValueError("Invalid image file")
            except Exception as e:
                os.remove(photo_path)  # Remove invalid file
                flash('Invalid image file. Please upload a valid JPG image.', 'error')
                return render_template('student_signup.html')
            
            # Store in database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO students (name, roll_number, university_id, password, bus_number, photo_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, roll_number, university_id, password, bus_number, photo_path))
                
                conn.commit()
                flash('Student registered successfully! Please login.', 'success')
                return redirect(url_for('student_login'))
                
            except Exception as e:
                conn.rollback()
                flash('Error registering student. Roll number or University ID might already exist.', 'error')
            finally:
                conn.close()
        else:
            flash('Please upload a valid JPG image', 'error')
    
    return render_template('student_signup.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

# Student Login
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        university_id = request.form['university_id']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students WHERE university_id = ? AND password = ?', 
                      (university_id, password))
        student = cursor.fetchone()
        conn.close()
        
        if student:
            session['student_id'] = student['id']
            session['student_name'] = student['name']
            session['student_roll_number'] = student['roll_number']
            flash('Login successful!', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid University ID or password', 'error')
    
    return render_template('student_login.html')

# Student Dashboard
@app.route('/student_dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    
    # Get student attendance data
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT date, status FROM attendance 
        WHERE student_id = ? ORDER BY date DESC LIMIT 10
    ''', (session['student_id'],))
    attendance_records = cursor.fetchall()
    conn.close()
    
    return render_template('student_dashboard.html', 
                         student_name=session['student_name'],
                         attendance_records=attendance_records)

# Mark Attendance with Face Recognition
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'photo' not in request.files:
        return jsonify({'success': False, 'message': 'No photo uploaded'})
    
    photo = request.files['photo']
    bus_number = request.form.get('bus_number')
    
    if photo.filename == '':
        return jsonify({'success': False, 'message': 'No photo selected'})
    
    # Save temporary photo for processing
    temp_filename = f"temp_{uuid.uuid4().hex[:8]}.jpg"
    temp_path = os.path.join('static/uploads/temp', temp_filename)
    photo.save(temp_path)
    
    try:
        # Get all students in this bus
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students WHERE bus_number = ?', (bus_number,))
        students = cursor.fetchall()
        
        best_match = None
        best_score = 0
        
        # Compare with each student's photo
        for student in students:
            if student['photo_path'] and os.path.exists(student['photo_path']):
                try:
                    result = DeepFace.verify(
                        temp_path, 
                        student['photo_path'],
                        model_name='VGG-Face',
                        enforce_detection=False
                    )
                    
                    if result['verified'] and result['distance'] > best_score:
                        best_score = result['distance']
                        best_match = student
                        
                except Exception as e:
                    print(f"Face comparison error for {student['name']}: {e}")
                    continue
        
        # If match found, mark attendance
        if best_match and best_score > 0.5:  # Adjust threshold as needed
            cursor.execute('''
                INSERT OR REPLACE INTO attendance (student_id, date, status, bus_number)
                VALUES (?, DATE('now'), 'Present', ?)
            ''', (best_match['id'], bus_number))
            
            conn.commit()
            conn.close()
            
            # Clean up temp file
            os.remove(temp_path)
            
            return jsonify({
                'success': True, 
                'message': f'Attendance marked for {best_match["name"]}',
                'student_name': best_match['name'],
                'roll_number': best_match['roll_number']
            })
        else:
            conn.close()
            os.remove(temp_path)
            return jsonify({'success': False, 'message': 'No matching student found'})
            
    except Exception as e:
        # Clean up temp file in case of error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'success': False, 'message': f'Error processing attendance: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True)