import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { prescriptionsAPI } from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import Topbar from '../../components/Layout/Topbar';
import { Loading, ErrorMessage, Badge, DetailItem } from '../../components/Common';

const PrescriptionDetail = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [prescription, setPrescription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchPrescription = async () => {
    setLoading(true);
    try {
      const res = await prescriptionsAPI.getById(id);
      setPrescription(res.data);
    } catch { setPrescription(null); }
    setLoading(false);
  };

  useEffect(() => { fetchPrescription(); }, [id]);

  const handleCancel = async () => {
    if (!window.confirm('Cancel this prescription?')) return;
    try {
      await prescriptionsAPI.update(id, { status: 'Cancelled' });
      fetchPrescription();
    } catch (err) { setError(err.response?.data?.error || 'Failed'); }
  };

  if (loading) return <><Topbar title="Prescription Detail" /><div className="page-content"><Loading /></div></>;
  if (error) return <><Topbar title="Prescription Detail" /><div className="page-content"><ErrorMessage message={error} onRetry={fetchPrescription} /></div></>;
  if (!prescription) return null;

  const statusColors = { Active: 'success', Completed: 'info', Cancelled: 'danger' };
  const canCancel = ['Admin', 'Doctor'].includes(user.role) && prescription.status === 'Active';

  return (
    <>
      <Topbar title="Prescription Details" />
      <div className="page-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
          <button className="btn btn-outline" onClick={() => navigate('/prescriptions')}>← Back</button>
          {canCancel && <button className="btn btn-danger" onClick={handleCancel}>Cancel Prescription</button>}
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Prescription #{prescription.id}</h3>
            <Badge status={statusColors[prescription.status]} text={prescription.status} />
          </div>
          <div className="detail-grid">
            <DetailItem label="Patient" value={prescription.patient_name} />
            <DetailItem label="Doctor" value={`Dr. ${prescription.doctor_name}`} />
            <DetailItem label="Date" value={prescription.prescription_date} />
            <DetailItem label="Valid Until" value={prescription.valid_until || 'N/A'} />
          </div>
          {prescription.notes && <div style={{ marginTop: 16, padding: '0 16px' }}><strong>Notes:</strong><p>{prescription.notes}</p></div>}
        </div>

        <div className="card">
          <div className="card-header"><h3>Medications</h3></div>
          {(!prescription.medications || prescription.medications.length === 0) ? (
            <p style={{ color: '#999', padding: 20 }}>No medications listed</p>
          ) : (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Medication</th>
                    <th>Dosage</th>
                    <th>Frequency</th>
                    <th>Route</th>
                    <th>Duration</th>
                    <th>Instructions</th>
                  </tr>
                </thead>
                <tbody>
                  {prescription.medications.map((m, i) => (
                    <tr key={i}>
                      <td><strong>{m.medication_name}</strong></td>
                      <td>{m.dosage}</td>
                      <td>{m.frequency}</td>
                      <td>{m.route || 'Oral'}</td>
                      <td>{m.duration || '-'}</td>
                      <td>{m.instructions || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default PrescriptionDetail;
