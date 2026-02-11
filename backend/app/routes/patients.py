from flask import Blueprint, request, jsonify, g
import bcrypt
from ..database import query_db, execute_db, dicts_from_rows, dict_from_row
from ..middleware import jwt_required, role_required, get_patient_id_for_user, log_audit
from ..utils import validate_required, generate_mrn, parse_pagination

patients_bp = Blueprint('patients', __name__, url_prefix='/api/patients')


@patients_bp.route('', methods=['GET'])
@jwt_required
def list_patients():
    role = g.current_user['role']

    if role == 'Patient':
        pid = get_patient_id_for_user(g.current_user['id'])
        if not pid:
            return jsonify({'patients': [], 'total': 0}), 200
        patient = query_db('SELECT * FROM patients WHERE id=? AND is_active=1', [pid], one=True)
        return jsonify({'patients': [dict_from_row(patient)] if patient else [], 'total': 1 if patient else 0}), 200

    page, per_page = parse_pagination(request)
    search = request.args.get('search', '')

    query = 'SELECT * FROM patients WHERE is_active=1'
    args = []

    if role == 'Doctor':
        from ..middleware import get_doctor_id_for_user
        doc_id = get_doctor_id_for_user(g.current_user['id'])
        query += ''' AND id IN (SELECT DISTINCT patient_id FROM visits WHERE doctor_id=?
                     UNION SELECT DISTINCT patient_id FROM appointments WHERE doctor_id=?)'''
        args.extend([doc_id, doc_id])

    if search:
        query += ' AND (first_name LIKE ? OR last_name LIKE ? OR mrn LIKE ? OR phone LIKE ?)'
        args.extend([f'%{search}%'] * 4)

    count_q = query.replace('SELECT *', 'SELECT COUNT(*) as cnt')
    total = query_db(count_q, args, one=True)['cnt']

    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    args.extend([per_page, (page - 1) * per_page])

    patients = dicts_from_rows(query_db(query, args))
    return jsonify({'patients': patients, 'total': total, 'page': page, 'per_page': per_page}), 200


@patients_bp.route('/<int:patient_id>', methods=['GET'])
@jwt_required
def get_patient(patient_id):
    role = g.current_user['role']

    if role == 'Patient':
        pid = get_patient_id_for_user(g.current_user['id'])
        if pid != patient_id:
            return jsonify({'error': 'Access denied'}), 403

    patient = query_db('SELECT * FROM patients WHERE id=?', [patient_id], one=True)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404

    result = dict_from_row(patient)

    # Fetch insurance
    insurance = dicts_from_rows(query_db('SELECT * FROM insurance WHERE patient_id=?', [patient_id]))
    result['insurance'] = insurance

    log_audit('VIEW_PATIENT', 'patient', patient_id, f"Viewed patient {patient['mrn']}")
    return jsonify({'patient': result}), 200


@patients_bp.route('', methods=['POST'])
@jwt_required
@role_required('Admin', 'Staff')
def create_patient():
    data = request.get_json()
    valid, msg = validate_required(data, ['first_name', 'last_name', 'date_of_birth', 'gender', 'username', 'password'])
    if not valid:
        return jsonify({'error': msg}), 400

    mrn = generate_mrn()

    # Create user account for patient
    username = data['username'].strip()
    password = data['password']
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    
    pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Check if username already exists
    existing_user = query_db('SELECT id FROM users WHERE username=?', [username], one=True)
    if existing_user:
        return jsonify({'error': f'Username "{username}" already exists'}), 400

    patient_role = query_db('SELECT id FROM roles WHERE name=?', ['Patient'], one=True)

    user_id = execute_db(
        'INSERT INTO users (username, password_hash, email, phone, role_id, must_change_password) VALUES (?,?,?,?,?,0)',
        [username, pw_hash, data.get('email'), data.get('phone'), patient_role['id']]
    )

    patient_id = execute_db(
        '''INSERT INTO patients (user_id, mrn, first_name, last_name, date_of_birth, gender, blood_group,
           marital_status, address_line1, address_line2, city, state, postal_code, country, phone, email,
           emergency_contact_name, emergency_contact_phone, emergency_contact_relation,
           national_id, hospital_id, created_by)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        [user_id, mrn, data['first_name'], data['last_name'], data['date_of_birth'], data['gender'],
         data.get('blood_group'), data.get('marital_status'),
         data.get('address_line1'), data.get('address_line2'), data.get('city'), data.get('state'),
         data.get('postal_code'), data.get('country', 'India'),
         data.get('phone'), data.get('email'),
         data.get('emergency_contact_name'), data.get('emergency_contact_phone'), data.get('emergency_contact_relation'),
         data.get('national_id'), data.get('hospital_id'),
         g.current_user['id']]
    )

    # Insurance
    if data.get('insurance'):
        ins = data['insurance']
        execute_db(
            '''INSERT INTO insurance (patient_id, provider_name, policy_number, group_number, plan_type,
               coverage_start, coverage_end, max_coverage_amount)
               VALUES (?,?,?,?,?,?,?,?)''',
            [patient_id, ins.get('provider_name', ''), ins.get('policy_number', ''),
             ins.get('group_number'), ins.get('plan_type'),
             ins.get('coverage_start'), ins.get('coverage_end'), ins.get('max_coverage_amount')]
        )

    log_audit('CREATE_PATIENT', 'patient', patient_id, f"Created patient {mrn}")

    return jsonify({
        'message': 'Patient created',
        'patient_id': patient_id,
        'mrn': mrn,
        'username': username,
        'password': password
    }), 201


@patients_bp.route('/<int:patient_id>', methods=['PUT'])
@jwt_required
def update_patient(patient_id):
    role = g.current_user['role']
    if role == 'Patient':
        pid = get_patient_id_for_user(g.current_user['id'])
        if pid != patient_id:
            return jsonify({'error': 'Access denied'}), 403

    if role not in ('Admin', 'Staff', 'Patient'):
        return jsonify({'error': 'Insufficient permissions'}), 403

    data = request.get_json()
    patient = query_db('SELECT * FROM patients WHERE id=?', [patient_id], one=True)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404

    allowed_fields = ['first_name', 'last_name', 'date_of_birth', 'gender', 'blood_group',
                      'marital_status', 'address_line1', 'address_line2', 'city', 'state',
                      'postal_code', 'country', 'phone', 'email',
                      'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation',
                      'national_id', 'hospital_id']

    # Patient can only update contact info
    if role == 'Patient':
        allowed_fields = ['phone', 'email', 'address_line1', 'address_line2', 'city', 'state',
                          'postal_code', 'emergency_contact_name', 'emergency_contact_phone',
                          'emergency_contact_relation']

    updates = []
    args = []
    for field in allowed_fields:
        if field in data:
            updates.append(f'{field}=?')
            args.append(data[field])

    if not updates:
        return jsonify({'error': 'No fields to update'}), 400

    updates.append('updated_at=CURRENT_TIMESTAMP')
    args.append(patient_id)
    execute_db(f"UPDATE patients SET {', '.join(updates)} WHERE id=?", args)

    log_audit('UPDATE_PATIENT', 'patient', patient_id, f"Updated patient {patient['mrn']}")
    return jsonify({'message': 'Patient updated'}), 200


@patients_bp.route('/departments', methods=['GET'])
@jwt_required
def list_departments():
    depts = dicts_from_rows(query_db('SELECT * FROM departments WHERE is_active=1 ORDER BY name'))
    return jsonify({'departments': depts}), 200


@patients_bp.route('/doctors', methods=['GET'])
@jwt_required
def list_doctors():
    dept_id = request.args.get('department_id', type=int)
    query = '''SELECT d.id, d.first_name, d.last_name, d.specialization, d.employee_id,
                      d.consultation_fee, dep.name as department_name
               FROM doctors d LEFT JOIN departments dep ON d.department_id=dep.id
               WHERE d.is_active=1'''
    args = []
    if dept_id:
        query += ' AND d.department_id=?'
        args.append(dept_id)
    query += ' ORDER BY d.first_name'
    doctors = dicts_from_rows(query_db(query, args))
    return jsonify({'doctors': doctors}), 200
