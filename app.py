from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from models.models import Database
from routes.student_routes import student_bp
from routes.incharge_routes import incharge_bp
from routes.attendance_routes import attendance_bp
import os
from datetime import timedelta
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db = Database()

# Register blueprints
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(incharge_bp, url_prefix='/incharge')
app.register_blueprint(attendance_bp, url_prefix='/attendance')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/profile')
def profile():
    if 'student_id' in session and session.get('role') == 'student':
        return redirect(url_for('student.dashboard'))
    elif 'incharge_id' in session and session.get('role') == 'incharge':
        return redirect(url_for('incharge.dashboard'))
    else:
        return redirect(url_for('home'))


if __name__ == '__main__':
    # Create upload directories
    os.makedirs('static/uploads/faces', exist_ok=True)
    os.makedirs('static/uploads/profiles', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)