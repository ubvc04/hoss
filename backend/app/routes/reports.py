import os
from flask import Blueprint, request, jsonify, g, send_file
from ..database import query_db, execute_db, dicts_from_rows, dict_from_row
from ..middleware import jwt_required, role_required, get_patient_id_for_user, log_audit
from ..utils import allowed_file, save_upload, validate_required, parse_pagination
from ..config import Config
from ..blockchain import get_blockchain_service

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')


@reports_bp.route('', methods=['GET'])
@jwt_required
def list_reports():
    patient_id = request.args.get('patient_id', type=int)
    role = g.current_user['role']

    if role == 'Patient':
        patient_id = get_patient_id_for_user(g.current_user['id'])

    page, per_page = parse_pagination(request)

    query = '''SELECT r.*, p.mrn, p.first_name || ' ' || p.last_name as patient_name,
                      d.first_name || ' ' || d.last_name as doctor_name,
                      dep.name as department_name,
                      u.username as uploaded_by_name
               FROM reports r
               JOIN patients p ON r.patient_id=p.id
               LEFT JOIN doctors d ON r.ordering_doctor_id=d.id
               LEFT JOIN departments dep ON r.department_id=dep.id
               LEFT JOIN users u ON r.uploaded_by=u.id
               WHERE 1=1'''
    args = []

    if patient_id:
        query += ' AND r.patient_id=?'
        args.append(patient_id)

    report_type = request.args.get('report_type')
    if report_type:
        query += ' AND r.report_type=?'
        args.append(report_type)

    count_q = query.replace(
        "SELECT r.*, p.mrn, p.first_name || ' ' || p.last_name as patient_name,\n                      d.first_name || ' ' || d.last_name as doctor_name,\n                      dep.name as department_name,\n                      u.username as uploaded_by_name",
        'SELECT COUNT(*) as cnt')
    total = query_db(count_q, args, one=True)['cnt']

    query += ' ORDER BY r.report_date DESC LIMIT ? OFFSET ?'
    args.extend([per_page, (page - 1) * per_page])

    reports = dicts_from_rows(query_db(query, args))

    # Attach files to each report
    for r in reports:
        r['files'] = dicts_from_rows(query_db('SELECT id, file_name, original_name, file_size, mime_type FROM report_files WHERE report_id=?', [r['id']]))

    return jsonify({'reports': reports, 'total': total, 'page': page, 'per_page': per_page}), 200


@reports_bp.route('/<int:report_id>', methods=['GET'])
@jwt_required
def get_report(report_id):
    report = query_db(
        '''SELECT r.*, p.mrn, p.first_name || ' ' || p.last_name as patient_name,
                  d.first_name || ' ' || d.last_name as doctor_name,
                  dep.name as department_name, u.username as uploaded_by_name
           FROM reports r
           JOIN patients p ON r.patient_id=p.id
           LEFT JOIN doctors d ON r.ordering_doctor_id=d.id
           LEFT JOIN departments dep ON r.department_id=dep.id
           LEFT JOIN users u ON r.uploaded_by=u.id
           WHERE r.id=?''', [report_id], one=True)

    if not report:
        return jsonify({'error': 'Report not found'}), 404

    role = g.current_user['role']
    if role == 'Patient':
        pid = get_patient_id_for_user(g.current_user['id'])
        if report['patient_id'] != pid:
            return jsonify({'error': 'Access denied'}), 403

    result = dict_from_row(report)
    result['files'] = dicts_from_rows(query_db('SELECT * FROM report_files WHERE report_id=?', [report_id]))

    log_audit('VIEW_REPORT', 'report', report_id)
    return jsonify({'report': result}), 200


@reports_bp.route('', methods=['POST'])
@jwt_required
@role_required('Doctor', 'Staff', 'Admin')
def create_report():
    # Multipart form
    patient_id = request.form.get('patient_id', type=int)
    if not patient_id:
        return jsonify({'error': 'patient_id is required'}), 400

    report_type = request.form.get('report_type')
    title = request.form.get('title')
    if not report_type or not title:
        return jsonify({'error': 'report_type and title are required'}), 400

    report_id = execute_db(
        '''INSERT INTO reports (patient_id, visit_id, report_type, title, description, report_date,
           ordering_doctor_id, department_id, uploaded_by, result_summary)
           VALUES (?,?,?,?,?,COALESCE(?,date('now')),?,?,?,?)''',
        [patient_id, request.form.get('visit_id', type=int), report_type, title,
         request.form.get('description'), request.form.get('report_date'),
         request.form.get('ordering_doctor_id', type=int),
         request.form.get('department_id', type=int),
         g.current_user['id'], request.form.get('result_summary')]
    )

    # Handle file uploads
    files = request.files.getlist('files')
    file_data = None
    filename = None
    for f in files:
        if f and allowed_file(f.filename):
            # Read file data for blockchain hashing before saving
            if file_data is None:
                file_data = f.read()
                filename = f.filename
                f.seek(0)  # Reset stream for save_upload
            safe_name, rel_path, file_size, mime_type = save_upload(f, f'reports/{report_id}')
            execute_db(
                '''INSERT INTO report_files (report_id, file_name, original_name, file_path, file_size, mime_type)
                   VALUES (?,?,?,?,?,?)''',
                [report_id, safe_name, f.filename, rel_path, file_size, mime_type]
            )

    # Notify patient
    patient = query_db('SELECT user_id FROM patients WHERE id=?', [patient_id], one=True)
    if patient and patient['user_id']:
        execute_db(
            '''INSERT INTO notifications (user_id, title, message, notification_type, reference_type, reference_id)
               VALUES (?,?,?,?,?,?)''',
            [patient['user_id'], f'New {report_type} Report',
             f'A new {report_type.lower()} report "{title}" has been uploaded.',
             'Report', 'report', report_id]
        )

    log_audit('CREATE_REPORT', 'report', report_id)

    # Store report hash on blockchain (with file if available)
    try:
        blockchain_service = get_blockchain_service()
        report_record = query_db('SELECT * FROM reports WHERE id=?', [report_id], one=True)
        if report_record:
            blockchain_service.store_report(
                report_id,
                patient_id,
                dict_from_row(report_record),
                file_data=file_data,
                filename=filename,
                upload_to_ipfs=True,  # IPFS enabled with Pinata
                metadata={'createdBy': g.current_user['id']}
            )
    except Exception as e:
        print(f"Blockchain store error: {e}")

    return jsonify({'message': 'Report created', 'id': report_id}), 201


@reports_bp.route('/<int:report_id>/verify', methods=['PUT'])
@jwt_required
@role_required('Doctor', 'Admin')
def verify_report(report_id):
    data = request.get_json()
    status = data.get('verification_status', 'Verified')

    execute_db(
        'UPDATE reports SET verification_status=?, verified_by=?, verified_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=?',
        [status, g.current_user['id'], report_id]
    )

    log_audit('VERIFY_REPORT', 'report', report_id, f"Status: {status}")
    return jsonify({'message': f'Report {status.lower()}'}), 200


@reports_bp.route('/files/<int:file_id>/download', methods=['GET'])
@jwt_required
def download_file(file_id):
    rf = query_db('SELECT rf.*, r.patient_id FROM report_files rf JOIN reports r ON rf.report_id=r.id WHERE rf.id=?',
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

    log_audit('DOWNLOAD_FILE', 'report_file', file_id)
    return send_file(file_path, download_name=rf['original_name'], as_attachment=True)
