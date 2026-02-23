"""
IPFS Client
Handles upload and download of encrypted files to/from IPFS.
Supports Pinata, Infura, or local IPFS node.
"""

import os
import requests
from typing import Optional, Tuple
from ..config import Config


class IPFSClient:
    """
    IPFS client for uploading and downloading encrypted report files.
    Supports multiple IPFS providers: Pinata, Infura, or local node.
    """

    def __init__(self):
        self.provider = getattr(Config, 'IPFS_PROVIDER', 'pinata')  # pinata, infura, or local
        self.pinata_api_key = getattr(Config, 'PINATA_API_KEY', '')
        self.pinata_secret = getattr(Config, 'PINATA_SECRET_KEY', '')
        self.infura_project_id = getattr(Config, 'INFURA_IPFS_PROJECT_ID', '')
        self.infura_project_secret = getattr(Config, 'INFURA_IPFS_PROJECT_SECRET', '')
        self.local_ipfs_url = getattr(Config, 'LOCAL_IPFS_URL', 'http://localhost:5001')
        self.ipfs_gateway = getattr(Config, 'IPFS_GATEWAY', 'https://gateway.pinata.cloud/ipfs/')

    def upload_file(self, file_data: bytes, filename: str, metadata: Optional[dict] = None) -> Tuple[bool, str, str]:
        """
        Upload encrypted file to IPFS.
        
        Args:
            file_data: Encrypted file bytes
            filename: Original filename
            metadata: Optional metadata dict
            
        Returns:
            Tuple of (success, ipfs_hash, error_message)
        """
        if self.provider == 'pinata':
            return self._upload_to_pinata(file_data, filename, metadata)
        elif self.provider == 'infura':
            return self._upload_to_infura(file_data, filename)
        else:
            return self._upload_to_local(file_data, filename)

    def _upload_to_pinata(self, file_data: bytes, filename: str, metadata: Optional[dict] = None) -> Tuple[bool, str, str]:
        """Upload to Pinata IPFS service."""
        import json
        
        if not self.pinata_api_key or not self.pinata_secret:
            return False, '', 'Pinata API credentials not configured'

        url = 'https://api.pinata.cloud/pinning/pinFileToIPFS'
        headers = {
            'pinata_api_key': self.pinata_api_key,
            'pinata_secret_api_key': self.pinata_secret
        }

        files = {
            'file': (filename, file_data)
        }

        # Add metadata if provided (must be proper JSON)
        if metadata:
            pinata_metadata = {
                'name': filename,
                'keyvalues': metadata
            }
            files['pinataMetadata'] = (None, json.dumps(pinata_metadata), 'application/json')

        try:
            response = requests.post(url, headers=headers, files=files, timeout=60)
            if response.status_code == 200:
                result = response.json()
                ipfs_hash = result.get('IpfsHash', '')
                return True, ipfs_hash, ''
            else:
                return False, '', f'Pinata upload failed: {response.text}'
        except requests.RequestException as e:
            return False, '', f'Pinata upload error: {str(e)}'

    def _upload_to_infura(self, file_data: bytes, filename: str) -> Tuple[bool, str, str]:
        """Upload to Infura IPFS service."""
        if not self.infura_project_id or not self.infura_project_secret:
            return False, '', 'Infura IPFS credentials not configured'

        url = 'https://ipfs.infura.io:5001/api/v0/add'
        auth = (self.infura_project_id, self.infura_project_secret)
        files = {'file': (filename, file_data)}

        try:
            response = requests.post(url, auth=auth, files=files, timeout=60)
            if response.status_code == 200:
                result = response.json()
                ipfs_hash = result.get('Hash', '')
                return True, ipfs_hash, ''
            else:
                return False, '', f'Infura upload failed: {response.text}'
        except requests.RequestException as e:
            return False, '', f'Infura upload error: {str(e)}'

    def _upload_to_local(self, file_data: bytes, filename: str) -> Tuple[bool, str, str]:
        """Upload to local IPFS node."""
        url = f'{self.local_ipfs_url}/api/v0/add'
        files = {'file': (filename, file_data)}

        try:
            response = requests.post(url, files=files, timeout=60)
            if response.status_code == 200:
                result = response.json()
                ipfs_hash = result.get('Hash', '')
                return True, ipfs_hash, ''
            else:
                return False, '', f'Local IPFS upload failed: {response.text}'
        except requests.RequestException as e:
            return False, '', f'Local IPFS upload error: {str(e)}'

    def download_file(self, ipfs_hash: str) -> Tuple[bool, bytes, str]:
        """
        Download file from IPFS.
        
        Args:
            ipfs_hash: IPFS CID/hash
            
        Returns:
            Tuple of (success, file_data, error_message)
        """
        gateway_url = f'{self.ipfs_gateway}{ipfs_hash}'

        try:
            response = requests.get(gateway_url, timeout=60)
            if response.status_code == 200:
                return True, response.content, ''
            else:
                return False, b'', f'IPFS download failed: {response.status_code}'
        except requests.RequestException as e:
            return False, b'', f'IPFS download error: {str(e)}'

    def pin_file(self, ipfs_hash: str) -> Tuple[bool, str]:
        """
        Pin a file to ensure it stays available.
        Only applicable for Pinata.
        """
        if self.provider != 'pinata':
            return True, 'Pinning only supported for Pinata'

        url = 'https://api.pinata.cloud/pinning/pinByHash'
        headers = {
            'pinata_api_key': self.pinata_api_key,
            'pinata_secret_api_key': self.pinata_secret,
            'Content-Type': 'application/json'
        }
        payload = {'hashToPin': ipfs_hash}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                return True, ''
            else:
                return False, f'Pin failed: {response.text}'
        except requests.RequestException as e:
            return False, f'Pin error: {str(e)}'

    def unpin_file(self, ipfs_hash: str) -> Tuple[bool, str]:
        """
        Unpin a file (for cleanup).
        Only applicable for Pinata.
        """
        if self.provider != 'pinata':
            return True, 'Unpinning only supported for Pinata'

        url = f'https://api.pinata.cloud/pinning/unpin/{ipfs_hash}'
        headers = {
            'pinata_api_key': self.pinata_api_key,
            'pinata_secret_api_key': self.pinata_secret
        }

        try:
            response = requests.delete(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return True, ''
            else:
                return False, f'Unpin failed: {response.text}'
        except requests.RequestException as e:
            return False, f'Unpin error: {str(e)}'

    def get_file_url(self, ipfs_hash: str) -> str:
        """Get the gateway URL for an IPFS hash."""
        return f'{self.ipfs_gateway}{ipfs_hash}'

    def is_configured(self) -> bool:
        """Check if IPFS client is properly configured."""
        if self.provider == 'pinata':
            return bool(self.pinata_api_key and self.pinata_secret)
        elif self.provider == 'infura':
            return bool(self.infura_project_id and self.infura_project_secret)
        else:
            return True  # Local IPFS assumed available


# Singleton instance
_ipfs_client = None

def get_ipfs_client() -> IPFSClient:
    """Get singleton IPFS client instance."""
    global _ipfs_client
    if _ipfs_client is None:
        _ipfs_client = IPFSClient()
    return _ipfs_client
