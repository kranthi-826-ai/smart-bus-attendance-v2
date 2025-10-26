import sqlite3
from datetime import datetime
import hashlib
import os

class Database:
    def __init__(self, db_path='database.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                university_id TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                bus_number INTEGER NOT NULL,
                bus_password TEXT NOT NULL,
                face_encoding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bus_number) REFERENCES buses(bus_number)
            )
        ''')
        
        # Bus incharges table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bus_incharges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                bus_number INTEGER UNIQUE NOT NULL,
                bus_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Buses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS buses (
                bus_number INTEGER PRIMARY KEY,
                route TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Attendance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                university_id TEXT NOT NULL,
                bus_number INTEGER NOT NULL,
                date DATE NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'Present',
                FOREIGN KEY (university_id) REFERENCES students(university_id)
            )
        ''')
        
        # Insert default buses
        for bus_num in range(1, 6):
            cursor.execute('INSERT OR IGNORE INTO buses (bus_number) VALUES (?)', (bus_num,))
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)