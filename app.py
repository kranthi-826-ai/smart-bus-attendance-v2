import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import uuid
from PIL import Image
import io

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-2024')
app.config['UPLOAD_FOLDER'] = 'static/uploads/students'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

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
    
    # Students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT UNIQUE NOT NULL,
            university_id TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            bus_number TEXT NOT NULL,
            photo_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Attendance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date DATE NOT NULL,
            status TEXT NOT NULL,
            bus_number TEXT NOT NULL,
            marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id),
            UNIQUE(student_id, date)
        )
    ''')
    
    # Bus incharge table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bus_incharge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            bus_number TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student_signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        name = request.form['name']
        roll_number = request.form['roll_number']
        university_id = request.form['university_id']
        password = request.form['password']
        bus_number = request.form['bus_number']
        
        if 'photo' not in request.files:
            flash('No photo uploaded', 'error')
            return render_template('student_signup.html')
        
        photo = request.files['photo']
        
        if photo.filename == '':
            flash('No photo selected', 'error')
            return render_template('student_signup.html')
        
        if photo and allowed_file(photo.filename):
            # Validate image using PIL
            try:
                img = Image.open(photo)
                img.verify()  # Verify it's a valid image
            except Exception as e:
                flash('Invalid image file', 'error')
                return render_template('student_signup.html')
            
            # Reset file pointer
            photo.seek(0)
            
            # Save photo
            filename = f"student_{roll_number}.jpg"
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)
            
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
                
            except sqlite3.IntegrityError:
                flash('Roll number or University ID already exists', 'error')
            except Exception as e:
                flash('Error registering student', 'error')
            finally:
                conn.close()
        else:
            flash('Please upload a valid JPG/PNG image', 'error')
    
    return render_template('student_signup.html')

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

@app.route('/student_dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT date, status, bus_number FROM attendance 
        WHERE student_id = ? ORDER BY date DESC LIMIT 10
    ''', (session['student_id'],))
    attendance_records = cursor.fetchall()
    conn.close()
    
    return render_template('student_dashboard.html', 
                         student_name=session['student_name'],
                         attendance_records=attendance_records)

# Simple attendance marking (manual for now)
@app.route('/mark_attendance_manual', methods=['POST'])
def mark_attendance_manual():
    if 'student_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    student_id = session['student_id']
    bus_number = request.form.get('bus_number', 'BUS001')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO attendance (student_id, date, status, bus_number)
            VALUES (?, DATE('now'), 'Present', ?)
        ''', (student_id, bus_number))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Attendance marked successfully!'
        })
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif'}

if __name__ == '__main__':
    app.run(debug=True)