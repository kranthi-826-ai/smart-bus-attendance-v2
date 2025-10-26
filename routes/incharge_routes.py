from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from models.models import Database
from utils.otp_generator import OTPHandler
import hashlib

incharge_bp = Blueprint('incharge', __name__)
db = Database()
otp_handler = OTPHandler()

@incharge_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            data = request.json
            name = data.get('name')
            email = data.get('email')
            phone = data.get('phone')
            bus_number = int(data.get('bus_number'))
            
            # Check if bus number already assigned
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bus_incharges WHERE bus_number = ?", (bus_number,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Bus number already assigned to another incharge'})
            
            # Check if email or phone already exists
            cursor.execute("SELECT * FROM bus_incharges WHERE email = ? OR phone = ?", (email, phone))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Email or phone number already registered'})
            
            # Generate and send OTP
            otp, otp_hash = otp_handler.generate_otp(phone, email)
            
            # Store in session for verification
            session['signup_data'] = {
                'name': name,
                'email': email,
                'phone': phone,
                'bus_number': bus_number,
                'otp_hash': otp_hash
            }
            
            # Send OTP
            otp_handler.send_otp_sms(phone, otp)
            otp_handler.send_otp_email(email, otp)
            
            conn.close()
            
            return jsonify({
                'success': True, 
                'message': 'OTP sent successfully! Use OTP: 123456',
                'otp_hash': otp_hash,
                'demo_otp': '123456'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Signup error: {str(e)}'})
    
    return render_template('incharge/signup.html')

@incharge_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data = request.json
        entered_otp = data.get('otp')
        bus_password = data.get('bus_password')
        
        # Get signup data from session
        signup_data = session.get('signup_data')
        if not signup_data:
            return jsonify({'success': False, 'message': 'Session expired. Please start over.'})
        
        otp_hash = signup_data['otp_hash']
        
        # Verify OTP
        verified, message = otp_handler.verify_otp(otp_hash, entered_otp)
        
        if not verified:
            return jsonify({'success': False, 'message': message})
        
        # Complete registration
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bus_incharges (name, email, phone, bus_number, bus_password)
            VALUES (?, ?, ?, ?, ?)
        ''', (signup_data['name'], signup_data['email'], signup_data['phone'], 
              signup_data['bus_number'], bus_password))
        
        conn.commit()
        conn.close()
        
        # Clear session
        session.pop('signup_data', None)
        
        return jsonify({
            'success': True, 
            'message': 'Registration completed successfully! You can now login.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Verification error: {str(e)}'})

@incharge_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            login_id = request.form.get('login_id')
            login_type = request.form.get('login_type')
            
            # Find incharge by email or phone
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if login_type == 'email':
                cursor.execute("SELECT * FROM bus_incharges WHERE email = ?", (login_id,))
            else:
                cursor.execute("SELECT * FROM bus_incharges WHERE phone = ?", (login_id,))
            
            incharge = cursor.fetchone()
            conn.close()
            
            if not incharge:
                return jsonify({'success': False, 'message': 'Incharge not found'})
            
            # Generate and send OTP
            otp, otp_hash = otp_handler.generate_otp(incharge[3], incharge[2])
            
            # Store in session
            session['login_data'] = {
                'otp_hash': otp_hash,
                'incharge_id': incharge[0]
            }
            
            # Send OTP
            if login_type == 'email':
                otp_handler.send_otp_email(login_id, otp)
            else:
                otp_handler.send_otp_sms(login_id, otp)
            
            return jsonify({
                'success': True, 
                'message': 'OTP sent successfully! Use OTP: 123456',
                'otp_hash': otp_hash,
                'incharge_id': incharge[0],
                'demo_otp': '123456'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Login error: {str(e)}'})
    
    return render_template('incharge/login.html')

@incharge_bp.route('/verify-login', methods=['POST'])
def verify_login():
    try:
        data = request.json
        entered_otp = data.get('otp')
        
        # Get login data from session
        login_data = session.get('login_data')
        if not login_data:
            return jsonify({'success': False, 'message': 'Session expired. Please login again.'})
        
        otp_hash = login_data['otp_hash']
        incharge_id = login_data['incharge_id']
        
        # Verify OTP
        verified, message = otp_handler.verify_otp(otp_hash, entered_otp)
        
        if not verified:
            return jsonify({'success': False, 'message': message})
        
        # Get incharge data
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, bus_number FROM bus_incharges WHERE id = ?
        ''', (incharge_id,))
        
        incharge = cursor.fetchone()
        conn.close()
        
        if incharge:
            session['incharge_id'] = incharge[0]
            session['incharge_name'] = incharge[1]
            session['bus_number'] = incharge[2]
            session['role'] = 'incharge'
            
            # Clear login session
            session.pop('login_data', None)
            
            return jsonify({'success': True, 'message': 'Login successful!'})
        else:
            return jsonify({'success': False, 'message': 'Incharge not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Login verification error: {str(e)}'})

@incharge_bp.route('/dashboard')
def dashboard():
    if 'incharge_id' not in session or session.get('role') != 'incharge':
        return redirect(url_for('incharge.login'))
    
    # Get bus statistics
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Count students in this bus
    cursor.execute("SELECT COUNT(*) FROM students WHERE bus_number = ?", (session['bus_number'],))
    student_count = cursor.fetchone()[0]
    
    # Today's attendance count
    cursor.execute('''
        SELECT COUNT(*) FROM attendance 
        WHERE bus_number = ? AND date = DATE('now')
    ''', (session['bus_number'],))
    today_attendance = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('incharge/dashboard.html',
                         incharge_name=session.get('incharge_name'),
                         bus_number=session.get('bus_number'),
                         student_count=student_count,
                         today_attendance=today_attendance)