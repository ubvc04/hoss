from flask import Blueprint, request, jsonify, g
import bcrypt
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..database import query_db, execute_db, dict_from_row
from ..middleware import create_token, jwt_required, log_audit
from ..config import Config

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _send_email(to_email, subject, html_body):
    """Send an email using SMTP."""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = Config.SMTP_EMAIL
    msg['To'] = to_email
    msg.attach(MIMEText(html_body, 'html'))

    with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
        server.starttls()
        server.login(Config.SMTP_EMAIL, Config.SMTP_PASSWORD)
        server.sendmail(Config.SMTP_EMAIL, to_email, msg.as_string())


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('identifier') or not data.get('password'):
        return jsonify({'error': 'Username/email/phone and password required'}), 400

    identifier = data['identifier'].strip()

    # Try to find user by username, email, or phone
    user = query_db(
        'SELECT u.*, r.name as role_name FROM users u JOIN roles r ON u.role_id=r.id WHERE u.username=? OR u.email=? OR u.phone=?',
        [identifier, identifier, identifier], one=True
    )

    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user['is_active']:
        return jsonify({'error': 'Account is deactivated. Contact hospital administration.'}), 403

    if not bcrypt.checkpw(data['password'].encode('utf-8'), user['password_hash'].encode('utf-8')):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = create_token(user['id'], user['username'], user['role_name'])

    execute_db('UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?', [user['id']])

    # Audit
    g.current_user = dict_from_row(user)
    g.current_user['role'] = user['role_name']
    log_audit('LOGIN', 'user', user['id'], f"User {user['username']} logged in")

    # Get profile info
    profile = _build_profile(user)

    return jsonify({
        'token': token,
        'user': profile
    }), 200


@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Create a new user account. Requires admin password for authorization."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    # Validate admin password
    admin_password = data.get('admin_password', '')
    if not admin_password:
        return jsonify({'error': 'Admin password is required to create accounts'}), 400

    admin_user = query_db(
        'SELECT u.*, r.name as role_name FROM users u JOIN roles r ON u.role_id=r.id WHERE r.name=? AND u.is_active=1',
        ['Admin'], one=True
    )
    if not admin_user or not bcrypt.checkpw(admin_password.encode('utf-8'), admin_user['password_hash'].encode('utf-8')):
        return jsonify({'error': 'Invalid admin password'}), 403

    # Validate required fields
    required = ['username', 'password', 'first_name', 'last_name', 'email', 'phone', 'role_id']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400

    username = data['username'].strip()
    email = data['email'].strip()
    phone = data['phone'].strip()

    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    # Check uniqueness
    existing = query_db('SELECT id FROM users WHERE username=?', [username], one=True)
    if existing:
        return jsonify({'error': 'Username already taken'}), 409

    existing_email = query_db('SELECT id FROM users WHERE email=?', [email], one=True)
    if existing_email:
        return jsonify({'error': 'Email already registered'}), 409

    password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user_id = execute_db(
        'INSERT INTO users (username, password_hash, email, phone, role_id, first_name, last_name, must_change_password) VALUES (?,?,?,?,?,?,?,0)',
        [username, password_hash, email, phone, int(data['role_id']), data['first_name'].strip(), data['last_name'].strip()]
    )

    # If patient role, create patient profile
    role = query_db('SELECT name FROM roles WHERE id=?', [int(data['role_id'])], one=True)
    if role and role['name'] == 'Patient':
        from ..utils import generate_mrn
        mrn = generate_mrn()
        dob = data.get('date_of_birth', '2000-01-01')
        gender = data.get('gender', 'Other')
        execute_db(
            '''INSERT INTO patients (user_id, mrn, first_name, last_name, date_of_birth, gender, phone, email, created_by)
               VALUES (?,?,?,?,?,?,?,?,?)''',
            [user_id, mrn, data['first_name'].strip(), data['last_name'].strip(),
             dob, gender, phone, email, admin_user['id']]
        )

    return jsonify({'message': 'Account created successfully', 'user_id': user_id}), 201


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Send a password reset link to the user's email."""
    data = request.get_json()
    if not data or not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400

    email = data['email'].strip()
    user = query_db('SELECT * FROM users WHERE email=? AND is_active=1', [email], one=True)

    # Always return success to prevent email enumeration
    if not user:
        return jsonify({'message': 'If the email exists, a reset link has been sent'}), 200

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    execute_db(
        'UPDATE users SET reset_token=?, reset_token_expiry=datetime("now", "+1 hour") WHERE id=?',
        [reset_token, user['id']]
    )

    # Send reset email
    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #2563eb;">🏥 Hospital Management System</h2>
        </div>
        <p>Hello <strong>{user['username']}</strong>,</p>
        <p>You requested a password reset. Click the button below to set a new password:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}" style="background: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">Reset Password</a>
        </div>
        <p style="font-size: 13px; color: #666;">This link expires in 1 hour. If you didn't request this, ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;" />
        <p style="font-size: 11px; color: #999; text-align: center;">Hospital Management System</p>
    </div>
    """

    try:
        _send_email(email, 'Password Reset - Hospital Management System', html_body)
    except Exception as e:
        return jsonify({'error': 'Failed to send email. Please try again later.'}), 500

    return jsonify({'message': 'If the email exists, a reset link has been sent'}), 200


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using the token from email."""
    data = request.get_json()
    if not data or not data.get('token') or not data.get('new_password'):
        return jsonify({'error': 'Token and new password required'}), 400

    if len(data['new_password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    user = query_db(
        'SELECT * FROM users WHERE reset_token=? AND reset_token_expiry > datetime("now") AND is_active=1',
        [data['token']], one=True
    )

    if not user:
        return jsonify({'error': 'Invalid or expired reset link'}), 400

    new_hash = bcrypt.hashpw(data['new_password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    execute_db(
        'UPDATE users SET password_hash=?, reset_token=NULL, reset_token_expiry=NULL, must_change_password=0, updated_at=CURRENT_TIMESTAMP WHERE id=?',
        [new_hash, user['id']]
    )

    return jsonify({'message': 'Password reset successfully. You can now login.'}), 200


@auth_bp.route('/roles', methods=['GET'])
def get_roles():
    """Get available roles for signup form."""
    roles = query_db('SELECT id, name, description FROM roles')
    return jsonify({'roles': [dict(r) for r in roles]}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required
def me():
    user = query_db(
        'SELECT u.*, r.name as role_name FROM users u JOIN roles r ON u.role_id=r.id WHERE u.id=?',
        [g.current_user['id']], one=True
    )
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': _build_profile(user)}), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required
def change_password():
    data = request.get_json()
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({'error': 'Current and new password required'}), 400

    if len(data['new_password']) < 6:
        return jsonify({'error': 'New password must be at least 6 characters'}), 400

    user = query_db('SELECT * FROM users WHERE id=?', [g.current_user['id']], one=True)
    if not bcrypt.checkpw(data['current_password'].encode('utf-8'), user['password_hash'].encode('utf-8')):
        return jsonify({'error': 'Current password is incorrect'}), 401

    new_hash = bcrypt.hashpw(data['new_password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    execute_db('UPDATE users SET password_hash=?, must_change_password=0, updated_at=CURRENT_TIMESTAMP WHERE id=?',
               [new_hash, g.current_user['id']])

    log_audit('PASSWORD_CHANGE', 'user', g.current_user['id'], 'Password changed')
    return jsonify({'message': 'Password changed successfully'}), 200


def _build_profile(user):
    """Build the user profile dict."""
    profile = {
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'phone': user['phone'],
        'role': user['role_name'],
        'is_active': user['is_active'],
        'must_change_password': user['must_change_password'],
        'last_login': user['last_login']
    }

    if user['role_name'] == 'Patient':
        patient = query_db('SELECT * FROM patients WHERE user_id=?', [user['id']], one=True)
        if patient:
            profile['patient_id'] = patient['id']
            profile['mrn'] = patient['mrn']
            profile['first_name'] = patient['first_name']
            profile['last_name'] = patient['last_name']
    elif user['role_name'] == 'Doctor':
        doctor = query_db('SELECT d.*, dep.name as department_name FROM doctors d LEFT JOIN departments dep ON d.department_id=dep.id WHERE d.user_id=?',
                          [user['id']], one=True)
        if doctor:
            profile['doctor_id'] = doctor['id']
            profile['first_name'] = doctor['first_name']
            profile['last_name'] = doctor['last_name']
            profile['specialization'] = doctor['specialization']
            profile['department'] = doctor['department_name']

    return profile
