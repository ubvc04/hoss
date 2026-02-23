"""
Blockchain API Routes
Provides endpoints for blockchain verification and audit trail queries.
"""

from flask import Blueprint, request, jsonify, g
from functools import wraps

from ..blockchain import get_blockchain_service
from ..database import get_db
from ..middleware import jwt_required, role_required

blockchain_bp = Blueprint('blockchain', __name__)


# =====================================================
# STATUS ENDPOINT
# =====================================================

@blockchain_bp.route('/status', methods=['GET'])
def get_status():
    """Get blockchain connection status."""
    try:
        service = get_blockchain_service()
        status = service.get_blockchain_status()
        return jsonify(status), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =====================================================
# GET BLOCKCHAIN RECORDS
# =====================================================

@blockchain_bp.route('/records/patient/<int:patient_id>', methods=['GET'])
@jwt_required
def get_patient_blockchain_records(patient_id):
    """Get all blockchain records for a patient including related records."""
    try:
        db = get_db()
        
        # Get patient record
        patient_record = db.execute('''
            SELECT * FROM record_blockchain_map WHERE record_type='PATIENT' AND record_id=?
        ''', [patient_id]).fetchone()
        
        # Get all related records (visits, prescriptions, etc.)
        visits = db.execute('''
            SELECT rbm.* FROM record_blockchain_map rbm
            JOIN visits v ON rbm.record_id = v.id
            WHERE rbm.record_type='VISIT' AND v.patient_id=?
        ''', [patient_id]).fetchall()
        
        prescriptions = db.execute('''
            SELECT rbm.* FROM record_blockchain_map rbm
            JOIN prescriptions p ON rbm.record_id = p.id
            WHERE rbm.record_type='PRESCRIPTION' AND p.patient_id=?
        ''', [patient_id]).fetchall()
        
        appointments = db.execute('''
            SELECT rbm.* FROM record_blockchain_map rbm
            JOIN appointments a ON rbm.record_id = a.id
            WHERE rbm.record_type='APPOINTMENT' AND a.patient_id=?
        ''', [patient_id]).fetchall()
        
        invoices = db.execute('''
            SELECT rbm.* FROM record_blockchain_map rbm
            JOIN invoices i ON rbm.record_id = i.id
            WHERE rbm.record_type='INVOICE' AND i.patient_id=?
        ''', [patient_id]).fetchall()
        
        reports = db.execute('''
            SELECT rbm.* FROM record_blockchain_map rbm
            JOIN reports r ON rbm.record_id = r.id
            WHERE rbm.record_type='REPORT' AND r.patient_id=?
        ''', [patient_id]).fetchall()
        
        def format_record(row):
            if not row:
                return None
            return {
                'recordType': row['record_type'],
                'recordId': row['record_id'],
                'blockchainRecordId': row['blockchain_record_id'],
                'transactionId': row['transaction_id'],
                'hash': row['record_hash'],
                'fileHash': row['file_hash'],
                'ipfsHash': row['ipfs_hash'],
                'ipfsUrl': f"https://gateway.pinata.cloud/ipfs/{row['ipfs_hash']}" if row['ipfs_hash'] else None,
                'createdAt': row['created_at'],
                'updatedAt': row['updated_at']
            }
        
        return jsonify({
            'patient': format_record(patient_record),
            'visits': [format_record(r) for r in visits],
            'prescriptions': [format_record(r) for r in prescriptions],
            'appointments': [format_record(r) for r in appointments],
            'invoices': [format_record(r) for r in invoices],
            'reports': [format_record(r) for r in reports],
            'totalRecords': 1 + len(visits) + len(prescriptions) + len(appointments) + len(invoices) + len(reports) if patient_record else 0
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@blockchain_bp.route('/records/<record_type>/<int:record_id>', methods=['GET'])
@jwt_required
def get_single_blockchain_record(record_type, record_id):
    """Get blockchain record for a specific record."""
    try:
        db = get_db()
        record = db.execute('''
            SELECT * FROM record_blockchain_map 
            WHERE record_type=? AND record_id=?
        ''', [record_type.upper(), record_id]).fetchone()
        
        if not record:
            return jsonify({'error': 'Blockchain record not found'}), 404
        
        return jsonify({
            'recordType': record['record_type'],
            'recordId': record['record_id'],
            'blockchainRecordId': record['blockchain_record_id'],
            'transactionId': record['transaction_id'],
            'hash': record['record_hash'],
            'fileHash': record['file_hash'],
            'ipfsHash': record['ipfs_hash'],
            'ipfsUrl': f"https://gateway.pinata.cloud/ipfs/{record['ipfs_hash']}" if record['ipfs_hash'] else None,
            'createdAt': record['created_at'],
            'updatedAt': record['updated_at']
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =====================================================
# VERIFICATION ENDPOINTS
# =====================================================

@blockchain_bp.route('/verify/patient/<int:patient_id>', methods=['GET'])
@jwt_required
def verify_patient(patient_id):
    """Verify patient record integrity."""
    try:
        db = get_db()
        cursor = db.execute(
            'SELECT * FROM patients WHERE id = ?',
            (patient_id,)
        )
        patient = cursor.fetchone()
        
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        patient_data = dict(patient)
        service = get_blockchain_service()
        result = service.verify_patient(patient_id, patient_data)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@blockchain_bp.route('/verify/visit/<int:visit_id>', methods=['GET'])
@jwt_required
def verify_visit(visit_id):
    """Verify visit record integrity."""
    try:
        db = get_db()
        cursor = db.execute(
            'SELECT * FROM visits WHERE id = ?',
            (visit_id,)
        )
        visit = cursor.fetchone()
        
        if not visit:
            return jsonify({'error': 'Visit not found'}), 404
        
        visit_data = dict(visit)
        service = get_blockchain_service()
        result = service.verify_visit(visit_id, visit_data)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@blockchain_bp.route('/verify/prescription/<int:prescription_id>', methods=['GET'])
@jwt_required
def verify_prescription(prescription_id):
    """Verify prescription record integrity."""
    try:
        db = get_db()
        
        # Get prescription
        cursor = db.execute(
            'SELECT * FROM prescriptions WHERE id = ?',
            (prescription_id,)
        )
        prescription = cursor.fetchone()
        
        if not prescription:
            return jsonify({'error': 'Prescription not found'}), 404
        
        # Get medications
        cursor = db.execute(
            'SELECT * FROM prescription_medications WHERE prescription_id = ?',
            (prescription_id,)
        )
        medications = [dict(row) for row in cursor.fetchall()]
        
        prescription_data = dict(prescription)
        service = get_blockchain_service()
        result = service.verify_prescription(prescription_id, prescription_data, medications)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@blockchain_bp.route('/verify/invoice/<int:invoice_id>', methods=['GET'])
@jwt_required
def verify_invoice(invoice_id):
    """Verify invoice record integrity."""
    try:
        db = get_db()
        
        # Get invoice
        cursor = db.execute(
            'SELECT * FROM invoices WHERE id = ?',
            (invoice_id,)
        )
        invoice = cursor.fetchone()
        
        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404
        
        # Get items
        cursor = db.execute(
            'SELECT * FROM invoice_items WHERE invoice_id = ?',
            (invoice_id,)
        )
        items = [dict(row) for row in cursor.fetchall()]
        
        invoice_data = dict(invoice)
        service = get_blockchain_service()
        result = service.verify_invoice(invoice_id, invoice_data, items)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@blockchain_bp.route('/verify/appointment/<int:appointment_id>', methods=['GET'])
@jwt_required
def verify_appointment(appointment_id):
    """Verify appointment record integrity."""
    try:
        db = get_db()
        cursor = db.execute(
            'SELECT * FROM appointments WHERE id = ?',
            (appointment_id,)
        )
        appointment = cursor.fetchone()
        
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        appointment_data = dict(appointment)
        service = get_blockchain_service()
        result = service.verify_appointment(appointment_id, appointment_data)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@blockchain_bp.route('/verify/report/<int:report_id>', methods=['GET'])
@jwt_required
def verify_report(report_id):
    """Verify report record integrity."""
    try:
        db = get_db()
        cursor = db.execute(
            'SELECT * FROM reports WHERE id = ?',
            (report_id,)
        )
        report = cursor.fetchone()
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        report_data = dict(report)
        
        # Optionally load file for verification
        # file_data = None  # Load from file system if needed
        
        service = get_blockchain_service()
        result = service.verify_report(report_id, report_data)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =====================================================
# AUDIT TRAIL ENDPOINTS
# =====================================================

@blockchain_bp.route('/audit/record/<record_id>', methods=['GET'])
@jwt_required
@role_required('Admin', 'Doctor')
def get_record_audit(record_id):
    """Get audit trail for a specific record."""
    try:
        service = get_blockchain_service()
        result = service.get_record_history(record_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@blockchain_bp.route('/audit/patient/<int:patient_id>', methods=['GET'])
@jwt_required
@role_required('Admin', 'Doctor')
def get_patient_audit(patient_id):
    """Get all blockchain records for a patient."""
    try:
        service = get_blockchain_service()
        result = service.get_patient_records(patient_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =====================================================
# BATCH VERIFICATION (Admin only)
# =====================================================

@blockchain_bp.route('/verify/batch/patients', methods=['POST'])
@jwt_required
@role_required('Admin')
def batch_verify_patients():
    """Verify multiple patient records."""
    try:
        data = request.get_json() or {}
        patient_ids = data.get('patient_ids', [])
        
        if not patient_ids:
            # Verify all patients
            db = get_db()
            cursor = db.execute('SELECT id FROM patients LIMIT 100')
            patient_ids = [row['id'] for row in cursor.fetchall()]
        
        db = get_db()
        patients = []
        for pid in patient_ids:
            cursor = db.execute('SELECT * FROM patients WHERE id = ?', (pid,))
            patient = cursor.fetchone()
            if patient:
                patients.append((pid, dict(patient)))
        
        from ..blockchain.integrity_service import get_integrity_service
        integrity_service = get_integrity_service()
        result = integrity_service.verify_patient_batch(patients)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =====================================================
# MANUAL STORE (Admin only - for existing records)
# =====================================================

@blockchain_bp.route('/store/patient/<int:patient_id>', methods=['POST'])
@jwt_required
@role_required('Admin')
def store_patient(patient_id):
    """Manually store patient record on blockchain."""
    try:
        db = get_db()
        cursor = db.execute(
            'SELECT * FROM patients WHERE id = ?',
            (patient_id,)
        )
        patient = cursor.fetchone()
        
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        patient_data = dict(patient)
        service = get_blockchain_service()
        result = service.store_patient(
            patient_id,
            patient_data,
            metadata={'storedBy': g.current_user.get('id'), 'manual': True}
        )
        
        # Log to blockchain audit
        _log_blockchain_operation(
            db, 'STORE', 'PATIENT', patient_id,
            result.get('recordId'),
            result.get('transactionId'),
            'SUCCESS' if result.get('success') else 'FAILED',
            error_message=result.get('error'),
            created_by=g.current_user.get('id')
        )
        
        return jsonify(result), 200 if result.get('success') else 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _log_blockchain_operation(
    db, operation_type, record_type, record_id,
    blockchain_record_id=None, transaction_id=None,
    status='SUCCESS', verification_result=None,
    error_message=None, metadata=None, created_by=None
):
    """Log blockchain operation to audit table."""
    import json
    try:
        db.execute(
            '''INSERT INTO blockchain_audit_log 
               (operation_type, record_type, record_id, blockchain_record_id,
                transaction_id, status, verification_result, error_message,
                metadata, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (operation_type, record_type, record_id, blockchain_record_id,
             transaction_id, status, verification_result, error_message,
             json.dumps(metadata) if metadata else None, created_by)
        )
        db.commit()
    except Exception:
        pass  # Don't fail if audit logging fails
