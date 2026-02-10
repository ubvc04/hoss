import os
import secrets

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))

    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', secrets.token_hex(32))
    JWT_ACCESS_TOKEN_EXPIRES = 3600 * 8  # 8 hours
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    DATABASE_PATH = os.path.join(PROJECT_DIR, 'hospital.db')
    SCHEMA_PATH = os.path.join(PROJECT_DIR, 'migrations', 'schema.sql')

    UPLOAD_FOLDER = os.path.join(PROJECT_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'dcm', 'doc', 'docx'}

    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')

    # SMTP Configuration
    SMTP_EMAIL = 'baveshchowdary1@gmail.com'
    SMTP_PASSWORD = 'snyr vgat cycn fztt'
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
