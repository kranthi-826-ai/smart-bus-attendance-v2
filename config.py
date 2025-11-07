import os
from datetime import timedelta

class Config:
    """Base configuration for PythonAnywhere deployment"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///attendance.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_REFRESH_EACH_REQUEST = True
    
    # Upload folder
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Face recognition thresholds (for face-recognition library)
    FACE_DISTANCE_THRESHOLD = 0.6
    MIN_FACE_CONFIDENCE = 0.7

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Select config
config_env = os.environ.get('FLASK_ENV', 'development')
if config_env == 'production':
    config = ProductionConfig
elif config_env == 'testing':
    config = TestingConfig
else:
    config = DevelopmentConfig
