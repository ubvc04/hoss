import os
from flask import Blueprint, request, jsonify, g, send_file
from ..database import query_db, execute_db, dicts_from_rows, dict_from_row
from ..middleware import jwt_required, role_required, get_patient_id_for_user, log_audit
from ..utils import validate_required, generate_invoice_number, parse_pagination, allowed_file, save_upload
from ..config import Config

billing_bp = Blueprint('billing', __name__, url_prefix='/api/invoices')


@billing_bp.route('', methods=['GET'])
@jwt_required
def list_invoices():
    role = g.current_user['role']
    patient_id = request.args.get('patient_id', type=int)
    page, per_page = parse_pagination(request)

    query = '''SELECT i.*, p.mrn, p.first_name || ' ' || p.last_name as patient_name
               FROM invoices i JOIN patients p ON i.patient_id=p.id WHERE 1=1'''
    args = []

    if role == 'Patient':
        pid = get_patient_id_for_user(g.current_user['id'])
        query += ' AND i.patient_id=?'
        args.append(pid)
    elif patient_id:
        query += ' AND i.patient_id=?'
        args.append(patient_id)

    status = request.args.get('payment_status')
    if status:
        query += ' AND i.payment_status=?'
        args.append(status)

    count_q = query.replace("SELECT i.*, p.mrn, p.first_name || ' ' || p.last_name as patient_name", 'SELECT COUNT(*) as cnt')
    total = query_db(count_q, args, one=True)['cnt']

    query += ' ORDER BY i.invoice_date DESC LIMIT ? OFFSET ?'
    args.extend([per_page, (page - 1) * per_page])

    invoices = dicts_from_rows(query_db(query, args))
    return jsonify({'invoices': invoices, 'total': total, 'page': page, 'per_page': per_page}), 200


@billing_bp.route('/<int:invoice_id>', methods=['GET'])
@jwt_required
def get_invoice(invoice_id):
    invoice = query_db(
        '''SELECT i.*, p.mrn, p.first_name || ' ' || p.last_name as patient_name
           FROM invoices i JOIN patients p ON i.patient_id=p.id WHERE i.id=?''',
        [invoice_id], one=True)

    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404

    role = g.current_user['role']
    if role == 'Patient':
        pid = get_patient_id_for_user(g.current_user['id'])
        if invoice['patient_id'] != pid:
            return jsonify({'error': 'Access denied'}), 403

    result = dict_from_row(invoice)
    items = dicts_from_rows(query_db('SELECT * FROM invoice_items WHERE invoice_id=?', [invoice_id]))
    result['items'] = items

    # Attach files
    result['files'] = dicts_from_rows(query_db('SELECT id, file_name, original_name, file_size, mime_type FROM invoice_files WHERE invoice_id=?', [invoice_id]))

    # Insurance info
    insurance = query_db('SELECT * FROM insurance WHERE patient_id=? AND is_active=1',
                         [invoice['patient_id']], one=True)
    result['insurance'] = dict_from_row(insurance) if insurance else None

    log_audit('VIEW_INVOICE', 'invoice', invoice_id)
    return jsonify({'invoice': result}), 200


@billing_bp.route('', methods=['POST'])
@jwt_required
@role_required('Admin', 'Staff')
def create_invoice():
    data = request.get_json()
    valid, msg = validate_required(data, ['patient_id'])
    if not valid:
        return jsonify({'error': msg}), 400

    invoice_number = generate_invoice_number()

    invoice_id = execute_db(
        '''INSERT INTO invoices (invoice_number, patient_id, visit_id, due_date, notes, created_by)
           VALUES (?,?,?,?,?,?)''',
        [invoice_number, data['patient_id'], data.get('visit_id'),
         data.get('due_date'), data.get('notes'), g.current_user['id']]
    )

    # Add items if provided
    if data.get('items'):
        _add_items(invoice_id, data['items'])

    # Notify patient
    patient = query_db('SELECT user_id FROM patients WHERE id=?', [data['patient_id']], one=True)
    if patient and patient['user_id']:
        execute_db(
            '''INSERT INTO notifications (user_id, title, message, notification_type, reference_type, reference_id)
               VALUES (?,?,?,?,?,?)''',
            [patient['user_id'], 'New Invoice',
             f'A new invoice {invoice_number} has been generated.',
             'Billing', 'invoice', invoice_id]
        )

    log_audit('CREATE_INVOICE', 'invoice', invoice_id, f"Invoice {invoice_number}")
    return jsonify({'message': 'Invoice created', 'id': invoice_id, 'invoice_number': invoice_number}), 201


@billing_bp.route('/<int:invoice_id>/items', methods=['POST'])
@jwt_required
@role_required('Admin', 'Staff')
def add_items(invoice_id):
    invoice = query_db('SELECT * FROM invoices WHERE id=?', [invoice_id], one=True)
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404

    data = request.get_json()
    if not data.get('items'):
        return jsonify({'error': 'items required'}), 400

    _add_items(invoice_id, data['items'])

    log_audit('ADD_INVOICE_ITEMS', 'invoice', invoice_id)
    return jsonify({'message': 'Items added'}), 200


@billing_bp.route('/<int:invoice_id>/payment', methods=['PUT'])
@jwt_required
@role_required('Admin', 'Staff')
def update_payment(invoice_id):
    data = request.get_json()
    invoice = query_db('SELECT * FROM invoices WHERE id=?', [invoice_id], one=True)
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404

    updates = []
    args = []

    if 'paid_amount' in data:
        updates.append('paid_amount=?')
        args.append(data['paid_amount'])
    if 'payment_status' in data:
        updates.append('payment_status=?')
        args.append(data['payment_status'])
    if 'payment_method' in data:
        updates.append('payment_method=?')
        args.append(data['payment_method'])
    if 'payment_date' in data:
        updates.append('payment_date=?')
        args.append(data['payment_date'])
    if 'insurance_claim_status' in data:
        updates.append('insurance_claim_status=?')
        args.append(data['insurance_claim_status'])
    if 'insurance_claim_amount' in data:
        updates.append('insurance_claim_amount=?')
        args.append(data['insurance_claim_amount'])
    if 'discount_amount' in data:
        updates.append('discount_amount=?')
        args.append(data['discount_amount'])

    if not updates:
        return jsonify({'error': 'No fields to update'}), 400

    updates.append('updated_at=CURRENT_TIMESTAMP')
    args.append(invoice_id)
    execute_db(f"UPDATE invoices SET {', '.join(updates)} WHERE id=?", args)

    # Notify patient
    patient = query_db('SELECT p.user_id FROM patients p JOIN invoices i ON i.patient_id=p.id WHERE i.id=?',
                       [invoice_id], one=True)
    if patient and patient['user_id']:
        execute_db(
            '''INSERT INTO notifications (user_id, title, message, notification_type, reference_type, reference_id)
               VALUES (?,?,?,?,?,?)''',
            [patient['user_id'], 'Billing Update',
             f'Your invoice has been updated.',
             'Billing', 'invoice', invoice_id]
        )

    log_audit('UPDATE_PAYMENT', 'invoice', invoice_id)
    return jsonify({'message': 'Payment updated'}), 200


def _add_items(invoice_id, items):
    """Add items to an invoice and recalculate totals."""
    for item in items:
        total_price = float(item.get('quantity', 1)) * float(item['unit_price'])
        execute_db(
            '''INSERT INTO invoice_items (invoice_id, item_type, description, quantity, unit_price, total_price)
               VALUES (?,?,?,?,?,?)''',
            [invoice_id, item['item_type'], item['description'],
             item.get('quantity', 1), item['unit_price'], total_price]
        )

    # Recalculate
    row = query_db('SELECT SUM(total_price) as subtotal FROM invoice_items WHERE invoice_id=?',
                   [invoice_id], one=True)
    subtotal = row['subtotal'] or 0
    inv = query_db('SELECT tax_amount, discount_amount FROM invoices WHERE id=?', [invoice_id], one=True)
    total = subtotal + (inv['tax_amount'] or 0) - (inv['discount_amount'] or 0)
    execute_db('UPDATE invoices SET subtotal=?, total_amount=?, updated_at=CURRENT_TIMESTAMP WHERE id=?',
               [subtotal, total, invoice_id])


@billing_bp.route('/<int:invoice_id>/files', methods=['POST'])
@jwt_required
@role_required('Admin', 'Staff')
def upload_invoice_file(invoice_id):
    """Upload a file (bill soft copy) to an invoice."""
    invoice = query_db('SELECT * FROM invoices WHERE id=?', [invoice_id], one=True)
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404

    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'No files provided'}), 400

    uploaded = []
    for f in files:
        if f and allowed_file(f.filename):
            safe_name, rel_path, file_size, mime_type = save_upload(f, f'invoices/{invoice_id}')
            file_id = execute_db(
                '''INSERT INTO invoice_files (invoice_id, file_name, original_name, file_path, file_size, mime_type)
                   VALUES (?,?,?,?,?,?)''',
                [invoice_id, safe_name, f.filename, rel_path, file_size, mime_type]
            )
            uploaded.append({'id': file_id, 'original_name': f.filename, 'file_size': file_size})

    if not uploaded:
        return jsonify({'error': 'No valid files uploaded'}), 400

    log_audit('UPLOAD_INVOICE_FILE', 'invoice', invoice_id, f"Uploaded {len(uploaded)} file(s)")
    return jsonify({'message': f'{len(uploaded)} file(s) uploaded', 'files': uploaded}), 201


@billing_bp.route('/files/<int:file_id>/download', methods=['GET'])
@jwt_required
def download_invoice_file(file_id):
    """Download a bill soft copy file."""
    rf = query_db(
        'SELECT inf.*, i.patient_id FROM invoice_files inf JOIN invoices i ON inf.invoice_id=i.id WHERE inf.id=?',
        [file_id], one=True)
    if not rf:
        return jsonify({'error': 'File not found'}), 404

    role = g.current_user['role']
    if role == 'Patient':
        pid = get_patient_id_for_user(g.current_user['id'])
        if rf['patient_id'] != pid:
            return jsonify({'error': 'Access denied'}), 403

    file_path = os.path.join(Config.UPLOAD_FOLDER, rf['file_path'])
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found on disk'}), 404

    log_audit('DOWNLOAD_INVOICE_FILE', 'invoice_file', file_id)
    return send_file(file_path, download_name=rf['original_name'], as_attachment=True)


@billing_bp.route('/<int:invoice_id>/files/<int:file_id>', methods=['DELETE'])
@jwt_required
@role_required('Admin', 'Staff')
def delete_invoice_file(invoice_id, file_id):
    """Delete a bill file."""
    rf = query_db('SELECT * FROM invoice_files WHERE id=? AND invoice_id=?', [file_id, invoice_id], one=True)
    if not rf:
        return jsonify({'error': 'File not found'}), 404

    file_path = os.path.join(Config.UPLOAD_FOLDER, rf['file_path'])
    if os.path.exists(file_path):
        os.remove(file_path)

    execute_db('DELETE FROM invoice_files WHERE id=?', [file_id])
    log_audit('DELETE_INVOICE_FILE', 'invoice_file', file_id)
    return jsonify({'message': 'File deleted'}), 200
