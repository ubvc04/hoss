"""
Hash Builder Utility
Builds canonical strings and generates SHA-256 hashes for medical records.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional


class HashBuilder:
    """
    Builds deterministic canonical strings from record data and generates SHA-256 hashes.
    Canonical strings ensure consistent hashing regardless of field order.
    """

    @staticmethod
    def _normalize_value(value: Any) -> str:
        """Normalize a value to string for hashing."""
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, (list, dict)):
            return json.dumps(value, sort_keys=True, separators=(',', ':'))
        return str(value).strip()

    @staticmethod
    def _build_canonical_string(fields: Dict[str, Any], field_order: List[str]) -> str:
        """
        Build a canonical string from fields in a specific order.
        Format: field1=value1|field2=value2|...
        """
        parts = []
        for field in field_order:
            value = fields.get(field)
            normalized = HashBuilder._normalize_value(value)
            parts.append(f"{field}={normalized}")
        return "|".join(parts)

    @staticmethod
    def generate_hash(data: str) -> str:
        """Generate SHA-256 hash of a string."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    @staticmethod
    def generate_file_hash(file_data: bytes) -> str:
        """Generate SHA-256 hash of file bytes."""
        return hashlib.sha256(file_data).hexdigest()

    # =====================================================
    # PATIENT HASH
    # =====================================================
    @staticmethod
    def build_patient_hash(patient: Dict[str, Any]) -> str:
        """
        Build hash for patient record.
        Fields: mrn, first_name, last_name, date_of_birth, gender, phone, email, national_id
        """
        field_order = [
            'mrn', 'first_name', 'last_name', 'date_of_birth', 'gender',
            'phone', 'email', 'national_id', 'blood_group', 'address_line1',
            'city', 'state', 'postal_code', 'country'
        ]
        canonical = HashBuilder._build_canonical_string(patient, field_order)
        return HashBuilder.generate_hash(canonical)

    # =====================================================
    # VISIT HASH
    # =====================================================
    @staticmethod
    def build_visit_hash(visit: Dict[str, Any]) -> str:
        """
        Build hash for visit record.
        Fields: patient_id, doctor_id, department_id, visit_type, admission_date, 
                chief_complaint, room_number, bed_number
        """
        field_order = [
            'patient_id', 'doctor_id', 'department_id', 'visit_type',
            'admission_date', 'chief_complaint', 'room_number', 'bed_number',
            'ward', 'status'
        ]
        canonical = HashBuilder._build_canonical_string(visit, field_order)
        return HashBuilder.generate_hash(canonical)

    # =====================================================
    # PRESCRIPTION HASH
    # =====================================================
    @staticmethod
    def build_prescription_hash(prescription: Dict[str, Any], medications: List[Dict[str, Any]]) -> str:
        """
        Build hash for prescription record.
        Fields: patient_id, doctor_id, visit_id, notes, prescription_date
        Plus: medications list (name, dosage, frequency, duration, instructions)
        """
        # Build base fields
        field_order = ['patient_id', 'doctor_id', 'visit_id', 'notes', 'prescription_date']
        base_canonical = HashBuilder._build_canonical_string(prescription, field_order)

        # Build medications canonical string
        med_parts = []
        for med in sorted(medications, key=lambda x: x.get('medicine_name', '')):
            med_fields = ['medicine_name', 'dosage', 'frequency', 'duration', 'instructions', 'quantity']
            med_canonical = HashBuilder._build_canonical_string(med, med_fields)
            med_parts.append(med_canonical)

        medications_str = ";".join(med_parts)
        full_canonical = f"{base_canonical}|medications=[{medications_str}]"
        return HashBuilder.generate_hash(full_canonical)

    # =====================================================
    # BILLING / INVOICE HASH
    # =====================================================
    @staticmethod
    def build_invoice_hash(invoice: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
        """
        Build hash for invoice record.
        Fields: patient_id, visit_id, invoice_number, due_date, notes
        Plus: line items (category, description, quantity, unit_price)
        """
        field_order = ['patient_id', 'visit_id', 'invoice_number', 'due_date', 'notes', 'invoice_date']
        base_canonical = HashBuilder._build_canonical_string(invoice, field_order)

        # Build items canonical string
        item_parts = []
        for item in sorted(items, key=lambda x: (x.get('category', ''), x.get('description', ''))):
            item_fields = ['category', 'description', 'quantity', 'unit_price']
            item_canonical = HashBuilder._build_canonical_string(item, item_fields)
            item_parts.append(item_canonical)

        items_str = ";".join(item_parts)
        full_canonical = f"{base_canonical}|items=[{items_str}]"
        return HashBuilder.generate_hash(full_canonical)

    # =====================================================
    # APPOINTMENT HASH
    # =====================================================
    @staticmethod
    def build_appointment_hash(appointment: Dict[str, Any]) -> str:
        """
        Build hash for appointment record.
        Fields: patient_id, doctor_id, appointment_date, appointment_time, visit_type, reason
        """
        field_order = [
            'patient_id', 'doctor_id', 'department_id', 'appointment_date',
            'appointment_time', 'visit_type', 'reason', 'status'
        ]
        canonical = HashBuilder._build_canonical_string(appointment, field_order)
        return HashBuilder.generate_hash(canonical)

    # =====================================================
    # REPORT HASH (Form fields only - separate from file)
    # =====================================================
    @staticmethod
    def build_report_form_hash(report: Dict[str, Any]) -> str:
        """
        Build hash for report form fields (excluding file).
        Fields: patient_id, visit_id, report_type, title, description, 
                ordering_doctor_id, department_id, report_date, result_summary
        """
        field_order = [
            'patient_id', 'visit_id', 'report_type', 'title', 'description',
            'ordering_doctor_id', 'department_id', 'report_date', 'result_summary'
        ]
        canonical = HashBuilder._build_canonical_string(report, field_order)
        return HashBuilder.generate_hash(canonical)

    # =====================================================
    # COMBINED REPORT HASH PAYLOAD
    # =====================================================
    @staticmethod
    def build_report_hash_payload(
        form_hash: str,
        file_hash: Optional[str] = None,
        ipfs_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build combined hash payload for report (form + optional file).
        """
        payload = {
            'formHash': form_hash
        }
        if file_hash:
            payload['fileHash'] = file_hash
        if ipfs_hash:
            payload['ipfsHash'] = ipfs_hash
        return payload

    # =====================================================
    # SIMPLE HASH PAYLOAD
    # =====================================================
    @staticmethod
    def build_simple_hash_payload(hash_value: str) -> Dict[str, str]:
        """Build simple hash payload for form-only records."""
        return {'hash': hash_value}
