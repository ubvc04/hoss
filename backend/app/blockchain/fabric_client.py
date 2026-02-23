"""
Hyperledger Fabric Client
Handles connection to Fabric network and transaction submission.
"""

import json
import os
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from ..config import Config


class FabricClient:
    """
    Client for interacting with Hyperledger Fabric blockchain network.
    Uses Fabric peer CLI or SDK for transaction submission.
    """

    def __init__(self):
        """Initialize Fabric client with network configuration."""
        self.channel_name = getattr(Config, 'FABRIC_CHANNEL', 'hms-channel')
        self.chaincode_name = getattr(Config, 'FABRIC_CHAINCODE', 'medical_records')
        self.msp_id = getattr(Config, 'FABRIC_MSP_ID', 'HospitalMSP')
        self.peer_endpoint = getattr(Config, 'FABRIC_PEER_ENDPOINT', 'localhost:7051')
        self.orderer_endpoint = getattr(Config, 'FABRIC_ORDERER_ENDPOINT', 'localhost:7050')
        self.tls_enabled = getattr(Config, 'FABRIC_TLS_ENABLED', True)
        
        # Path to crypto materials
        self.crypto_path = getattr(Config, 'FABRIC_CRYPTO_PATH', '')
        self.cert_path = getattr(Config, 'FABRIC_CERT_PATH', '')
        self.key_path = getattr(Config, 'FABRIC_KEY_PATH', '')
        self.tls_cert_path = getattr(Config, 'FABRIC_TLS_CERT_PATH', '')
        
        # Simulation mode for development
        self.simulation_mode = getattr(Config, 'BLOCKCHAIN_SIMULATION_MODE', True)
        self._simulated_ledger = {}

    def is_configured(self) -> bool:
        """Check if Fabric client is properly configured."""
        if self.simulation_mode:
            return True
        return all([
            self.cert_path and os.path.exists(self.cert_path),
            self.key_path and os.path.exists(self.key_path)
        ])

    # =====================================================
    # CHAINCODE INVOCATION METHODS
    # =====================================================

    def add_record_hash(
        self,
        record_id: str,
        record_type: str,
        patient_id: str,
        hash_payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, str]:
        """
        Add a record hash to the blockchain.
        
        Args:
            record_id: Unique identifier (e.g., "patient_123", "visit_456")
            record_type: Type of record (PATIENT, VISIT, PRESCRIPTION, etc.)
            patient_id: Associated patient ID for indexing
            hash_payload: Hash data (simple or complex with file hashes)
            metadata: Optional metadata dict
            
        Returns:
            Tuple of (success, transaction_id, error_message)
        """
        if self.simulation_mode:
            return self._simulate_add_record(record_id, record_type, patient_id, hash_payload, metadata)

        args = [
            'AddRecordHash',
            record_id,
            record_type,
            patient_id,
            json.dumps(hash_payload),
            json.dumps(metadata or {})
        ]
        return self._invoke_chaincode(args)

    def get_record_hash(self, record_id: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Get a record hash from the blockchain.
        
        Args:
            record_id: Record identifier
            
        Returns:
            Tuple of (success, record_data, error_message)
        """
        if self.simulation_mode:
            return self._simulate_get_record(record_id)

        args = ['GetRecordHash', record_id]
        success, result, error = self._query_chaincode(args)
        if success and result:
            try:
                return True, json.loads(result), ''
            except json.JSONDecodeError:
                return False, None, 'Invalid JSON response from chaincode'
        return success, None, error

    def get_record_history(self, record_id: str) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Get the history of all changes to a record.
        
        Args:
            record_id: Record identifier
            
        Returns:
            Tuple of (success, history_list, error_message)
        """
        if self.simulation_mode:
            return self._simulate_get_history(record_id)

        args = ['GetRecordHistory', record_id]
        success, result, error = self._query_chaincode(args)
        if success and result:
            try:
                return True, json.loads(result), ''
            except json.JSONDecodeError:
                return False, [], 'Invalid JSON response from chaincode'
        return success, [], error

    def verify_hash(self, record_id: str, hash_to_verify: str) -> Tuple[bool, bool, str]:
        """
        Verify a hash against blockchain stored value.
        
        Args:
            record_id: Record identifier
            hash_to_verify: Hash value to verify
            
        Returns:
            Tuple of (success, is_valid, error_message)
        """
        if self.simulation_mode:
            return self._simulate_verify_hash(record_id, hash_to_verify)

        args = ['VerifyHash', record_id, hash_to_verify]
        success, result, error = self._query_chaincode(args)
        if success and result:
            try:
                data = json.loads(result)
                return True, data.get('isValid', False), ''
            except json.JSONDecodeError:
                return False, False, 'Invalid JSON response from chaincode'
        return success, False, error

    def get_records_by_patient(self, patient_id: str) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Get all record hashes for a patient.
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            Tuple of (success, records_list, error_message)
        """
        if self.simulation_mode:
            return self._simulate_get_by_patient(patient_id)

        args = ['GetRecordsByPatient', patient_id]
        success, result, error = self._query_chaincode(args)
        if success and result:
            try:
                return True, json.loads(result), ''
            except json.JSONDecodeError:
                return False, [], 'Invalid JSON response from chaincode'
        return success, [], error

    def get_records_by_type(self, record_type: str) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Get all record hashes of a specific type.
        
        Args:
            record_type: Record type (PATIENT, VISIT, etc.)
            
        Returns:
            Tuple of (success, records_list, error_message)
        """
        if self.simulation_mode:
            return self._simulate_get_by_type(record_type)

        args = ['GetRecordsByType', record_type]
        success, result, error = self._query_chaincode(args)
        if success and result:
            try:
                return True, json.loads(result), ''
            except json.JSONDecodeError:
                return False, [], 'Invalid JSON response from chaincode'
        return success, [], error

    # =====================================================
    # LOW-LEVEL FABRIC OPERATIONS
    # =====================================================

    def _invoke_chaincode(self, args: List[str]) -> Tuple[bool, str, str]:
        """
        Invoke chaincode function (write operation).
        Uses peer CLI in subprocess.
        """
        try:
            cmd = self._build_peer_command('invoke', args)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                # Extract transaction ID from output
                tx_id = self._extract_tx_id(result.stdout)
                return True, tx_id, ''
            else:
                return False, '', f'Chaincode invoke failed: {result.stderr}'
        except subprocess.TimeoutExpired:
            return False, '', 'Chaincode invoke timeout'
        except Exception as e:
            return False, '', f'Chaincode invoke error: {str(e)}'

    def _query_chaincode(self, args: List[str]) -> Tuple[bool, str, str]:
        """
        Query chaincode function (read operation).
        Uses peer CLI in subprocess.
        """
        try:
            cmd = self._build_peer_command('query', args)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return True, result.stdout.strip(), ''
            else:
                return False, '', f'Chaincode query failed: {result.stderr}'
        except subprocess.TimeoutExpired:
            return False, '', 'Chaincode query timeout'
        except Exception as e:
            return False, '', f'Chaincode query error: {str(e)}'

    def _build_peer_command(self, command: str, args: List[str]) -> List[str]:
        """Build peer CLI command."""
        cmd = [
            'peer', 'chaincode', command,
            '-C', self.channel_name,
            '-n', self.chaincode_name,
            '-c', json.dumps({'function': args[0], 'Args': args[1:]})
        ]
        
        if command == 'invoke':
            cmd.extend(['-o', self.orderer_endpoint])
            if self.tls_enabled:
                cmd.extend(['--tls', '--cafile', self.tls_cert_path])

        return cmd

    def _extract_tx_id(self, output: str) -> str:
        """Extract transaction ID from peer CLI output."""
        # Parse transaction ID from output
        # Format varies by Fabric version
        if 'txid' in output.lower():
            parts = output.split()
            for i, part in enumerate(parts):
                if 'txid' in part.lower() and i + 1 < len(parts):
                    return parts[i + 1].strip('[]')
        return datetime.utcnow().strftime('%Y%m%d%H%M%S') + '-' + os.urandom(8).hex()

    # =====================================================
    # SIMULATION MODE (for development)
    # =====================================================

    def _simulate_add_record(
        self,
        record_id: str,
        record_type: str,
        patient_id: str,
        hash_payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ) -> Tuple[bool, str, str]:
        """Simulate adding record to ledger (development mode)."""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        tx_id = f'sim-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}-{os.urandom(4).hex()}'
        
        record = {
            'recordID': record_id,
            'recordType': record_type,
            'patientID': patient_id,
            'hashPayload': hash_payload,
            'metadata': metadata or {},
            'timestamp': timestamp,
            'txID': tx_id
        }
        
        # Store in simulated ledger with history
        if record_id not in self._simulated_ledger:
            self._simulated_ledger[record_id] = {'current': record, 'history': []}
        else:
            self._simulated_ledger[record_id]['history'].append(
                self._simulated_ledger[record_id]['current']
            )
            self._simulated_ledger[record_id]['current'] = record
        
        return True, tx_id, ''

    def _simulate_get_record(self, record_id: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Simulate getting record from ledger."""
        if record_id in self._simulated_ledger:
            return True, self._simulated_ledger[record_id]['current'], ''
        return False, None, 'Record not found'

    def _simulate_get_history(self, record_id: str) -> Tuple[bool, List[Dict[str, Any]], str]:
        """Simulate getting record history."""
        if record_id in self._simulated_ledger:
            ledger_entry = self._simulated_ledger[record_id]
            history = ledger_entry['history'] + [ledger_entry['current']]
            return True, history, ''
        return False, [], 'Record not found'

    def _simulate_verify_hash(self, record_id: str, hash_to_verify: str) -> Tuple[bool, bool, str]:
        """Simulate hash verification."""
        if record_id in self._simulated_ledger:
            record = self._simulated_ledger[record_id]['current']
            stored_hash = record.get('hashPayload', {}).get('hash', '')
            if not stored_hash:
                stored_hash = record.get('hashPayload', {}).get('formHash', '')
            return True, stored_hash == hash_to_verify, ''
        return False, False, 'Record not found'

    def _simulate_get_by_patient(self, patient_id: str) -> Tuple[bool, List[Dict[str, Any]], str]:
        """Simulate getting records by patient ID."""
        records = []
        for record_id, entry in self._simulated_ledger.items():
            if entry['current'].get('patientID') == patient_id:
                records.append(entry['current'])
        return True, records, ''

    def _simulate_get_by_type(self, record_type: str) -> Tuple[bool, List[Dict[str, Any]], str]:
        """Simulate getting records by type."""
        records = []
        for record_id, entry in self._simulated_ledger.items():
            if entry['current'].get('recordType') == record_type:
                records.append(entry['current'])
        return True, records, ''


# Singleton instance
_fabric_client = None


def get_fabric_client() -> FabricClient:
    """Get singleton Fabric client instance."""
    global _fabric_client
    if _fabric_client is None:
        _fabric_client = FabricClient()
    return _fabric_client
