from flask import Blueprint, request, jsonify, g
from ..database import query_db, execute_db, dicts_from_rows
from ..middleware import jwt_required, log_audit
from ..utils import parse_pagination

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


@notifications_bp.route('', methods=['GET'])
@jwt_required
def list_notifications():
    page, per_page = parse_pagination(request)
    unread_only = request.args.get('unread', '').lower() == 'true'

    query = 'SELECT * FROM notifications WHERE user_id=?'
    args = [g.current_user['id']]

    if unread_only:
        query += ' AND is_read=0'

    count_q = query.replace('SELECT *', 'SELECT COUNT(*) as cnt')
    total = query_db(count_q, args, one=True)['cnt']

    unread_count = query_db('SELECT COUNT(*) as cnt FROM notifications WHERE user_id=? AND is_read=0',
                            [g.current_user['id']], one=True)['cnt']

    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    args.extend([per_page, (page - 1) * per_page])

    notifications = dicts_from_rows(query_db(query, args))
    return jsonify({
        'notifications': notifications,
        'total': total,
        'unread_count': unread_count,
        'page': page,
        'per_page': per_page
    }), 200


@notifications_bp.route('/<int:notif_id>/read', methods=['PUT'])
@jwt_required
def mark_read(notif_id):
    notif = query_db('SELECT * FROM notifications WHERE id=? AND user_id=?',
                     [notif_id, g.current_user['id']], one=True)
    if not notif:
        return jsonify({'error': 'Notification not found'}), 404

    execute_db('UPDATE notifications SET is_read=1 WHERE id=?', [notif_id])
    return jsonify({'message': 'Marked as read'}), 200


@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required
def mark_all_read():
    execute_db('UPDATE notifications SET is_read=1 WHERE user_id=? AND is_read=0',
               [g.current_user['id']])
    return jsonify({'message': 'All notifications marked as read'}), 200
