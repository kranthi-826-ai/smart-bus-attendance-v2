import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    DATABASE_PATH = 'database.db'
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Face recognition settings
    FACE_RECOGNITION_TOLERANCE = 0.6
    FACE_DETECTION_MODEL = 'hog'  # or 'cnn' for better accuracy (slower)
    
    # OTP settings
    OTP_EXPIRY_MINUTES = 10
    OTP_LENGTH = 6

class ProductionConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = True