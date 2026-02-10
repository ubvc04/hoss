import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { prescriptionsAPI, patientsAPI } from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import Topbar from '../../components/Layout/Topbar';
import { Loading, EmptyState, ErrorMessage, Badge, Pagination, Modal } from '../../components/Common';

const statusColors = { Active: 'success', Completed: 'info', Cancelled: 'danger' };

const PrescriptionList = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [prescriptions, setPrescriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [form, setForm] = useState({ patient_id: '', doctor_id: '', diagnosis: '', notes: '', medications: [{ name: '', dosage: '', frequency: '', duration: '', instructions: '' }] });
  const [saving, setSaving] = useState(false);

  const canCreate = ['Admin', 'Staff', 'Doctor'].includes(user.role);

  const fetchPrescriptions = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, per_page: 15 };
      if (statusFilter) params.status = statusFilter;
      const res = await prescriptionsAPI.getAll(params);
      setPrescriptions(res.data.prescriptions || []);
      setTotal(res.data.total || 0);
    } catch { setPrescriptions([]); setTotal(0); }
    setLoading(false);
  }, [page, statusFilter]);

  useEffect(() => { fetchPrescriptions(); }, [fetchPrescriptions]);

  const openCreate = async () => {
    try {
      const [pRes, dRes] = await Promise.all([patientsAPI.getAll({ per_page: 200 }), patientsAPI.getDoctors()]);
      setPatients(pRes.data.patients || []);
      setDoctors(dRes.data.doctors || []);
    } catch {}
    setShowCreate(true);
  };

  // Auto-open create if patient_id in URL
  useEffect(() => {
    const pid = searchParams.get('patient_id');
    if (pid) {
      setForm(f => ({ ...f, patient_id: pid }));
      openCreate();
      setSearchParams({}, { replace: true });
    }
  }, []);

  const addMedication = () => {
    setForm(f => ({ ...f, medications: [...f.medications, { name: '', dosage: '', frequency: '', duration: '', instructions: '' }] }));
  };

  const removeMedication = (idx) => {
    setForm(f => ({ ...f, medications: f.medications.filter((_, i) => i !== idx) }));
  };

  const updateMedication = (idx, field, value) => {
    setForm(f => {
      const meds = [...f.medications];
      meds[idx] = { ...meds[idx], [field]: value };
      return { ...f, medications: meds };
    });
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        patient_id: form.patient_id,
        doctor_id: form.doctor_id,
        notes: form.notes,
        medications: form.medications.map(m => ({
          medication_name: m.name,
          dosage: m.dosage || 'As directed',
          frequency: m.frequency || 'As needed',
          duration: m.duration,
          instructions: m.instructions,
          route: 'Oral',
        })),
      };
      await prescriptionsAPI.create(payload);
      setShowCreate(false);
      setForm({ patient_id: '', doctor_id: '', diagnosis: '', notes: '', medications: [{ name: '', dosage: '', frequency: '', duration: '', instructions: '' }] });
      fetchPrescriptions();
    } catch (err) { setError(err.response?.data?.error || 'Failed to create prescription'); }
    setSaving(false);
  };

  return (
    <>
      <Topbar title="Prescriptions" />
      <div className="page-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <select className="form-control" style={{ width: 200 }} value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }}>
            <option value="">All Statuses</option>
            {['Active', 'Completed', 'Cancelled'].map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          {canCreate && <button className="btn btn-primary" onClick={openCreate}>+ New Prescription</button>}
        </div>

        {error && <ErrorMessage message={error} onRetry={() => { setError(''); fetchPrescriptions(); }} />}
        {loading ? <Loading /> : prescriptions.length === 0 ? <EmptyState message="No prescriptions found" /> : (
          <>
            <div className="table-container">
              <table>
                <thead><tr>{user.role !== 'Patient' && <th>Patient</th>}<th>Doctor</th><th>Date</th><th>Medications</th><th>Status</th><th>Actions</th></tr></thead>
                <tbody>
                  {prescriptions.map(p => (
                    <tr key={p.id}>
                      {user.role !== 'Patient' && <td>{p.patient_name}</td>}
                      <td>Dr. {p.doctor_name}</td>
                      <td>{p.prescription_date}</td>
                      <td>{p.medication_count || 0} item(s)</td>
                      <td><Badge status={statusColors[p.status]} text={p.status} /></td>
                      <td><button className="btn btn-outline btn-sm" onClick={() => navigate(`/prescriptions/${p.id}`)}>View</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={page} total={total} perPage={15} onPageChange={setPage} />
          </>
        )}
      </div>

      <Modal show={showCreate} title="Create Prescription" onClose={() => setShowCreate(false)}>
        <form onSubmit={handleCreate}>
          <div className="form-row">
            <div className="form-group">
              <label className="required">Patient</label>
              <select className="form-control" value={form.patient_id} onChange={e => setForm(p => ({ ...p, patient_id: e.target.value }))} required>
                <option value="">Select Patient</option>
                {patients.map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name} ({p.mrn})</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="required">Doctor</label>
              <select className="form-control" value={form.doctor_id} onChange={e => setForm(p => ({ ...p, doctor_id: e.target.value }))} required>
                <option value="">Select Doctor</option>
                {doctors.map(d => <option key={d.id} value={d.id}>Dr. {d.first_name} {d.last_name}</option>)}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Diagnosis</label>
            <input className="form-control" value={form.diagnosis} onChange={e => setForm(p => ({ ...p, diagnosis: e.target.value }))} placeholder="e.g. Hypertension, Diabetes" />
          </div>

          <h4 style={{ margin: '16px 0 8px', fontSize: 14, fontWeight: 600 }}>Medications</h4>
          {form.medications.map((med, idx) => (
            <div key={idx} style={{ border: '1px solid #e0e0e0', borderRadius: 8, padding: 12, marginBottom: 10, background: '#f9f9f9' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <strong style={{ fontSize: 13 }}>Medication #{idx + 1}</strong>
                {form.medications.length > 1 && <button type="button" className="btn btn-outline btn-sm" style={{ color: '#e74c3c' }} onClick={() => removeMedication(idx)}>Remove</button>}
              </div>
              <div className="form-row">
                <div className="form-group"><label className="required">Medicine Name</label><input className="form-control" value={med.name} onChange={e => updateMedication(idx, 'name', e.target.value)} required placeholder="e.g. Paracetamol 500mg" /></div>
                <div className="form-group"><label>Dosage</label><input className="form-control" value={med.dosage} onChange={e => updateMedication(idx, 'dosage', e.target.value)} placeholder="e.g. 1 tablet" /></div>
              </div>
              <div className="form-row">
                <div className="form-group"><label>Frequency</label><input className="form-control" value={med.frequency} onChange={e => updateMedication(idx, 'frequency', e.target.value)} placeholder="e.g. Twice daily" /></div>
                <div className="form-group"><label>Duration</label><input className="form-control" value={med.duration} onChange={e => updateMedication(idx, 'duration', e.target.value)} placeholder="e.g. 7 days" /></div>
              </div>
              <div className="form-group"><label>Instructions</label><input className="form-control" value={med.instructions} onChange={e => updateMedication(idx, 'instructions', e.target.value)} placeholder="e.g. After meals" /></div>
            </div>
          ))}
          <button type="button" className="btn btn-outline" style={{ marginBottom: 16 }} onClick={addMedication}>+ Add Another Medication</button>

          <div className="form-group">
            <label>Notes</label>
            <textarea className="form-control" rows={3} value={form.notes} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} placeholder="Any additional notes..." />
          </div>

          <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>{saving ? 'Creating...' : 'Create Prescription'}</button>
        </form>
      </Modal>
    </>
  );
};

export default PrescriptionList;
