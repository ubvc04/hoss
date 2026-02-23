"""
Blockchain Integration Module
Provides blockchain-based integrity and audit capabilities
using Hyperledger Fabric and IPFS.
"""

# Direct imports for commonly used items
from .hash_builder import HashBuilder
from .blockchain_service import get_blockchain_service
from .fabric_client import get_fabric_client
from .ipfs_client import get_ipfs_client
from .encryption import get_encryption_service
from .integrity_service import get_integrity_service

__all__ = [
    'HashBuilder',
    'get_blockchain_service',
    'get_fabric_client',
    'get_ipfs_client',
    'get_encryption_service',
    'get_integrity_service',
]
