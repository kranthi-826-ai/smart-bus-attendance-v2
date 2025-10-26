import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from datetime import datetime, date
import uuid
import json
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'smart-bus-attendance-secret-2024')
app.config['UPLOAD_FOLDER'] = 'static/uploads/students'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Create upload directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/uploads/temp', exist_ok=True)

# Database connection
def get_db_connection():
    conn = sqlite3.connect('bus_attendance.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Bus Incharge Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bus_incharge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone_number TEXT,
            bus_number TEXT UNIQUE NOT NULL,
            bus_password TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Students Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT UNIQUE NOT NULL,
            university_id TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            bus_number TEXT NOT NULL,
            photo_path TEXT,
            face_encoding TEXT,
            is_verified BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Attendance Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'Present',
            bus_number TEXT NOT NULL,
            marked_by TEXT DEFAULT 'face_recognition',
            confidence_score REAL,
            marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id),
            UNIQUE(student_id, date)
        )
    ''')
    
    # Face Recognition Logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS face_recognition_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            bus_number TEXT,
            confidence_score REAL,
            verification_result BOOLEAN,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# Student Routes
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
            
            # For now, store simulated face encoding
            # In production, you would use: face_encoding = extract_face_encoding(photo_path)
            face_encoding = "simulated_encoding_for_demo"
            
            # Store in database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO students (name, roll_number, university_id, password, bus_number, photo_path, face_encoding)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (name, roll_number, university_id, password, bus_number, photo_path, face_encoding))
                
                conn.commit()
                flash('Student registered successfully! You can now login.', 'success')
                return redirect(url_for('student_login'))
                
            except sqlite3.IntegrityError as e:
                conn.rollback()
                if 'roll_number' in str(e):
                    flash('Roll number already exists', 'error')
                elif 'university_id' in str(e):
                    flash('University ID already exists', 'error')
                else:
                    flash('Error registering student', 'error')
            except Exception as e:
                conn.rollback()
                flash('Error registering student', 'error')
            finally:
                conn.close()
        else:
            flash('Please upload a valid JPG, JPEG, or PNG image', 'error')
    
    return render_template('student_signup.html')

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        university_id = request.form['university_id']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students WHERE university_id = ? AND password = ? AND is_active = 1', 
                      (university_id, password))
        student = cursor.fetchone()
        conn.close()
        
        if student:
            session['student_id'] = student['id']
            session['student_name'] = student['name']
            session['student_roll_number'] = student['roll_number']
            session['user_type'] = 'student'
            flash('Login successful!', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid University ID or password', 'error')
    
    return render_template('student_login.html')

@app.route('/student_dashboard')
def student_dashboard():
    if 'student_id' not in session or session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get attendance records for this student
    cursor.execute('''
        SELECT date, status, bus_number, marked_at 
        FROM attendance 
        WHERE student_id = ? 
        ORDER BY date DESC LIMIT 10
    ''', (session['student_id'],))
    attendance_records = cursor.fetchall()
    
    conn.close()
    
    return render_template('student_dashboard.html', 
                         student_name=session['student_name'],
                         attendance_records=attendance_records,
                         current_date=date.today().isoformat())

# Bus Incharge Routes
@app.route('/incharge_signup', methods=['GET', 'POST'])
def incharge_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone_number = request.form.get('phone_number', '')
        bus_number = request.form['bus_number']
        bus_password = request.form['bus_password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO bus_incharge (name, email, password, phone_number, bus_number, bus_password)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, email, password, phone_number, bus_number, bus_password))
            
            conn.commit()
            flash('Bus Incharge registered successfully! You can now login.', 'success')
            return redirect(url_for('incharge_login'))
            
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if 'email' in str(e):
                flash('Email already exists', 'error')
            elif 'bus_number' in str(e):
                flash('Bus number already assigned to another incharge', 'error')
            else:
                flash('Error registering bus incharge', 'error')
        except Exception as e:
            conn.rollback()
            flash('Error registering bus incharge', 'error')
        finally:
            conn.close()
    
    return render_template('incharge_signup.html')

@app.route('/incharge_login', methods=['GET', 'POST'])
def incharge_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bus_incharge WHERE email = ? AND password = ? AND is_active = 1', 
                      (email, password))
        incharge = cursor.fetchone()
        conn.close()
        
        if incharge:
            session['incharge_id'] = incharge['id']
            session['incharge_name'] = incharge['name']
            session['bus_number'] = incharge['bus_number']
            session['user_type'] = 'incharge'
            flash('Login successful!', 'success')
            return redirect(url_for('incharge_dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('incharge_login.html')

@app.route('/incharge_dashboard')
def incharge_dashboard():
    if 'incharge_id' not in session or session.get('user_type') != 'incharge':
        return redirect(url_for('incharge_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get today's attendance records for this bus
    cursor.execute('''
        SELECT s.name, s.roll_number, a.marked_at 
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.date = DATE('now') AND a.bus_number = ?
        ORDER BY a.marked_at DESC
    ''', (session['bus_number'],))
    attendance_records = cursor.fetchall()
    
    # Get total students in this bus
    cursor.execute('SELECT COUNT(*) as total FROM students WHERE bus_number = ? AND is_active = 1', 
                  (session['bus_number'],))
    total_students = cursor.fetchone()['total']
    
    # Get today's present count
    cursor.execute('''
        SELECT COUNT(DISTINCT student_id) as present_count 
        FROM attendance 
        WHERE date = DATE('now') AND bus_number = ?
    ''', (session['bus_number'],))
    present_count = cursor.fetchone()['present_count']
    
    conn.close()
    
    return render_template('incharge_dashboard.html',
                         incharge_name=session['incharge_name'],
                         bus_number=session['bus_number'],
                         attendance_records=attendance_records,
                         total_students=total_students,
                         present_count=present_count,
                         current_date=date.today().isoformat())

# Face Recognition Attendance
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'photo' not in request.files:
        return jsonify({'success': False, 'message': 'No photo uploaded'})
    
    photo = request.files['photo']
    bus_number = request.form.get('bus_number')
    
    if not bus_number:
        return jsonify({'success': False, 'message': 'Bus number required'})
    
    if photo.filename == '':
        return jsonify({'success': False, 'message': 'No photo selected'})
    
    # Save temporary photo
    temp_filename = f"temp_{uuid.uuid4().hex[:8]}.jpg"
    temp_path = os.path.join('static/uploads/temp', temp_filename)
    photo.save(temp_path)
    
    try:
        # Get all students in this bus
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, roll_number, photo_path 
            FROM students 
            WHERE bus_number = ? AND is_active = 1
        ''', (bus_number,))
        students = cursor.fetchall()
        
        # Simulate face recognition (replace with actual face recognition)
        # In production, you would use: compare_faces_live(temp_path, student_photo_path)
        best_match = None
        best_confidence = 0.85  # Simulated high confidence
        
        # For demo, we'll just pick a random student
        import random
        if students:
            best_match = random.choice(students)
        
        # Log the recognition attempt
        cursor.execute('''
            INSERT INTO face_recognition_logs 
            (student_id, bus_number, confidence_score, verification_result, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (best_match['id'] if best_match else None, bus_number, best_confidence, bool(best_match), ''))
        
        # If match found, mark attendance
        if best_match:
            cursor.execute('''
                INSERT OR REPLACE INTO attendance 
                (student_id, date, status, bus_number, confidence_score, marked_by)
                VALUES (?, DATE('now'), 'Present', ?, ?, ?)
            ''', (best_match['id'], bus_number, best_confidence, 'face_recognition'))
            
            conn.commit()
            conn.close()
            
            # Clean up temp file
            os.remove(temp_path)
            
            return jsonify({
                'success': True, 
                'message': f'Attendance marked successfully!',
                'student_name': best_match['name'],
                'roll_number': best_match['roll_number'],
                'confidence': best_confidence
            })
        else:
            conn.commit()
            conn.close()
            os.remove(temp_path)
            return jsonify({
                'success': False, 
                'message': 'No matching student found. Please ensure clear face visibility.',
                'confidence': 0.0
            })
            
    except Exception as e:
        # Clean up temp file in case of error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'success': False, 'message': f'Error processing attendance: {str(e)}'})

# Excel Download
@app.route('/download_attendance_excel')
def download_attendance_excel():
    if 'incharge_id' not in session or session.get('user_type') != 'incharge':
        return redirect(url_for('incharge_login'))
    
    bus_number = session['bus_number']
    current_date = date.today().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get today's attendance data
    cursor.execute('''
        SELECT 
            s.roll_number as "Roll Number",
            s.name as "Student Name", 
            s.university_id as "University ID",
            a.status as "Status",
            a.marked_at as "Time",
            a.confidence_score as "Confidence Score"
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.date = DATE('now') AND a.bus_number = ?
        ORDER BY a.marked_at DESC
    ''', (bus_number,))
    
    attendance_data = cursor.fetchall()
    conn.close()
    
    # Create DataFrame
    df = pd.DataFrame([dict(row) for row in attendance_data])
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f'Attendance_{current_date}', index=False)
        
        # Get the worksheet
        worksheet = writer.sheets[f'Attendance_{current_date}']
        
        # Adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    
    filename = f"Bus_{bus_number}_Attendance_{current_date}.xlsx"
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

# Profile Management Routes
@app.route('/edit_profile')
def edit_profile():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students WHERE id = ?', (session['student_id'],))
    student = cursor.fetchone()
    conn.close()
    
    return render_template('edit_profile.html', student=student)

@app.route('/change_password')
def change_password():
    if 'student_id' not in session and 'incharge_id' not in session:
        return redirect(url_for('index'))
    
    return render_template('change_password.html')

@app.route('/incharge_edit_profile')
def incharge_edit_profile():
    if 'incharge_id' not in session:
        return redirect(url_for('incharge_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bus_incharge WHERE id = ?', (session['incharge_id'],))
    incharge = cursor.fetchone()
    conn.close()
    
    return render_template('incharge_edit_profile.html', incharge=incharge)

@app.route('/incharge_change_password')
def incharge_change_password():
    if 'incharge_id' not in session:
        return redirect(url_for('incharge_login'))
    
    return render_template('incharge_change_password.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

# Utility Functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

# Template filter for date formatting
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d'):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.strftime(format)
# Profile Update Routes
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    
    name = request.form['name']
    bus_number = request.form['bus_number']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Handle photo upload if provided
        photo_path = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename != '' and allowed_file(photo.filename):
                # Generate new filename
                filename = f"student_{session['student_roll_number']}_{uuid.uuid4().hex[:8]}.jpg"
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(photo_path)
        
        if photo_path:
            cursor.execute('''
                UPDATE students 
                SET name = ?, bus_number = ?, photo_path = ?, face_encoding = ?
                WHERE id = ?
            ''', (name, bus_number, photo_path, "simulated_encoding_updated", session['student_id']))
        else:
            cursor.execute('''
                UPDATE students 
                SET name = ?, bus_number = ?
                WHERE id = ?
            ''', (name, bus_number, session['student_id']))
        
        conn.commit()
        session['student_name'] = name
        flash('Profile updated successfully!', 'success')
        
    except Exception as e:
        conn.rollback()
        flash('Error updating profile', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('student_dashboard'))

@app.route('/update_password', methods=['POST'])
def update_password():
    if 'student_id' not in session and 'incharge_id' not in session:
        return redirect(url_for('index'))
    
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if 'student_id' in session:
            # Verify current password for student
            cursor.execute('SELECT password FROM students WHERE id = ?', (session['student_id'],))
            student = cursor.fetchone()
            
            if student and student['password'] == current_password:
                cursor.execute('UPDATE students SET password = ? WHERE id = ?', 
                             (new_password, session['student_id']))
                conn.commit()
                flash('Password updated successfully!', 'success')
            else:
                flash('Current password is incorrect', 'error')
                
        elif 'incharge_id' in session:
            # Verify current password for incharge
            cursor.execute('SELECT password FROM bus_incharge WHERE id = ?', (session['incharge_id'],))
            incharge = cursor.fetchone()
            
            if incharge and incharge['password'] == current_password:
                cursor.execute('UPDATE bus_incharge SET password = ? WHERE id = ?', 
                             (new_password, session['incharge_id']))
                conn.commit()
                flash('Password updated successfully!', 'success')
            else:
                flash('Current password is incorrect', 'error')
                
    except Exception as e:
        conn.rollback()
        flash('Error updating password', 'error')
    finally:
        conn.close()
    
    if 'student_id' in session:
        return redirect(url_for('student_dashboard'))
    else:
        return redirect(url_for('incharge_dashboard'))

@app.route('/update_incharge_profile', methods=['POST'])
def update_incharge_profile():
    if 'incharge_id' not in session:
        return redirect(url_for('incharge_login'))
    
    name = request.form['name']
    email = request.form['email']
    phone_number = request.form.get('phone_number', '')
    bus_password = request.form['bus_password']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE bus_incharge 
            SET name = ?, email = ?, phone_number = ?, bus_password = ?
            WHERE id = ?
        ''', (name, email, phone_number, bus_password, session['incharge_id']))
        
        conn.commit()
        session['incharge_name'] = name
        flash('Profile updated successfully!', 'success')
        
    except sqlite3.IntegrityError:
        conn.rollback()
        flash('Email already exists', 'error')
    except Exception as e:
        conn.rollback()
        flash('Error updating profile', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('incharge_dashboard'))

@app.route('/update_incharge_password', methods=['POST'])
def update_incharge_password():
    if 'incharge_id' not in session:
        return redirect(url_for('incharge_login'))
    
    return update_password()  # Reuse the same function
if __name__ == '__main__':
    app.run(debug=True)