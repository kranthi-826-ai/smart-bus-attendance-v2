import sqlite3

# Replace with your actual database file name, for example: "smart_bus_attendance.db"
db_path = "database.db"

# Replace with the student's university ID you want to delete
university_id_to_delete = "2420030539"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("DELETE FROM students WHERE university_id = ?", (university_id_to_delete,))
conn.commit()
conn.close()

print(f"Deleted student with university ID: {university_id_to_delete}")
