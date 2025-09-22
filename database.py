import sqlite3

def create_database():
    conn = sqlite3.connect('bus_attendance.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS buses (
        bus_id INTEGER PRIMARY KEY AUTOINCREMENT,
        bus_number TEXT NOT NULL UNIQUE,
        route TEXT,
        password TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS incharges (
        incharge_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        bus_id INTEGER,
        FOREIGN KEY (bus_id) REFERENCES buses (bus_id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        roll_number TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,  -- ADDED PASSWORD FIELD
        bus_id INTEGER,
        face_encoding_data TEXT,
        id_card_image_path TEXT,
        FOREIGN KEY (bus_id) REFERENCES buses (bus_id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS valid_university_numbers (  -- NEW TABLE
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_number TEXT NOT NULL UNIQUE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        bus_id INTEGER,
        date TEXT NOT NULL,
        status TEXT DEFAULT 'Present',
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students (student_id),
        FOREIGN KEY (bus_id) REFERENCES buses (bus_id)
    )
    ''')

    # Insert sample buses
    cursor.execute("INSERT OR IGNORE INTO buses (bus_number, route, password) VALUES ('BUS001', 'Route A - Downtown', 'bus001pass')")
    cursor.execute("INSERT OR IGNORE INTO buses (bus_number, route, password) VALUES ('BUS002', 'Route B - Uptown', 'bus002pass')")
    cursor.execute("INSERT OR IGNORE INTO buses (bus_number, route, password) VALUES ('BUS003', 'Route C - Suburbs', 'bus003pass')")

    # Insert valid university numbers (REPLACE WITH YOUR ACTUAL NUMBERS)
    valid_numbers = [
        '2420030539',
        '2420030440', 
        '2420030546',
        # Add all your valid numbers here
    ]
    
    for roll_number in valid_numbers:
        try:
            cursor.execute("INSERT OR IGNORE INTO valid_university_numbers (roll_number) VALUES (?)", 
                          (roll_number,))
        except sqlite3.IntegrityError:
            pass  # Already exists

    conn.commit()
    conn.close()
    print("Database and tables created successfully!")

if __name__ == "__main__":
    create_database()