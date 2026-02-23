"""
Integrity Service
Verification APIs to compare database data hash vs blockchain stored hash.
Detects tampering and data corruption.
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from .hash_builder import HashBuilder
from .fabric_client import get_fabric_client


class IntegrityService:
    """
    Service for verifying data integrity by comparing
    current database state against blockchain-stored hashes.
    """

    def __init__(self):
        self.hash_builder = HashBuilder()
        self.fabric_client = get_fabric_client()

    # =====================================================
    # VERIFICATION METHODS
    # =====================================================

    def verify_patient(self, patient_id: int, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify patient record integrity.
        
        Args:
            patient_id: Patient database ID
            patient_data: Current patient data from database
            
        Returns:
            Verification result dict with status and details
        """
        record_id = f'patient_{patient_id}'
        current_hash = self.hash_builder.build_patient_hash(patient_data)
        return self._verify_record(record_id, current_hash, 'PATIENT')

    def verify_visit(self, visit_id: int, visit_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify visit record integrity.
        """
        record_id = f'visit_{visit_id}'
        current_hash = self.hash_builder.build_visit_hash(visit_data)
        return self._verify_record(record_id, current_hash, 'VISIT')

    def verify_prescription(
        self,
        prescription_id: int,
        prescription_data: Dict[str, Any],
        medications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verify prescription record integrity.
        """
        record_id = f'prescription_{prescription_id}'
        current_hash = self.hash_builder.build_prescription_hash(prescription_data, medications)
        return self._verify_record(record_id, current_hash, 'PRESCRIPTION')

    def verify_invoice(
        self,
        invoice_id: int,
        invoice_data: Dict[str, Any],
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verify invoice record integrity.
        """
        record_id = f'invoice_{invoice_id}'
        current_hash = self.hash_builder.build_invoice_hash(invoice_data, items)
        return self._verify_record(record_id, current_hash, 'INVOICE')

    def verify_appointment(self, appointment_id: int, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify appointment record integrity.
        """
        record_id = f'appointment_{appointment_id}'
        current_hash = self.hash_builder.build_appointment_hash(appointment_data)
        return self._verify_record(record_id, current_hash, 'APPOINTMENT')

    def verify_report(
        self,
        report_id: int,
        report_data: Dict[str, Any],
        file_data: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Verify report record integrity (form and optionally file).
        
        Args:
            report_id: Report database ID
            report_data: Current report data from database
            file_data: Optional file bytes for file hash verification
            
        Returns:
            Verification result with form and file verification status
        """
        record_id = f'report_{report_id}'
        
        # Get stored record from blockchain
        success, stored_record, error = self.fabric_client.get_record_hash(record_id)
        
        if not success:
            return {
                'verified': False,
                'status': 'ERROR',
                'error': error or 'Failed to retrieve blockchain record',
                'recordId': record_id,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

        if stored_record is None:
            return {
                'verified': False,
                'status': 'NOT_FOUND',
                'error': 'Record not found on blockchain',
                'recordId': record_id,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

        # Calculate current form hash
        current_form_hash = self.hash_builder.build_report_form_hash(report_data)
        stored_payload = stored_record.get('hashPayload', {})
        stored_form_hash = stored_payload.get('formHash', '')
        
        form_verified = current_form_hash == stored_form_hash

        # Verify file if provided
        file_verified = None
        if file_data is not None:
            current_file_hash = self.hash_builder.generate_file_hash(file_data)
            stored_file_hash = stored_payload.get('fileHash', '')
            file_verified = current_file_hash == stored_file_hash

        # Overall status
        if file_verified is not None:
            verified = form_verified and file_verified
        else:
            verified = form_verified

        return {
            'verified': verified,
            'status': 'VALID' if verified else 'TAMPERED',
            'recordId': record_id,
            'recordType': 'REPORT',
            'formVerified': form_verified,
            'fileVerified': file_verified,
            'currentFormHash': current_form_hash,
            'storedFormHash': stored_form_hash,
            'blockchainTimestamp': stored_record.get('timestamp'),
            'transactionId': stored_record.get('txID'),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    def _verify_record(self, record_id: str, current_hash: str, record_type: str) -> Dict[str, Any]:
        """
        Internal method to verify a simple record (non-report).
        """
        # Get stored record from blockchain
        success, stored_record, error = self.fabric_client.get_record_hash(record_id)
        
        if not success:
            return {
                'verified': False,
                'status': 'ERROR',
                'error': error or 'Failed to retrieve blockchain record',
                'recordId': record_id,
                'recordType': record_type,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

        if stored_record is None:
            return {
                'verified': False,
                'status': 'NOT_FOUND',
                'error': 'Record not found on blockchain',
                'recordId': record_id,
                'recordType': record_type,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

        # Get stored hash
        stored_payload = stored_record.get('hashPayload', {})
        stored_hash = stored_payload.get('hash', '')
        
        # Compare hashes
        verified = current_hash == stored_hash

        return {
            'verified': verified,
            'status': 'VALID' if verified else 'TAMPERED',
            'recordId': record_id,
            'recordType': record_type,
            'currentHash': current_hash,
            'storedHash': stored_hash,
            'blockchainTimestamp': stored_record.get('timestamp'),
            'transactionId': stored_record.get('txID'),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    # =====================================================
    # BATCH VERIFICATION
    # =====================================================

    def verify_patient_batch(self, patients: List[Tuple[int, Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Verify multiple patient records.
        
        Args:
            patients: List of tuples (patient_id, patient_data)
            
        Returns:
            Summary with list of verification results
        """
        results = []
        valid_count = 0
        tampered_count = 0
        not_found_count = 0
        error_count = 0

        for patient_id, patient_data in patients:
            result = self.verify_patient(patient_id, patient_data)
            results.append(result)
            
            if result['status'] == 'VALID':
                valid_count += 1
            elif result['status'] == 'TAMPERED':
                tampered_count += 1
            elif result['status'] == 'NOT_FOUND':
                not_found_count += 1
            else:
                error_count += 1

        return {
            'totalRecords': len(patients),
            'validRecords': valid_count,
            'tamperedRecords': tampered_count,
            'notFoundRecords': not_found_count,
            'errorRecords': error_count,
            'results': results,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    # =====================================================
    # AUDIT TRAIL
    # =====================================================

    def get_record_audit_trail(self, record_id: str) -> Dict[str, Any]:
        """
        Get the complete audit trail for a record.
        
        Args:
            record_id: Record identifier (e.g., 'patient_123')
            
        Returns:
            Audit trail with all historical changes
        """
        success, history, error = self.fabric_client.get_record_history(record_id)
        
        if not success:
            return {
                'success': False,
                'error': error or 'Failed to retrieve audit trail',
                'recordId': record_id
            }

        return {
            'success': True,
            'recordId': record_id,
            'changesCount': len(history),
            'history': history,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    def get_patient_audit_summary(self, patient_id: str) -> Dict[str, Any]:
        """
        Get audit summary for all records belonging to a patient.
        """
        success, records, error = self.fabric_client.get_records_by_patient(patient_id)
        
        if not success:
            return {
                'success': False,
                'error': error or 'Failed to retrieve patient records',
                'patientId': patient_id
            }

        # Group by record type
        by_type = {}
        for record in records:
            record_type = record.get('recordType', 'UNKNOWN')
            if record_type not in by_type:
                by_type[record_type] = []
            by_type[record_type].append(record)

        return {
            'success': True,
            'patientId': patient_id,
            'totalRecords': len(records),
            'recordsByType': {k: len(v) for k, v in by_type.items()},
            'records': records,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }


# Singleton instance
_integrity_service = None


def get_integrity_service() -> IntegrityService:
    """Get singleton integrity service instance."""
    global _integrity_service
    if _integrity_service is None:
        _integrity_service = IntegrityService()
    return _integrity_service
