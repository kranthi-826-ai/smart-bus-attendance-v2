import sqlite3

def get_db_connection():
    conn = sqlite3.connect('bus_attendance.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Students table with photo_path
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