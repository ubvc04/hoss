from flask import Blueprint, request, jsonify, g
from ..database import query_db, execute_db, dicts_from_rows, dict_from_row
from ..middleware import jwt_required, role_required, get_patient_id_for_user, get_doctor_id_for_user, log_audit
from ..utils import validate_required, parse_pagination

appointments_bp = Blueprint('appointments', __name__, url_prefix='/api/appointments')


@appointments_bp.route('', methods=['GET'])
@jwt_required
def list_appointments():
    role = g.current_user['role']
    page, per_page = parse_pagination(request)
    patient_id = request.args.get('patient_id', type=int)

    query = '''SELECT a.*, p.mrn, p.first_name || ' ' || p.last_name as patient_name,
                      d.first_name || ' ' || d.last_name as doctor_name,
                      dep.name as department_name
               FROM appointments a
               JOIN patients p ON a.patient_id=p.id
               LEFT JOIN doctors d ON a.doctor_id=d.id
               LEFT JOIN departments dep ON a.department_id=dep.id
               WHERE 1=1'''
    args = []

    if role == 'Patient':
        pid = get_patient_id_for_user(g.current_user['id'])
        query += ' AND a.patient_id=?'
        args.append(pid)
    elif role == 'Doctor':
        doc_id = get_doctor_id_for_user(g.current_user['id'])
        query += ' AND a.doctor_id=?'
        args.append(doc_id)
    elif patient_id:
        query += ' AND a.patient_id=?'
        args.append(patient_id)

    status = request.args.get('status')
    if status:
        query += ' AND a.status=?'
        args.append(status)

    count_q = query.replace(
        "SELECT a.*, p.mrn, p.first_name || ' ' || p.last_name as patient_name,\n                      d.first_name || ' ' || d.last_name as doctor_name,\n                      dep.name as department_name",
        'SELECT COUNT(*) as cnt')
    total = query_db(count_q, args, one=True)['cnt']

    query += ' ORDER BY a.appointment_date DESC, a.appointment_time DESC LIMIT ? OFFSET ?'
    args.extend([per_page, (page - 1) * per_page])

    appointments = dicts_from_rows(query_db(query, args))
    return jsonify({'appointments': appointments, 'total': total, 'page': page, 'per_page': per_page}), 200


@appointments_bp.route('/<int:appt_id>', methods=['GET'])
@jwt_required
def get_appointment(appt_id):
    appt = query_db(
        '''SELECT a.*, p.mrn, p.first_name || ' ' || p.last_name as patient_name,
                  d.first_name || ' ' || d.last_name as doctor_name,
                  dep.name as department_name
           FROM appointments a
           JOIN patients p ON a.patient_id=p.id
           LEFT JOIN doctors d ON a.doctor_id=d.id
           LEFT JOIN departments dep ON a.department_id=dep.id
           WHERE a.id=?''', [appt_id], one=True)

    if not appt:
        return jsonify({'error': 'Appointment not found'}), 404

    role = g.current_user['role']
    if role == 'Patient':
        pid = get_patient_id_for_user(g.current_user['id'])
        if appt['patient_id'] != pid:
            return jsonify({'error': 'Access denied'}), 403

    return jsonify({'appointment': dict_from_row(appt)}), 200


@appointments_bp.route('', methods=['POST'])
@jwt_required
def create_appointment():
    data = request.get_json()
    role = g.current_user['role']

    if role == 'Patient':
        patient_id = get_patient_id_for_user(g.current_user['id'])
        if not patient_id:
            return jsonify({'error': 'Patient record not found'}), 400
        data['patient_id'] = patient_id
        data['status'] = 'Requested'

    valid, msg = validate_required(data, ['patient_id', 'appointment_date', 'appointment_time'])
    if not valid:
        return jsonify({'error': msg}), 400

    status = data.get('status', 'Requested')
    if role in ('Staff', 'Admin'):
        status = data.get('status', 'Confirmed')

    appt_id = execute_db(
        '''INSERT INTO appointments (patient_id, doctor_id, department_id, appointment_date,
           appointment_time, visit_type, status, reason, notes, created_by)
           VALUES (?,?,?,?,?,?,?,?,?,?)''',
        [data['patient_id'], data.get('doctor_id'), data.get('department_id'),
         data['appointment_date'], data['appointment_time'],
         data.get('visit_type', 'In-Person'), status,
         data.get('reason'), data.get('notes'), g.current_user['id']]
    )

    # Notify relevant people
    if role == 'Patient':
        # Notify staff
        staff_users = query_db("SELECT u.id FROM users u JOIN roles r ON u.role_id=r.id WHERE r.name='Staff' AND u.is_active=1")
        for su in staff_users:
            execute_db(
                '''INSERT INTO notifications (user_id, title, message, notification_type, reference_type, reference_id)
                   VALUES (?,?,?,?,?,?)''',
                [su['id'], 'New Appointment Request',
                 f'A patient has requested an appointment on {data["appointment_date"]}.',
                 'Appointment', 'appointment', appt_id]
            )
    else:
        # Notify patient
        patient = query_db('SELECT user_id FROM patients WHERE id=?', [data['patient_id']], one=True)
        if patient and patient['user_id']:
            execute_db(
                '''INSERT INTO notifications (user_id, title, message, notification_type, reference_type, reference_id)
                   VALUES (?,?,?,?,?,?)''',
                [patient['user_id'], 'Appointment Scheduled',
                 f'Your appointment has been scheduled for {data["appointment_date"]} at {data["appointment_time"]}.',
                 'Appointment', 'appointment', appt_id]
            )

    log_audit('CREATE_APPOINTMENT', 'appointment', appt_id)
    return jsonify({'message': 'Appointment created', 'id': appt_id}), 201


@appointments_bp.route('/<int:appt_id>', methods=['PUT'])
@jwt_required
@role_required('Admin', 'Staff', 'Doctor')
def update_appointment(appt_id):
    data = request.get_json()
    appt = query_db('SELECT * FROM appointments WHERE id=?', [appt_id], one=True)
    if not appt:
        return jsonify({'error': 'Appointment not found'}), 404

    fields = ['doctor_id', 'department_id', 'appointment_date', 'appointment_time',
              'visit_type', 'status', 'reason', 'notes']
    updates = []
    args = []

    for f in fields:
        if f in data:
            updates.append(f'{f}=?')
            args.append(data[f])

    if data.get('status') in ('Confirmed', 'Rescheduled'):
        updates.append('approved_by=?')
        args.append(g.current_user['id'])

    if not updates:
        return jsonify({'error': 'No fields to update'}), 400

    updates.append('updated_at=CURRENT_TIMESTAMP')
    args.append(appt_id)
    execute_db(f"UPDATE appointments SET {', '.join(updates)} WHERE id=?", args)

    # Notify patient of changes
    patient = query_db('SELECT user_id FROM patients WHERE id=?', [appt['patient_id']], one=True)
    if patient and patient['user_id']:
        status_text = data.get('status', 'updated')
        execute_db(
            '''INSERT INTO notifications (user_id, title, message, notification_type, reference_type, reference_id)
               VALUES (?,?,?,?,?,?)''',
            [patient['user_id'], f'Appointment {status_text}',
             f'Your appointment has been {status_text.lower()}.',
             'Appointment', 'appointment', appt_id]
        )

    log_audit('UPDATE_APPOINTMENT', 'appointment', appt_id, f"Status: {data.get('status', 'updated')}")
    return jsonify({'message': 'Appointment updated'}), 200
