from flask import Blueprint, request, jsonify, g
import bcrypt
from ..database import query_db, execute_db, dicts_from_rows
from ..middleware import jwt_required, role_required, log_audit
from ..utils import validate_required, validate_email, parse_pagination

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


@users_bp.route('', methods=['GET'])
@jwt_required
@role_required('Admin')
def list_users():
    page, per_page = parse_pagination(request)
    role_filter = request.args.get('role', '')
    search = request.args.get('search', '')

    query = '''SELECT u.id, u.username, u.email, u.phone, u.is_active, u.last_login, u.created_at,
                      r.name as role_name
               FROM users u JOIN roles r ON u.role_id=r.id WHERE 1=1'''
    args = []

    if role_filter:
        query += ' AND r.name=?'
        args.append(role_filter)
    if search:
        query += ' AND (u.username LIKE ? OR u.email LIKE ?)'
        args.extend([f'%{search}%', f'%{search}%'])

    count_q = query.replace('SELECT u.id, u.username, u.email, u.phone, u.is_active, u.last_login, u.created_at,\n                      r.name as role_name', 'SELECT COUNT(*) as cnt')
    total = query_db(count_q, args, one=True)['cnt']

    query += ' ORDER BY u.created_at DESC LIMIT ? OFFSET ?'
    args.extend([per_page, (page - 1) * per_page])

    users = dicts_from_rows(query_db(query, args))
    return jsonify({'users': users, 'total': total, 'page': page, 'per_page': per_page}), 200


@users_bp.route('', methods=['POST'])
@jwt_required
@role_required('Admin')
def create_user():
    data = request.get_json()
    valid, msg = validate_required(data, ['username', 'password', 'role'])
    if not valid:
        return jsonify({'error': msg}), 400

    if data.get('email') and not validate_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400

    existing = query_db('SELECT id FROM users WHERE username=?', [data['username']], one=True)
    if existing:
        return jsonify({'error': 'Username already exists'}), 409

    role = query_db('SELECT id FROM roles WHERE name=?', [data['role']], one=True)
    if not role:
        return jsonify({'error': 'Invalid role'}), 400

    pw_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user_id = execute_db(
        'INSERT INTO users (username, password_hash, email, phone, role_id) VALUES (?,?,?,?,?)',
        [data['username'], pw_hash, data.get('email'), data.get('phone'), role['id']]
    )

    log_audit('CREATE_USER', 'user', user_id, f"Created user {data['username']} with role {data['role']}")
    return jsonify({'message': 'User created', 'user_id': user_id}), 201


@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required
@role_required('Admin')
def update_user(user_id):
    data = request.get_json()
    user = query_db('SELECT * FROM users WHERE id=?', [user_id], one=True)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    updates = []
    args = []

    if 'email' in data:
        if data['email'] and not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        updates.append('email=?')
        args.append(data['email'])
    if 'phone' in data:
        updates.append('phone=?')
        args.append(data['phone'])
    if 'is_active' in data:
        updates.append('is_active=?')
        args.append(1 if data['is_active'] else 0)
    if 'password' in data and data['password']:
        pw_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        updates.append('password_hash=?')
        args.append(pw_hash)
        updates.append('must_change_password=1')

    if not updates:
        return jsonify({'error': 'No fields to update'}), 400

    updates.append('updated_at=CURRENT_TIMESTAMP')
    args.append(user_id)

    execute_db(f"UPDATE users SET {', '.join(updates)} WHERE id=?", args)
    log_audit('UPDATE_USER', 'user', user_id, f"Updated user {user['username']}")
    return jsonify({'message': 'User updated'}), 200


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required
@role_required('Admin')
def deactivate_user(user_id):
    user = query_db('SELECT * FROM users WHERE id=?', [user_id], one=True)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user['id'] == g.current_user['id']:
        return jsonify({'error': 'Cannot deactivate your own account'}), 400

    execute_db('UPDATE users SET is_active=0, updated_at=CURRENT_TIMESTAMP WHERE id=?', [user_id])
    log_audit('DEACTIVATE_USER', 'user', user_id, f"Deactivated user {user['username']}")
    return jsonify({'message': 'User deactivated'}), 200


@users_bp.route('/roles', methods=['GET'])
@jwt_required
@role_required('Admin')
def list_roles():
    roles = dicts_from_rows(query_db('SELECT * FROM roles ORDER BY id'))
    return jsonify({'roles': roles}), 200
