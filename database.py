import sqlite3
from datetime import datetime

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
    
    # Students Table (REMOVED roll_number)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
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