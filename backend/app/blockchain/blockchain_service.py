"""
Blockchain Service
Main orchestration service for all blockchain operations.
Provides simple API for route handlers to store and verify records.
"""

import os
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from .hash_builder import HashBuilder
from .fabric_client import get_fabric_client
from .ipfs_client import get_ipfs_client
from .encryption import get_encryption_service
from .integrity_service import get_integrity_service


def _persist_to_db(record_type: str, record_id: int, blockchain_record_id: str, 
                   tx_id: str, record_hash: str, ipfs_hash: str = None, 
                   encryption_iv: str = None, file_hash: str = None, created_by: int = None):
    """Persist blockchain record to database."""
    try:
        from ..database import get_db
        db = get_db()
        db.execute('''
            INSERT INTO record_blockchain_map 
            (record_type, record_id, blockchain_record_id, transaction_id, record_hash, 
             file_hash, ipfs_hash, encryption_iv, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(record_type, record_id) DO UPDATE SET
            transaction_id=excluded.transaction_id,
            record_hash=excluded.record_hash,
            file_hash=excluded.file_hash,
            ipfs_hash=excluded.ipfs_hash,
            encryption_iv=excluded.encryption_iv,
            updated_at=CURRENT_TIMESTAMP
        ''', [record_type, record_id, blockchain_record_id, tx_id, record_hash,
              file_hash, ipfs_hash, encryption_iv, created_by])
        db.commit()
    except Exception as e:
        print(f"Warning: Failed to persist blockchain record to DB: {e}")


class BlockchainService:
    """
    Main service for blockchain operations.
    Orchestrates hashing, encryption, IPFS upload, and Fabric transactions.
    """

    # Record type constants
    TYPE_PATIENT = 'PATIENT'
    TYPE_VISIT = 'VISIT'
    TYPE_PRESCRIPTION = 'PRESCRIPTION'
    TYPE_REPORT = 'REPORT'
    TYPE_INVOICE = 'INVOICE'
    TYPE_APPOINTMENT = 'APPOINTMENT'

    def __init__(self):
        self.hash_builder = HashBuilder()
        self.fabric_client = get_fabric_client()
        self.ipfs_client = get_ipfs_client()
        self.encryption_service = get_encryption_service()
        self.integrity_service = get_integrity_service()

    # =====================================================
    # PATIENT OPERATIONS
    # =====================================================

    def store_patient(
        self,
        patient_id: int,
        patient_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store patient record hash on blockchain.
        
        Args:
            patient_id: Patient database ID
            patient_data: Patient record data
            metadata: Optional metadata (created_by, etc.)
            
        Returns:
            Result dict with success status and transaction details
        """
        record_id = f'patient_{patient_id}'
        patient_id_str = str(patient_id)
        
        # Generate hash
        record_hash = self.hash_builder.build_patient_hash(patient_data)
        hash_payload = self.hash_builder.build_simple_hash_payload(record_hash)
        
        # Store on blockchain
        success, tx_id, error = self.fabric_client.add_record_hash(
            record_id=record_id,
            record_type=self.TYPE_PATIENT,
            patient_id=patient_id_str,
            hash_payload=hash_payload,
            metadata=metadata
        )

        # Persist to database
        if success:
            created_by = metadata.get('createdBy') if metadata else None
            _persist_to_db(self.TYPE_PATIENT, patient_id, record_id, tx_id, record_hash, created_by=created_by)

        return {
            'success': success,
            'recordId': record_id,
            'recordType': self.TYPE_PATIENT,
            'hash': record_hash,
            'transactionId': tx_id if success else None,
            'error': error if not success else None,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    def verify_patient(self, patient_id: int, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify patient record integrity."""
        return self.integrity_service.verify_patient(patient_id, patient_data)

    # =====================================================
    # VISIT OPERATIONS
    # =====================================================

    def store_visit(
        self,
        visit_id: int,
        patient_id: int,
        visit_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store visit record hash on blockchain."""
        record_id = f'visit_{visit_id}'
        
        record_hash = self.hash_builder.build_visit_hash(visit_data)
        hash_payload = self.hash_builder.build_simple_hash_payload(record_hash)
        
        success, tx_id, error = self.fabric_client.add_record_hash(
            record_id=record_id,
            record_type=self.TYPE_VISIT,
            patient_id=str(patient_id),
            hash_payload=hash_payload,
            metadata=metadata
        )

        if success:
            created_by = metadata.get('createdBy') if metadata else None
            _persist_to_db(self.TYPE_VISIT, visit_id, record_id, tx_id, record_hash, created_by=created_by)

        return {
            'success': success,
            'recordId': record_id,
            'recordType': self.TYPE_VISIT,
            'hash': record_hash,
            'transactionId': tx_id if success else None,
            'error': error if not success else None,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    def verify_visit(self, visit_id: int, visit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify visit record integrity."""
        return self.integrity_service.verify_visit(visit_id, visit_data)

    # =====================================================
    # PRESCRIPTION OPERATIONS
    # =====================================================

    def store_prescription(
        self,
        prescription_id: int,
        patient_id: int,
        prescription_data: Dict[str, Any],
        medications: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store prescription record hash on blockchain."""
        record_id = f'prescription_{prescription_id}'
        
        record_hash = self.hash_builder.build_prescription_hash(prescription_data, medications)
        hash_payload = self.hash_builder.build_simple_hash_payload(record_hash)
        
        success, tx_id, error = self.fabric_client.add_record_hash(
            record_id=record_id,
            record_type=self.TYPE_PRESCRIPTION,
            patient_id=str(patient_id),
            hash_payload=hash_payload,
            metadata=metadata
        )

        if success:
            created_by = metadata.get('createdBy') if metadata else None
            _persist_to_db(self.TYPE_PRESCRIPTION, prescription_id, record_id, tx_id, record_hash, created_by=created_by)

        return {
            'success': success,
            'recordId': record_id,
            'recordType': self.TYPE_PRESCRIPTION,
            'hash': record_hash,
            'transactionId': tx_id if success else None,
            'error': error if not success else None,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    def verify_prescription(
        self,
        prescription_id: int,
        prescription_data: Dict[str, Any],
        medications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Verify prescription record integrity."""
        return self.integrity_service.verify_prescription(prescription_id, prescription_data, medications)

    # =====================================================
    # INVOICE / BILLING OPERATIONS
    # =====================================================

    def store_invoice(
        self,
        invoice_id: int,
        patient_id: int,
        invoice_data: Dict[str, Any],
        items: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store invoice record hash on blockchain."""
        record_id = f'invoice_{invoice_id}'
        
        record_hash = self.hash_builder.build_invoice_hash(invoice_data, items)
        hash_payload = self.hash_builder.build_simple_hash_payload(record_hash)
        
        success, tx_id, error = self.fabric_client.add_record_hash(
            record_id=record_id,
            record_type=self.TYPE_INVOICE,
            patient_id=str(patient_id),
            hash_payload=hash_payload,
            metadata=metadata
        )

        if success:
            created_by = metadata.get('createdBy') if metadata else None
            _persist_to_db(self.TYPE_INVOICE, invoice_id, record_id, tx_id, record_hash, created_by=created_by)

        return {
            'success': success,
            'recordId': record_id,
            'recordType': self.TYPE_INVOICE,
            'hash': record_hash,
            'transactionId': tx_id if success else None,
            'error': error if not success else None,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    def verify_invoice(
        self,
        invoice_id: int,
        invoice_data: Dict[str, Any],
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Verify invoice record integrity."""
        return self.integrity_service.verify_invoice(invoice_id, invoice_data, items)

    # =====================================================
    # APPOINTMENT OPERATIONS
    # =====================================================

    def store_appointment(
        self,
        appointment_id: int,
        patient_id: int,
        appointment_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store appointment record hash on blockchain."""
        record_id = f'appointment_{appointment_id}'
        
        record_hash = self.hash_builder.build_appointment_hash(appointment_data)
        hash_payload = self.hash_builder.build_simple_hash_payload(record_hash)
        
        success, tx_id, error = self.fabric_client.add_record_hash(
            record_id=record_id,
            record_type=self.TYPE_APPOINTMENT,
            patient_id=str(patient_id),
            hash_payload=hash_payload,
            metadata=metadata
        )

        if success:
            created_by = metadata.get('createdBy') if metadata else None
            _persist_to_db(self.TYPE_APPOINTMENT, appointment_id, record_id, tx_id, record_hash, created_by=created_by)

        return {
            'success': success,
            'recordId': record_id,
            'recordType': self.TYPE_APPOINTMENT,
            'hash': record_hash,
            'transactionId': tx_id if success else None,
            'error': error if not success else None,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    def verify_appointment(self, appointment_id: int, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify appointment record integrity."""
        return self.integrity_service.verify_appointment(appointment_id, appointment_data)

    # =====================================================
    # REPORT OPERATIONS (with file handling)
    # =====================================================

    def store_report(
        self,
        report_id: int,
        patient_id: int,
        report_data: Dict[str, Any],
        file_data: Optional[bytes] = None,
        filename: Optional[str] = None,
        upload_to_ipfs: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store report record on blockchain with optional file handling.
        
        For reports with files:
        1. Encrypt file
        2. Upload encrypted file to IPFS
        3. Hash both form data and file
        4. Store combined hash payload on blockchain
        
        Args:
            report_id: Report database ID
            patient_id: Patient ID
            report_data: Report form data
            file_data: Optional file bytes
            filename: Original filename
            upload_to_ipfs: Whether to upload file to IPFS
            metadata: Optional metadata
            
        Returns:
            Result with blockchain and IPFS details
        """
        record_id = f'report_{report_id}'
        
        # Calculate form hash
        form_hash = self.hash_builder.build_report_form_hash(report_data)
        
        file_hash = None
        ipfs_hash = None
        encryption_iv = None
        
        # Handle file if provided
        if file_data and filename:
            # Calculate file hash before encryption
            file_hash = self.hash_builder.generate_file_hash(file_data)
            
            if upload_to_ipfs:
                # Encrypt file
                encrypted_data, encryption_iv = self.encryption_service.encrypt_for_storage(file_data)
                
                # Upload to IPFS
                success, ipfs_hash, ipfs_error = self.ipfs_client.upload_file(
                    encrypted_data,
                    f'{filename}.enc',
                    metadata={'reportId': str(report_id), 'patientId': str(patient_id)}
                )
                
                if not success:
                    return {
                        'success': False,
                        'recordId': record_id,
                        'error': f'IPFS upload failed: {ipfs_error}',
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    }
        
        # Build hash payload
        hash_payload = self.hash_builder.build_report_hash_payload(
            form_hash=form_hash,
            file_hash=file_hash,
            ipfs_hash=ipfs_hash
        )
        
        # Store on blockchain
        success, tx_id, error = self.fabric_client.add_record_hash(
            record_id=record_id,
            record_type=self.TYPE_REPORT,
            patient_id=str(patient_id),
            hash_payload=hash_payload,
            metadata=metadata
        )

        result = {
            'success': success,
            'recordId': record_id,
            'recordType': self.TYPE_REPORT,
            'formHash': form_hash,
            'transactionId': tx_id if success else None,
            'error': error if not success else None,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        if file_hash:
            result['fileHash'] = file_hash
        if ipfs_hash:
            result['ipfsHash'] = ipfs_hash
            result['ipfsUrl'] = self.ipfs_client.get_file_url(ipfs_hash)
        if encryption_iv:
            result['encryptionIv'] = encryption_iv
        
        # Also set result['hash'] for consistency with other store methods
        result['hash'] = form_hash
        
        # Persist to database
        if success:
            created_by = metadata.get('createdBy') if metadata else None
            _persist_to_db(self.TYPE_REPORT, report_id, record_id, tx_id, form_hash,
                          ipfs_hash=ipfs_hash, encryption_iv=encryption_iv, 
                          file_hash=file_hash, created_by=created_by)
            
        return result

    def verify_report(
        self,
        report_id: int,
        report_data: Dict[str, Any],
        file_data: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Verify report record integrity."""
        return self.integrity_service.verify_report(report_id, report_data, file_data)

    def download_report_file(self, ipfs_hash: str, encryption_iv: str) -> Tuple[bool, bytes, str]:
        """
        Download and decrypt report file from IPFS.
        
        Args:
            ipfs_hash: IPFS CID
            encryption_iv: IV used during encryption (hex string)
            
        Returns:
            Tuple of (success, decrypted_data, error_message)
        """
        # Download from IPFS
        success, encrypted_data, error = self.ipfs_client.download_file(ipfs_hash)
        if not success:
            return False, b'', error
        
        # Decrypt
        try:
            decrypted_data = self.encryption_service.decrypt_from_storage(encrypted_data, encryption_iv)
            return True, decrypted_data, ''
        except Exception as e:
            return False, b'', f'Decryption failed: {str(e)}'

    # =====================================================
    # AUDIT & QUERY OPERATIONS
    # =====================================================

    def get_record_history(self, record_id: str) -> Dict[str, Any]:
        """Get audit trail for a record."""
        return self.integrity_service.get_record_audit_trail(record_id)

    def get_patient_records(self, patient_id: int) -> Dict[str, Any]:
        """Get all blockchain records for a patient."""
        return self.integrity_service.get_patient_audit_summary(str(patient_id))

    def get_blockchain_status(self) -> Dict[str, Any]:
        """Get blockchain connection status."""
        return {
            'fabricConnected': self.fabric_client.is_configured(),
            'ipfsConnected': self.ipfs_client.is_configured(),
            'simulationMode': self.fabric_client.simulation_mode,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }


# Singleton instance
_blockchain_service = None


def get_blockchain_service() -> BlockchainService:
    """Get singleton blockchain service instance."""
    global _blockchain_service
    if _blockchain_service is None:
        _blockchain_service = BlockchainService()
    return _blockchain_service
