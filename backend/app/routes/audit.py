from flask import Blueprint, request, jsonify, g
from ..database import query_db, dicts_from_rows
from ..middleware import jwt_required, role_required
from ..utils import parse_pagination

audit_bp = Blueprint('audit', __name__, url_prefix='/api/audit-logs')


@audit_bp.route('', methods=['GET'])
@jwt_required
@role_required('Admin')
def list_audit_logs():
    page, per_page = parse_pagination(request)

    query = 'SELECT * FROM audit_logs WHERE 1=1'
    args = []

    user_id = request.args.get('user_id', type=int)
    if user_id:
        query += ' AND user_id=?'
        args.append(user_id)

    action = request.args.get('action')
    if action:
        query += ' AND action LIKE ?'
        args.append(f'%{action}%')

    resource_type = request.args.get('resource_type')
    if resource_type:
        query += ' AND resource_type=?'
        args.append(resource_type)

    date_from = request.args.get('date_from')
    if date_from:
        query += ' AND created_at >= ?'
        args.append(date_from)

    date_to = request.args.get('date_to')
    if date_to:
        query += ' AND created_at <= ?'
        args.append(date_to + ' 23:59:59')

    count_q = query.replace('SELECT *', 'SELECT COUNT(*) as cnt')
    total = query_db(count_q, args, one=True)['cnt']

    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    args.extend([per_page, (page - 1) * per_page])

    logs = dicts_from_rows(query_db(query, args))
    return jsonify({'audit_logs': logs, 'total': total, 'page': page, 'per_page': per_page}), 200
