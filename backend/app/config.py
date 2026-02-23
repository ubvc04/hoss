import os
import secrets

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))

    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', secrets.token_hex(32))
    JWT_ACCESS_TOKEN_EXPIRES = 3600 * 8  # 8 hours
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    DATABASE_PATH = os.path.join(PROJECT_DIR, 'hospital.db')
    SCHEMA_PATH = os.path.join(PROJECT_DIR, 'migrations', 'schema.sql')

    UPLOAD_FOLDER = os.path.join(PROJECT_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'dcm', 'doc', 'docx'}

    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')

    # SMTP Configuration
    SMTP_EMAIL = 'baveshchowdary1@gmail.com'
    SMTP_PASSWORD = 'snyr vgat cycn fztt'
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587

    # =====================================================
    # BLOCKCHAIN CONFIGURATION
    # =====================================================
    
    # Simulation mode (True for development, False for production with real Fabric)
    BLOCKCHAIN_SIMULATION_MODE = os.environ.get('BLOCKCHAIN_SIMULATION_MODE', 'true').lower() == 'true'
    
    # Hyperledger Fabric Configuration
    FABRIC_CHANNEL = os.environ.get('FABRIC_CHANNEL', 'hms-channel')
    FABRIC_CHAINCODE = os.environ.get('FABRIC_CHAINCODE', 'medical_records')
    FABRIC_MSP_ID = os.environ.get('FABRIC_MSP_ID', 'HospitalMSP')
    FABRIC_PEER_ENDPOINT = os.environ.get('FABRIC_PEER_ENDPOINT', 'localhost:7051')
    FABRIC_ORDERER_ENDPOINT = os.environ.get('FABRIC_ORDERER_ENDPOINT', 'localhost:7050')
    FABRIC_TLS_ENABLED = os.environ.get('FABRIC_TLS_ENABLED', 'true').lower() == 'true'
    
    # Fabric crypto materials paths (set these in production)
    FABRIC_CRYPTO_PATH = os.environ.get('FABRIC_CRYPTO_PATH', '')
    FABRIC_CERT_PATH = os.environ.get('FABRIC_CERT_PATH', '')
    FABRIC_KEY_PATH = os.environ.get('FABRIC_KEY_PATH', '')
    FABRIC_TLS_CERT_PATH = os.environ.get('FABRIC_TLS_CERT_PATH', '')
    
    # IPFS Configuration
    IPFS_PROVIDER = os.environ.get('IPFS_PROVIDER', 'pinata')  # pinata, infura, or local
    IPFS_GATEWAY = os.environ.get('IPFS_GATEWAY', 'https://gateway.pinata.cloud/ipfs/')
    
    # Pinata (recommended for production)
    PINATA_API_KEY = os.environ.get('PINATA_API_KEY', '2a8f21a5b7f2a5171fb5')
    PINATA_SECRET_KEY = os.environ.get('PINATA_SECRET_KEY', 'db9ad461ffee4e56af0cb38505a60c4cc3d4e44e370fee1767b4ec339a6dc755')
    
    # Infura (alternative)
    INFURA_IPFS_PROJECT_ID = os.environ.get('INFURA_IPFS_PROJECT_ID', '')
    INFURA_IPFS_PROJECT_SECRET = os.environ.get('INFURA_IPFS_PROJECT_SECRET', '')
    
    # Local IPFS node (for development)
    LOCAL_IPFS_URL = os.environ.get('LOCAL_IPFS_URL', 'http://localhost:5001')
    
    # File Encryption Key (MUST be set in production - 64 hex chars = 256 bits)
    # Generate with: python -c "import os; print(os.urandom(32).hex())"
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', '')
