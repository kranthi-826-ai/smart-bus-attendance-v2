import sqlite3

# Your database file name
db_path = "database.db"  # Change this to your actual database file name

# University ID of the student you want to delete attendance for
university_id_to_delete = "2420030349"  # The same ID as you used in delete_student.py

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Delete the attendance records for this student
cursor.execute("DELETE FROM attendance WHERE university_id = ?", (university_id_to_delete,))
conn.commit()
conn.close()

print(f"Deleted all attendance for student ID: {university_id_to_delete}")
