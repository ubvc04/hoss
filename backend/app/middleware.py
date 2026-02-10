from functools import wraps
from flask import request, jsonify, g
import jwt
import datetime
from .config import Config
from .database import query_db, dict_from_row, execute_db


def decode_token(token):
    """Decode a JWT token."""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def create_token(user_id, username, role_name):
    """Create a JWT token."""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role_name,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')


def jwt_required(f):
    """Decorator to require JWT authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]

        if not token:
            return jsonify({'error': 'Authentication required'}), 401

        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        user = query_db('SELECT u.*, r.name as role_name FROM users u JOIN roles r ON u.role_id=r.id WHERE u.id=? AND u.is_active=1',
                        [payload['user_id']], one=True)
        if not user:
            return jsonify({'error': 'User not found or inactive'}), 401

        g.current_user = dict_from_row(user)
        g.current_user['role'] = user['role_name']
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """Decorator to require specific roles."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, 'current_user') or g.current_user is None:
                return jsonify({'error': 'Authentication required'}), 401
            if g.current_user['role'] not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def get_patient_id_for_user(user_id):
    """Get the patient_id for a user (if they are a patient)."""
    patient = query_db('SELECT id FROM patients WHERE user_id=?', [user_id], one=True)
    return patient['id'] if patient else None


def get_doctor_id_for_user(user_id):
    """Get the doctor_id for a user (if they are a doctor)."""
    doctor = query_db('SELECT id FROM doctors WHERE user_id=?', [user_id], one=True)
    return doctor['id'] if doctor else None


def log_audit(action, resource_type=None, resource_id=None, details=None):
    """Log an audit event."""
    user_id = g.current_user['id'] if hasattr(g, 'current_user') and g.current_user else None
    username = g.current_user['username'] if hasattr(g, 'current_user') and g.current_user else 'system'
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')[:255]

    execute_db(
        '''INSERT INTO audit_logs (user_id, username, action, resource_type, resource_id, details, ip_address, user_agent)
           VALUES (?,?,?,?,?,?,?,?)''',
        [user_id, username, action, resource_type, resource_id, details, ip_address, user_agent]
    )
