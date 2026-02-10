from flask import Blueprint, jsonify, g
from ..database import query_db
from ..middleware import jwt_required, get_patient_id_for_user, get_doctor_id_for_user

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('', methods=['GET'])
@jwt_required
def get_dashboard():
    role = g.current_user['role']

    if role == 'Admin':
        return _admin_dashboard()
    elif role == 'Doctor':
        return _doctor_dashboard()
    elif role == 'Staff':
        return _staff_dashboard()
    elif role == 'Patient':
        return _patient_dashboard()

    return jsonify({'error': 'Unknown role'}), 400


def _admin_dashboard():
    total_patients = query_db("SELECT COUNT(*) as cnt FROM patients WHERE is_active=1", one=True)['cnt']
    total_doctors = query_db("SELECT COUNT(*) as cnt FROM doctors WHERE is_active=1", one=True)['cnt']
    total_users = query_db("SELECT COUNT(*) as cnt FROM users WHERE is_active=1", one=True)['cnt']
    active_visits = query_db("SELECT COUNT(*) as cnt FROM visits WHERE status='Active'", one=True)['cnt']
    today_appointments = query_db("SELECT COUNT(*) as cnt FROM appointments WHERE appointment_date=date('now')", one=True)['cnt']
    pending_appointments = query_db("SELECT COUNT(*) as cnt FROM appointments WHERE status='Requested'", one=True)['cnt']
    pending_invoices = query_db("SELECT COUNT(*) as cnt FROM invoices WHERE payment_status='Pending'", one=True)['cnt']
    total_revenue = query_db("SELECT COALESCE(SUM(paid_amount),0) as total FROM invoices", one=True)['total']

    recent_logs = []
    rows = query_db("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10")
    for r in rows:
        recent_logs.append(dict(r))

    # All patients list
    all_patients = []
    rows = query_db(
        '''SELECT p.id, p.mrn, p.first_name, p.last_name, p.gender, p.date_of_birth,
                  p.phone, p.email, p.registration_date, p.is_active,
                  u.username, u.last_login
           FROM patients p
           LEFT JOIN users u ON p.user_id = u.id
           ORDER BY p.created_at DESC'''
    )
    for r in rows:
        all_patients.append(dict(r))

    return jsonify({
        'stats': {
            'total_patients': total_patients,
            'total_doctors': total_doctors,
            'total_users': total_users,
            'active_visits': active_visits,
            'today_appointments': today_appointments,
            'pending_appointments': pending_appointments,
            'pending_invoices': pending_invoices,
            'total_revenue': total_revenue
        },
        'recent_audit_logs': recent_logs,
        'all_patients': all_patients
    }), 200


def _doctor_dashboard():
    doc_id = get_doctor_id_for_user(g.current_user['id'])

    my_patients = query_db(
        "SELECT COUNT(DISTINCT patient_id) as cnt FROM visits WHERE doctor_id=?", [doc_id], one=True)['cnt']
    active_visits = query_db(
        "SELECT COUNT(*) as cnt FROM visits WHERE doctor_id=? AND status='Active'", [doc_id], one=True)['cnt']
    today_appointments = query_db(
        "SELECT COUNT(*) as cnt FROM appointments WHERE doctor_id=? AND appointment_date=date('now')",
        [doc_id], one=True)['cnt']

    upcoming = []
    rows = query_db(
        '''SELECT a.*, p.mrn, p.first_name || ' ' || p.last_name as patient_name
           FROM appointments a JOIN patients p ON a.patient_id=p.id
           WHERE a.doctor_id=? AND a.appointment_date >= date('now') AND a.status IN ('Confirmed','Requested')
           ORDER BY a.appointment_date, a.appointment_time LIMIT 10''', [doc_id])
    for r in rows:
        upcoming.append(dict(r))

    return jsonify({
        'stats': {
            'my_patients': my_patients,
            'active_visits': active_visits,
            'today_appointments': today_appointments
        },
        'upcoming_appointments': upcoming
    }), 200


def _staff_dashboard():
    total_patients = query_db("SELECT COUNT(*) as cnt FROM patients WHERE is_active=1", one=True)['cnt']
    today_appointments = query_db("SELECT COUNT(*) as cnt FROM appointments WHERE appointment_date=date('now')", one=True)['cnt']
    pending_appointments = query_db("SELECT COUNT(*) as cnt FROM appointments WHERE status='Requested'", one=True)['cnt']
    active_visits = query_db("SELECT COUNT(*) as cnt FROM visits WHERE status='Active'", one=True)['cnt']
    pending_invoices = query_db("SELECT COUNT(*) as cnt FROM invoices WHERE payment_status='Pending'", one=True)['cnt']
    pending_reports = query_db("SELECT COUNT(*) as cnt FROM reports WHERE verification_status='Pending'", one=True)['cnt']

    recent_patients = []
    rows = query_db("SELECT * FROM patients WHERE is_active=1 ORDER BY created_at DESC LIMIT 5")
    for r in rows:
        recent_patients.append(dict(r))

    return jsonify({
        'stats': {
            'total_patients': total_patients,
            'today_appointments': today_appointments,
            'pending_appointments': pending_appointments,
            'active_visits': active_visits,
            'pending_invoices': pending_invoices,
            'pending_reports': pending_reports
        },
        'recent_patients': recent_patients
    }), 200


def _patient_dashboard():
    pid = get_patient_id_for_user(g.current_user['id'])
    if not pid:
        return jsonify({'stats': {}, 'message': 'No patient record found'}), 200

    total_visits = query_db("SELECT COUNT(*) as cnt FROM visits WHERE patient_id=?", [pid], one=True)['cnt']
    upcoming_appointments = query_db(
        "SELECT COUNT(*) as cnt FROM appointments WHERE patient_id=? AND appointment_date >= date('now') AND status IN ('Confirmed','Requested')",
        [pid], one=True)['cnt']
    total_reports = query_db("SELECT COUNT(*) as cnt FROM reports WHERE patient_id=?", [pid], one=True)['cnt']
    pending_bills = query_db(
        "SELECT COUNT(*) as cnt FROM invoices WHERE patient_id=? AND payment_status IN ('Pending','Partial')",
        [pid], one=True)['cnt']
    active_prescriptions = query_db(
        "SELECT COUNT(*) as cnt FROM prescriptions WHERE patient_id=? AND status='Active'",
        [pid], one=True)['cnt']

    upcoming = []
    rows = query_db(
        '''SELECT a.*, d.first_name || ' ' || d.last_name as doctor_name,
                  dep.name as department_name
           FROM appointments a
           LEFT JOIN doctors d ON a.doctor_id=d.id
           LEFT JOIN departments dep ON a.department_id=dep.id
           WHERE a.patient_id=? AND a.appointment_date >= date('now')
           AND a.status IN ('Confirmed','Requested')
           ORDER BY a.appointment_date, a.appointment_time LIMIT 5''', [pid])
    for r in rows:
        upcoming.append(dict(r))

    recent_reports = []
    rows = query_db(
        "SELECT id, report_type, title, report_date, verification_status FROM reports WHERE patient_id=? ORDER BY report_date DESC LIMIT 5",
        [pid])
    for r in rows:
        recent_reports.append(dict(r))

    return jsonify({
        'stats': {
            'total_visits': total_visits,
            'upcoming_appointments': upcoming_appointments,
            'total_reports': total_reports,
            'pending_bills': pending_bills,
            'active_prescriptions': active_prescriptions
        },
        'upcoming_appointments': upcoming,
        'recent_reports': recent_reports
    }), 200
