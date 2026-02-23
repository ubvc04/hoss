-- Blockchain Integration Tables
-- Run this migration to add blockchain tracking tables

-- Table to map database records to blockchain transactions
CREATE TABLE IF NOT EXISTS record_blockchain_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type VARCHAR(50) NOT NULL,  -- PATIENT, VISIT, PRESCRIPTION, REPORT, INVOICE, APPOINTMENT
    record_id INTEGER NOT NULL,         -- Foreign key to the respective table
    blockchain_record_id VARCHAR(100) NOT NULL,  -- e.g., 'patient_123'
    transaction_id VARCHAR(100),        -- Fabric transaction ID
    record_hash VARCHAR(64) NOT NULL,   -- SHA-256 hash (64 hex chars)
    file_hash VARCHAR(64),              -- SHA-256 hash of file (for reports)
    ipfs_hash VARCHAR(100),             -- IPFS CID for encrypted file
    encryption_iv VARCHAR(32),          -- AES IV for file decryption (32 hex chars)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    UNIQUE(record_type, record_id)
);

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS idx_blockchain_record_type ON record_blockchain_map(record_type);
CREATE INDEX IF NOT EXISTS idx_blockchain_record_id ON record_blockchain_map(record_id);
CREATE INDEX IF NOT EXISTS idx_blockchain_tx_id ON record_blockchain_map(transaction_id);

-- Audit log for blockchain operations
CREATE TABLE IF NOT EXISTS blockchain_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_type VARCHAR(50) NOT NULL,  -- STORE, VERIFY, UPDATE
    record_type VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    blockchain_record_id VARCHAR(100),
    transaction_id VARCHAR(100),
    status VARCHAR(20) NOT NULL,  -- SUCCESS, FAILED, PENDING
    verification_result VARCHAR(20),  -- VALID, TAMPERED, NOT_FOUND (for VERIFY operations)
    error_message TEXT,
    metadata TEXT,  -- JSON metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER
);

-- Index for audit queries
CREATE INDEX IF NOT EXISTS idx_audit_record_type ON blockchain_audit_log(record_type);
CREATE INDEX IF NOT EXISTS idx_audit_status ON blockchain_audit_log(status);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON blockchain_audit_log(created_at);
