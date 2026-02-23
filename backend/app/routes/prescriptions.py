from flask import Blueprint, request, jsonify, g
from ..database import query_db, execute_db, dicts_from_rows, dict_from_row
from ..middleware import jwt_required, role_required, get_patient_id_for_user, get_doctor_id_for_user, log_audit
from ..utils import validate_required
from ..blockchain import get_blockchain_service

prescriptions_bp = Blueprint('prescriptions', __name__, url_prefix='/api/prescriptions')


@prescriptions_bp.route('', methods=['GET'])
@jwt_required
def list_prescriptions():
    patient_id = request.args.get('patient_id', type=int)
    role = g.current_user['role']

    if role == 'Patient':
        patient_id = get_patient_id_for_user(g.current_user['id'])

    if not patient_id:
        if role == 'Doctor':
            doc_id = get_doctor_id_for_user(g.current_user['id'])
            prescriptions = dicts_from_rows(query_db(
                '''SELECT pr.*, p.mrn, p.first_name || ' ' || p.last_name as patient_name,
                          d.first_name || ' ' || d.last_name as doctor_name
                   FROM prescriptions pr
                   JOIN patients p ON pr.patient_id=p.id
                   JOIN doctors d ON pr.doctor_id=d.id
                   WHERE pr.doctor_id=? ORDER BY pr.prescription_date DESC''', [doc_id]))
            return jsonify({'prescriptions': prescriptions}), 200
        if role in ('Admin', 'Staff'):
            prescriptions = dicts_from_rows(query_db(
                '''SELECT pr.*, p.mrn, p.first_name || ' ' || p.last_name as patient_name,
                          d.first_name || ' ' || d.last_name as doctor_name,
                          (SELECT COUNT(*) FROM medications WHERE prescription_id=pr.id) as medication_count
                   FROM prescriptions pr
                   JOIN patients p ON pr.patient_id=p.id
                   JOIN doctors d ON pr.doctor_id=d.id
                   ORDER BY pr.prescription_date DESC'''))
            return jsonify({'prescriptions': prescriptions}), 200
        return jsonify({'error': 'patient_id required'}), 400

    prescriptions = dicts_from_rows(query_db(
        '''SELECT pr.*, p.mrn, p.first_name || ' ' || p.last_name as patient_name,
                  d.first_name || ' ' || d.last_name as doctor_name
           FROM prescriptions pr
           JOIN patients p ON pr.patient_id=p.id
           JOIN doctors d ON pr.doctor_id=d.id
           WHERE pr.patient_id=? ORDER BY pr.prescription_date DESC''', [patient_id]))

    return jsonify({'prescriptions': prescriptions}), 200


@prescriptions_bp.route('/<int:rx_id>', methods=['GET'])
@jwt_required
def get_prescription(rx_id):
    rx = query_db(
        '''SELECT pr.*, p.mrn, p.first_name || ' ' || p.last_name as patient_name,
                  d.first_name || ' ' || d.last_name as doctor_name
           FROM prescriptions pr
           JOIN patients p ON pr.patient_id=p.id
           JOIN doctors d ON pr.doctor_id=d.id
           WHERE pr.id=?''', [rx_id], one=True)

    if not rx:
        return jsonify({'error': 'Prescription not found'}), 404

    role = g.current_user['role']
    if role == 'Patient':
        pid = get_patient_id_for_user(g.current_user['id'])
        if rx['patient_id'] != pid:
            return jsonify({'error': 'Access denied'}), 403

    result = dict_from_row(rx)
    meds = dicts_from_rows(query_db('SELECT * FROM medications WHERE prescription_id=?', [rx_id]))
    result['medications'] = meds

    log_audit('VIEW_PRESCRIPTION', 'prescription', rx_id)
    return jsonify({'prescription': result}), 200


@prescriptions_bp.route('', methods=['POST'])
@jwt_required
@role_required('Doctor', 'Admin', 'Staff')
def create_prescription():
    data = request.get_json()
    valid, msg = validate_required(data, ['patient_id', 'medications'])
    if not valid:
        return jsonify({'error': msg}), 400

    if not data['medications'] or not isinstance(data['medications'], list):
        return jsonify({'error': 'At least one medication is required'}), 400

    doctor_id = get_doctor_id_for_user(g.current_user['id']) if g.current_user['role'] == 'Doctor' else data.get('doctor_id')
    if not doctor_id:
        return jsonify({'error': 'doctor_id required'}), 400

    rx_id = execute_db(
        '''INSERT INTO prescriptions (patient_id, visit_id, doctor_id, notes, prescription_date)
           VALUES (?,?,?,?,COALESCE(?,date('now')))''',
        [data['patient_id'], data.get('visit_id'), doctor_id, data.get('notes'), data.get('prescription_date')]
    )

    for med in data['medications']:
        execute_db(
            '''INSERT INTO medications (prescription_id, medication_name, generic_name, dosage,
               frequency, duration, route, instructions, start_date, end_date)
               VALUES (?,?,?,?,?,?,?,?,?,?)''',
            [rx_id, med['medication_name'], med.get('generic_name'), med['dosage'],
             med['frequency'], med.get('duration'), med.get('route', 'Oral'),
             med.get('instructions'), med.get('start_date'), med.get('end_date')]
        )

    # Notify patient
    patient = query_db('SELECT user_id FROM patients WHERE id=?', [data['patient_id']], one=True)
    if patient and patient['user_id']:
        execute_db(
            '''INSERT INTO notifications (user_id, title, message, notification_type, reference_type, reference_id)
               VALUES (?,?,?,?,?,?)''',
            [patient['user_id'], 'New Prescription',
             'A new prescription has been added to your records.',
             'Prescription', 'prescription', rx_id]
        )

    log_audit('CREATE_PRESCRIPTION', 'prescription', rx_id)

    # Store prescription hash on blockchain
    try:
        blockchain_service = get_blockchain_service()
        rx_record = query_db('SELECT * FROM prescriptions WHERE id=?', [rx_id], one=True)
        meds = dicts_from_rows(query_db('SELECT * FROM medications WHERE prescription_id=?', [rx_id]))
        if rx_record:
            blockchain_service.store_prescription(
                rx_id,
                data['patient_id'],
                dict_from_row(rx_record),
                meds,
                metadata={'createdBy': g.current_user['id']}
            )
    except Exception as e:
        print(f"Blockchain store error: {e}")

    return jsonify({'message': 'Prescription created', 'id': rx_id}), 201
