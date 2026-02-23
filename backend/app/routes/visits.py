from flask import Blueprint, request, jsonify, g
from ..database import query_db, execute_db, dicts_from_rows, dict_from_row
from ..middleware import jwt_required, role_required, get_patient_id_for_user, get_doctor_id_for_user, log_audit
from ..utils import validate_required, parse_pagination
from ..blockchain import get_blockchain_service

visits_bp = Blueprint('visits', __name__, url_prefix='/api/visits')


@visits_bp.route('', methods=['GET'])
@jwt_required
def list_visits():
    role = g.current_user['role']
    patient_id = request.args.get('patient_id', type=int)
    page, per_page = parse_pagination(request)

    query = '''SELECT v.*, p.mrn, p.first_name || ' ' || p.last_name as patient_name,
                      d.first_name || ' ' || d.last_name as doctor_name,
                      dep.name as department_name
               FROM visits v
               JOIN patients p ON v.patient_id=p.id
               LEFT JOIN doctors d ON v.doctor_id=d.id
               LEFT JOIN departments dep ON v.department_id=dep.id
               WHERE 1=1'''
    args = []

    if role == 'Patient':
        pid = get_patient_id_for_user(g.current_user['id'])
        query += ' AND v.patient_id=?'
        args.append(pid)
    elif role == 'Doctor':
        doc_id = get_doctor_id_for_user(g.current_user['id'])
        query += ' AND v.doctor_id=?'
        args.append(doc_id)
    elif patient_id:
        query += ' AND v.patient_id=?'
        args.append(patient_id)

    status = request.args.get('status')
    if status:
        query += ' AND v.status=?'
        args.append(status)

    visit_type = request.args.get('visit_type')
    if visit_type:
        query += ' AND v.visit_type=?'
        args.append(visit_type)

    count_q = query.replace(
        "SELECT v.*, p.mrn, p.first_name || ' ' || p.last_name as patient_name,\n                      d.first_name || ' ' || d.last_name as doctor_name,\n                      dep.name as department_name",
        'SELECT COUNT(*) as cnt')
    total = query_db(count_q, args, one=True)['cnt']

    query += ' ORDER BY v.admission_date DESC LIMIT ? OFFSET ?'
    args.extend([per_page, (page - 1) * per_page])

    visits = dicts_from_rows(query_db(query, args))
    return jsonify({'visits': visits, 'total': total, 'page': page, 'per_page': per_page}), 200


@visits_bp.route('/<int:visit_id>', methods=['GET'])
@jwt_required
def get_visit(visit_id):
    visit = query_db(
        '''SELECT v.*, p.mrn, p.first_name || ' ' || p.last_name as patient_name,
                  d.first_name || ' ' || d.last_name as doctor_name,
                  dep.name as department_name
           FROM visits v
           JOIN patients p ON v.patient_id=p.id
           LEFT JOIN doctors d ON v.doctor_id=d.id
           LEFT JOIN departments dep ON v.department_id=dep.id
           WHERE v.id=?''', [visit_id], one=True)

    if not visit:
        return jsonify({'error': 'Visit not found'}), 404

    role = g.current_user['role']
    if role == 'Patient':
        pid = get_patient_id_for_user(g.current_user['id'])
        if visit['patient_id'] != pid:
            return jsonify({'error': 'Access denied'}), 403

    log_audit('VIEW_VISIT', 'visit', visit_id)
    return jsonify({'visit': dict_from_row(visit)}), 200


@visits_bp.route('', methods=['POST'])
@jwt_required
@role_required('Admin', 'Staff', 'Doctor')
def create_visit():
    data = request.get_json()
    valid, msg = validate_required(data, ['patient_id', 'visit_type'])
    if not valid:
        return jsonify({'error': msg}), 400

    visit_id = execute_db(
        '''INSERT INTO visits (patient_id, visit_type, doctor_id, department_id, chief_complaint,
           ward, bed_number, room_number, created_by)
           VALUES (?,?,?,?,?,?,?,?,?)''',
        [data['patient_id'], data['visit_type'], data.get('doctor_id'), data.get('department_id'),
         data.get('chief_complaint'), data.get('ward'), data.get('bed_number'), data.get('room_number'),
         g.current_user['id']]
    )

    log_audit('CREATE_VISIT', 'visit', visit_id, f"Created {data['visit_type']} visit for patient {data['patient_id']}")

    # Store visit hash on blockchain
    try:
        blockchain_service = get_blockchain_service()
        visit_record = query_db('SELECT * FROM visits WHERE id=?', [visit_id], one=True)
        if visit_record:
            blockchain_service.store_visit(
                visit_id,
                data['patient_id'],
                dict_from_row(visit_record),
                metadata={'createdBy': g.current_user['id']}
            )
    except Exception as e:
        print(f"Blockchain store error: {e}")

    return jsonify({'message': 'Visit created', 'visit_id': visit_id}), 201


@visits_bp.route('/<int:visit_id>', methods=['PUT'])
@jwt_required
@role_required('Admin', 'Staff', 'Doctor')
def update_visit(visit_id):
    data = request.get_json()
    visit = query_db('SELECT * FROM visits WHERE id=?', [visit_id], one=True)
    if not visit:
        return jsonify({'error': 'Visit not found'}), 404

    fields = ['status', 'discharge_date', 'ward', 'bed_number', 'room_number',
              'doctor_id', 'department_id', 'chief_complaint', 'discharge_summary']
    updates = []
    args = []

    for f in fields:
        if f in data:
            updates.append(f'{f}=?')
            args.append(data[f])

    if not updates:
        return jsonify({'error': 'No fields to update'}), 400

    updates.append('updated_at=CURRENT_TIMESTAMP')
    args.append(visit_id)
    execute_db(f"UPDATE visits SET {', '.join(updates)} WHERE id=?", args)

    log_audit('UPDATE_VISIT', 'visit', visit_id)

    # Update blockchain hash
    try:
        blockchain_service = get_blockchain_service()
        updated_visit = query_db('SELECT * FROM visits WHERE id=?', [visit_id], one=True)
        if updated_visit:
            blockchain_service.store_visit(
                visit_id,
                updated_visit['patient_id'],
                dict_from_row(updated_visit),
                metadata={'updatedBy': g.current_user['id'], 'action': 'UPDATE'}
            )
    except Exception as e:
        print(f"Blockchain update error: {e}")

    return jsonify({'message': 'Visit updated'}), 200
