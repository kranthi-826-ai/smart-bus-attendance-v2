from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from models.models import Database
from utils.face_encoder import FaceEncoder
import cv2
import numpy as np
import base64
import os
from datetime import datetime
import csv
from io import StringIO

attendance_bp = Blueprint('attendance', __name__)
db = Database()
face_encoder = FaceEncoder()

@attendance_bp.route('/scan')
def scan_attendance():
    if 'incharge_id' not in session or session.get('role') != 'incharge':
        return redirect(url_for('incharge.login'))
    
    return render_template('attendance/scan.html',
                         bus_number=session.get('bus_number'),
                         incharge_name=session.get('incharge_name'))

@attendance_bp.route('/process-attendance', methods=['POST'])
def process_attendance():
    if 'incharge_id' not in session or session.get('role') != 'incharge':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        data = request.json
        image_data = data.get('image')
        bus_number = session.get('bus_number')
        
        # Convert base64 image to file
        image_data = image_data.split(',')[1]  # Remove data:image/jpeg;base64,
        image_bytes = base64.b64decode(image_data)
        
        # Save temporary image
        temp_path = f"static/uploads/temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        with open(temp_path, 'wb') as f:
            f.write(image_bytes)
        
        # Get all students from this bus
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT university_id, name, face_encoding 
            FROM students 
            WHERE bus_number = ?
        ''', (bus_number,))
        
        students = cursor.fetchall()
        conn.close()
        
        if not students:
            os.remove(temp_path)
            return jsonify({'success': False, 'message': 'No students found in this bus'})
        
        # Find matching student
        matched_student = None
        confidence = 0
        
        for student in students:
            university_id, name, stored_encoding = student
            
            # Compare faces
            is_match, message = face_encoder.verify_face_match(temp_path, stored_encoding)
            
            if is_match:
                matched_student = {
                    'university_id': university_id,
                    'name': name
                }
                break
        
        # Cleanup temp file
        os.remove(temp_path)
        
        if matched_student:
            # Mark attendance
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Check if already marked today
            cursor.execute('''
                SELECT * FROM attendance 
                WHERE university_id = ? AND date = DATE('now') AND bus_number = ?
            ''', (matched_student['university_id'], bus_number))
            
            if not cursor.fetchone():
                # Insert attendance
                cursor.execute('''
                    INSERT INTO attendance (university_id, bus_number, date)
                    VALUES (?, ?, DATE('now'))
                ''', (matched_student['university_id'], bus_number))
                
                conn.commit()
            
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'Attendance marked for {matched_student["name"]}',
                'student': matched_student,
                'already_marked': False
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No matching student found in this bus'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Attendance error: {str(e)}'})

@attendance_bp.route('/today-attendance')
def today_attendance():
    if 'incharge_id' not in session or session.get('role') != 'incharge':
        return redirect(url_for('incharge.login'))
    
    bus_number = session.get('bus_number')
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get today's attendance
    cursor.execute('''
        SELECT s.university_id, s.name, a.timestamp 
        FROM attendance a
        JOIN students s ON a.university_id = s.university_id
        WHERE a.date = DATE('now') AND a.bus_number = ?
        ORDER BY a.timestamp DESC
    ''', (bus_number,))
    
    attendance_data = cursor.fetchall()
    
    # Get all students in this bus for comparison
    cursor.execute('''
        SELECT university_id, name FROM students 
        WHERE bus_number = ?
    ''', (bus_number,))
    
    all_students = cursor.fetchall()
    conn.close()
    
    # Calculate present vs absent
    present_count = len(attendance_data)
    total_count = len(all_students)
    absent_count = total_count - present_count
    
    return jsonify({
        'attendance': [
            {
                'university_id': row[0],
                'name': row[1],
                'time': row[2]
            } for row in attendance_data
        ],
        'stats': {
            'present': present_count,
            'absent': absent_count,
            'total': total_count
        }
    })

@attendance_bp.route('/download-attendance')
def download_attendance():
    if 'incharge_id' not in session or session.get('role') != 'incharge':
        return redirect(url_for('incharge.login'))
    
    bus_number = session.get('bus_number')
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get attendance data
    cursor.execute('''
        SELECT s.university_id, s.name, a.timestamp 
        FROM attendance a
        JOIN students s ON a.university_id = s.university_id
        WHERE a.date = ? AND a.bus_number = ?
        ORDER BY s.university_id
    ''', (date, bus_number))
    
    attendance_data = cursor.fetchall()
    conn.close()
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['University ID', 'Name', 'Timestamp', 'Status'])
    
    # Write data
    for row in attendance_data:
        writer.writerow([row[0], row[1], row[2], 'Present'])
    
    # Prepare response
    output.seek(0)
    
    return jsonify({
        'success': True,
        'csv_data': output.getvalue(),
        'filename': f'attendance_bus_{bus_number}_{date}.csv'
    })

@attendance_bp.route('/change-bus-password', methods=['POST'])
def change_bus_password():
    if 'incharge_id' not in session or session.get('role') != 'incharge':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        data = request.json
        new_password = data.get('new_password')
        bus_number = session.get('bus_number')
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Update bus password
        cursor.execute('''
            UPDATE bus_incharges 
            SET bus_password = ? 
            WHERE bus_number = ?
        ''', (new_password, bus_number))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Bus password updated successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating password: {str(e)}'})