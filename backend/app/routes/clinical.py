from flask import Blueprint, request, jsonify, g
from ..database import query_db, execute_db, dicts_from_rows, dict_from_row
from ..middleware import jwt_required, role_required, get_patient_id_for_user, get_doctor_id_for_user, log_audit
from ..utils import validate_required, parse_pagination

clinical_bp = Blueprint('clinical', __name__, url_prefix='/api')


# ========== DIAGNOSES ==========

@clinical_bp.route('/diagnoses', methods=['GET'])
@jwt_required
def list_diagnoses():
    patient_id = request.args.get('patient_id', type=int)
    role = g.current_user['role']

    if role == 'Patient':
        patient_id = get_patient_id_for_user(g.current_user['id'])

    if not patient_id:
        return jsonify({'error': 'patient_id required'}), 400

    diagnoses = dicts_from_rows(query_db(
        '''SELECT d.*, doc.first_name || ' ' || doc.last_name as doctor_name
           FROM diagnoses d LEFT JOIN doctors doc ON d.diagnosed_by=doc.id
           WHERE d.patient_id=? ORDER BY d.diagnosed_date DESC''', [patient_id]))

    return jsonify({'diagnoses': diagnoses}), 200


@clinical_bp.route('/diagnoses', methods=['POST'])
@jwt_required
@role_required('Doctor', 'Admin')
def create_diagnosis():
    data = request.get_json()
    valid, msg = validate_required(data, ['patient_id', 'diagnosis_name'])
    if not valid:
        return jsonify({'error': msg}), 400

    doctor_id = get_doctor_id_for_user(g.current_user['id']) if g.current_user['role'] == 'Doctor' else data.get('diagnosed_by')

    diag_id = execute_db(
        '''INSERT INTO diagnoses (patient_id, visit_id, icd_code, diagnosis_name, diagnosis_type,
           severity, status, notes, diagnosed_by, diagnosed_date) VALUES (?,?,?,?,?,?,?,?,?,?)''',
        [data['patient_id'], data.get('visit_id'), data.get('icd_code'), data['diagnosis_name'],
         data.get('diagnosis_type', 'Primary'), data.get('severity'), data.get('status', 'Active'),
         data.get('notes'), doctor_id, data.get('diagnosed_date')]
    )

    log_audit('CREATE_DIAGNOSIS', 'diagnosis', diag_id)
    return jsonify({'message': 'Diagnosis added', 'id': diag_id}), 201


# ========== ALLERGIES ==========

@clinical_bp.route('/allergies', methods=['GET'])
@jwt_required
def list_allergies():
    patient_id = request.args.get('patient_id', type=int)
    role = g.current_user['role']

    if role == 'Patient':
        patient_id = get_patient_id_for_user(g.current_user['id'])

    if not patient_id:
        return jsonify({'error': 'patient_id required'}), 400

    allergies = dicts_from_rows(query_db(
        'SELECT * FROM allergies WHERE patient_id=? ORDER BY noted_date DESC', [patient_id]))
    return jsonify({'allergies': allergies}), 200


@clinical_bp.route('/allergies', methods=['POST'])
@jwt_required
@role_required('Doctor', 'Staff', 'Admin')
def create_allergy():
    data = request.get_json()
    valid, msg = validate_required(data, ['patient_id', 'allergen'])
    if not valid:
        return jsonify({'error': msg}), 400

    allergy_id = execute_db(
        '''INSERT INTO allergies (patient_id, allergen, allergy_type, severity, reaction, noted_by)
           VALUES (?,?,?,?,?,?)''',
        [data['patient_id'], data['allergen'], data.get('allergy_type'), data.get('severity'),
         data.get('reaction'), g.current_user['id']]
    )

    log_audit('CREATE_ALLERGY', 'allergy', allergy_id)
    return jsonify({'message': 'Allergy added', 'id': allergy_id}), 201


# ========== VITALS ==========

@clinical_bp.route('/vitals', methods=['GET'])
@jwt_required
def list_vitals():
    patient_id = request.args.get('patient_id', type=int)
    role = g.current_user['role']

    if role == 'Patient':
        patient_id = get_patient_id_for_user(g.current_user['id'])

    if not patient_id:
        return jsonify({'error': 'patient_id required'}), 400

    vitals = dicts_from_rows(query_db(
        'SELECT * FROM vitals WHERE patient_id=? ORDER BY recorded_at DESC', [patient_id]))
    return jsonify({'vitals': vitals}), 200


@clinical_bp.route('/vitals', methods=['POST'])
@jwt_required
@role_required('Doctor', 'Staff', 'Admin')
def create_vitals():
    data = request.get_json()
    valid, msg = validate_required(data, ['patient_id'])
    if not valid:
        return jsonify({'error': msg}), 400

    # Auto-calculate BMI
    bmi = None
    if data.get('height_cm') and data.get('weight_kg'):
        h = float(data['height_cm']) / 100
        bmi = round(float(data['weight_kg']) / (h * h), 1)

    vital_id = execute_db(
        '''INSERT INTO vitals (patient_id, visit_id, systolic_bp, diastolic_bp, pulse, temperature,
           respiratory_rate, oxygen_saturation, height_cm, weight_kg, bmi, blood_sugar, notes, recorded_by)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        [data['patient_id'], data.get('visit_id'), data.get('systolic_bp'), data.get('diastolic_bp'),
         data.get('pulse'), data.get('temperature'), data.get('respiratory_rate'),
         data.get('oxygen_saturation'), data.get('height_cm'), data.get('weight_kg'),
         bmi, data.get('blood_sugar'), data.get('notes'), g.current_user['id']]
    )

    log_audit('RECORD_VITALS', 'vitals', vital_id)
    return jsonify({'message': 'Vitals recorded', 'id': vital_id}), 201


# ========== CLINICAL NOTES ==========

@clinical_bp.route('/clinical-notes', methods=['GET'])
@jwt_required
def list_notes():
    patient_id = request.args.get('patient_id', type=int)
    visit_id = request.args.get('visit_id', type=int)
    role = g.current_user['role']

    if role == 'Patient':
        patient_id = get_patient_id_for_user(g.current_user['id'])

    query = '''SELECT cn.*, u.username as author_name FROM clinical_notes cn
               JOIN users u ON cn.author_id=u.id WHERE 1=1'''
    args = []

    if patient_id:
        query += ' AND cn.patient_id=?'
        args.append(patient_id)
    if visit_id:
        query += ' AND cn.visit_id=?'
        args.append(visit_id)

    if not patient_id and not visit_id:
        return jsonify({'error': 'patient_id or visit_id required'}), 400

    query += ' ORDER BY cn.created_at DESC'
    notes = dicts_from_rows(query_db(query, args))
    return jsonify({'clinical_notes': notes}), 200


@clinical_bp.route('/clinical-notes', methods=['POST'])
@jwt_required
@role_required('Doctor', 'Admin')
def create_note():
    data = request.get_json()
    valid, msg = validate_required(data, ['patient_id'])
    if not valid:
        return jsonify({'error': msg}), 400

    note_id = execute_db(
        '''INSERT INTO clinical_notes (patient_id, visit_id, note_type, subjective, objective,
           assessment, plan, content, author_id) VALUES (?,?,?,?,?,?,?,?,?)''',
        [data['patient_id'], data.get('visit_id'), data.get('note_type', 'Progress'),
         data.get('subjective'), data.get('objective'), data.get('assessment'),
         data.get('plan'), data.get('content'), g.current_user['id']]
    )

    log_audit('CREATE_NOTE', 'clinical_note', note_id)
    return jsonify({'message': 'Clinical note added', 'id': note_id}), 201
