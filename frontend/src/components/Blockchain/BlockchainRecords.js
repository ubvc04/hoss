import React, { useState, useEffect } from 'react';
import axios from '../../api/axios';
import './BlockchainRecords.css';

const BlockchainRecords = ({ patientId }) => {
  const [records, setRecords] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState({});

  useEffect(() => {
    fetchBlockchainRecords();
  }, [patientId]);

  const fetchBlockchainRecords = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/blockchain/records/patient/${patientId}`);
      setRecords(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load blockchain records');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (key) => {
    setExpanded(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleString();
  };

  const renderRecordCard = (record, title, icon) => {
    if (!record) return null;
    
    const key = `${record.recordType}-${record.recordId}`;
    const isExpanded = expanded[key];

    return (
      <div className="blockchain-record-card" key={key}>
        <div className="record-header" onClick={() => toggleExpand(key)}>
          <span className="record-icon">{icon}</span>
          <span className="record-title">{title}</span>
          <span className="record-status verified">✓ On Blockchain</span>
          <span className="expand-icon">{isExpanded ? '▼' : '▶'}</span>
        </div>
        
        {isExpanded && (
          <div className="record-details">
            <div className="detail-row">
              <label>Record Hash:</label>
              <div className="hash-value">
                <code>{record.hash}</code>
                <button onClick={() => copyToClipboard(record.hash)} title="Copy">📋</button>
              </div>
            </div>
            
            <div className="detail-row">
              <label>Transaction ID:</label>
              <div className="hash-value">
                <code>{record.transactionId}</code>
                <button onClick={() => copyToClipboard(record.transactionId)} title="Copy">📋</button>
              </div>
            </div>
            
            <div className="detail-row">
              <label>Blockchain Record ID:</label>
              <code>{record.blockchainRecordId}</code>
            </div>
            
            {record.ipfsHash && (
              <>
                <div className="detail-row">
                  <label>IPFS Hash (File):</label>
                  <div className="hash-value">
                    <code>{record.ipfsHash}</code>
                    <button onClick={() => copyToClipboard(record.ipfsHash)} title="Copy">📋</button>
                  </div>
                </div>
                <div className="detail-row">
                  <label>IPFS URL:</label>
                  <a href={record.ipfsUrl} target="_blank" rel="noopener noreferrer">
                    View on IPFS Gateway
                  </a>
                </div>
              </>
            )}
            
            {record.fileHash && (
              <div className="detail-row">
                <label>File Hash:</label>
                <code>{record.fileHash}</code>
              </div>
            )}
            
            <div className="detail-row">
              <label>Recorded At:</label>
              <span>{formatDate(record.createdAt)}</span>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderRecordList = (recordList, title, icon) => {
    if (!recordList || recordList.length === 0) return null;
    
    return (
      <div className="record-section">
        <h4>{icon} {title} ({recordList.length})</h4>
        {recordList.map((record, idx) => 
          renderRecordCard(record, `${title.slice(0, -1)} #${record.recordId}`, icon)
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="blockchain-records-container">
        <div className="loading">Loading blockchain records...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="blockchain-records-container">
        <div className="error">{error}</div>
      </div>
    );
  }

  if (!records || records.totalRecords === 0) {
    return (
      <div className="blockchain-records-container">
        <div className="no-records">
          <span className="icon">🔗</span>
          <p>No blockchain records found for this patient.</p>
          <small>Records are automatically created when patient data is added or updated.</small>
        </div>
      </div>
    );
  }

  return (
    <div className="blockchain-records-container">
      <div className="blockchain-header">
        <h3>🔗 Blockchain Verification</h3>
        <span className="total-records">{records.totalRecords} records on chain</span>
      </div>
      
      <div className="blockchain-info">
        <div className="info-item">
          <span className="label">Network:</span>
          <span className="value">Hyperledger Fabric (Simulation)</span>
        </div>
        <div className="info-item">
          <span className="label">Storage:</span>
          <span className="value">IPFS via Pinata</span>
        </div>
      </div>

      {renderRecordCard(records.patient, 'Patient Record', '👤')}
      {renderRecordList(records.visits, 'Visits', '🏥')}
      {renderRecordList(records.prescriptions, 'Prescriptions', '💊')}
      {renderRecordList(records.appointments, 'Appointments', '📅')}
      {renderRecordList(records.invoices, 'Invoices', '💰')}
      {renderRecordList(records.reports, 'Reports', '📄')}
    </div>
  );
};

export default BlockchainRecords;
