import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { visitsAPI, patientsAPI } from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import Topbar from '../../components/Layout/Topbar';
import { Loading, EmptyState, ErrorMessage, Badge, Pagination, Modal } from '../../components/Common';

const statusColors = { Active: 'info', Discharged: 'success', Transferred: 'warning' };

const VisitsPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [visits, setVisits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [showCreate, setShowCreate] = useState(false);
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [form, setForm] = useState({ patient_id: '', doctor_id: '', department_id: '', visit_type: 'OPD', admission_date: new Date().toISOString().split('T')[0], chief_complaint: '', room_number: '', bed_number: '' });
  const [saving, setSaving] = useState(false);

  const fetchVisits = useCallback(async () => {
    setLoading(true);
    try {
      const res = await visitsAPI.getAll({ page, per_page: 15 });
      setVisits(res.data.visits || []);
      setTotal(res.data.total || 0);
    } catch { setVisits([]); setTotal(0); }
    setLoading(false);
  }, [page]);

  useEffect(() => { fetchVisits(); }, [fetchVisits]);

  // Auto-open create modal if patient_id is in URL
  useEffect(() => {
    const pid = searchParams.get('patient_id');
    if (pid) {
      setForm(f => ({ ...f, patient_id: pid }));
      openCreate();
      setSearchParams({}, { replace: true });
    }
  }, []);

  const openCreate = async () => {
    try {
      const [pRes, dRes, depRes] = await Promise.all([
        patientsAPI.getAll({ per_page: 200 }),
        patientsAPI.getDoctors(),
        patientsAPI.getDepartments()
      ]);
      setPatients(pRes.data.patients || []);
      setDoctors(dRes.data.doctors || []);
      setDepartments(depRes.data.departments || []);
    } catch {}
    setShowCreate(true);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await visitsAPI.create(form);
      setShowCreate(false);
      setForm({ patient_id: '', doctor_id: '', department_id: '', visit_type: 'OPD', admission_date: new Date().toISOString().split('T')[0], chief_complaint: '', room_number: '', bed_number: '' });
      fetchVisits();
    } catch (err) { setError(err.response?.data?.error || 'Failed to create visit'); }
    setSaving(false);
  };

  const canCreate = ['Admin', 'Staff', 'Doctor'].includes(user.role);

  return (
    <>
      <Topbar title="Visits" />
      <div className="page-content">
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 20 }}>
          {canCreate && <button className="btn btn-primary" onClick={openCreate}>+ New Visit</button>}
        </div>

        {error && <ErrorMessage message={error} onRetry={() => { setError(''); fetchVisits(); }} />}
        {loading ? <Loading /> : visits.length === 0 ? <EmptyState message="No visits found" /> : (
          <>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Visit ID</th>
                    {user.role !== 'Patient' && <th>Patient</th>}
                    <th>Doctor</th>
                    <th>Department</th>
                    <th>Type</th>
                    <th>Admission</th>
                    <th>Discharge</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {visits.map(v => (
                    <tr key={v.id}>
                      <td>#{v.id}</td>
                      {user.role !== 'Patient' && <td>{v.patient_name}</td>}
                      <td>Dr. {v.doctor_name}</td>
                      <td>{v.department_name || '-'}</td>
                      <td>{v.visit_type}</td>
                      <td>{v.admission_date}</td>
                      <td>{v.discharge_date || '-'}</td>
                      <td><Badge status={statusColors[v.status]} text={v.status} /></td>
                      <td>
                        <button className="btn btn-outline btn-sm" onClick={() => navigate(`/visits/${v.id}`)}>View</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={page} total={total} perPage={15} onPageChange={setPage} />
          </>
        )}
      </div>

      <Modal show={showCreate} title="Create New Visit" onClose={() => setShowCreate(false)}>
        <form onSubmit={handleCreate}>
          <div className="form-group">
            <label className="required">Patient</label>
            <select className="form-control" value={form.patient_id} onChange={e => setForm(p => ({ ...p, patient_id: e.target.value }))} required>
              <option value="">Select Patient</option>
              {patients.map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name} ({p.mrn})</option>)}
            </select>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="required">Doctor</label>
              <select className="form-control" value={form.doctor_id} onChange={e => setForm(p => ({ ...p, doctor_id: e.target.value }))} required>
                <option value="">Select Doctor</option>
                {doctors.map(d => <option key={d.id} value={d.id}>Dr. {d.first_name} {d.last_name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Department</label>
              <select className="form-control" value={form.department_id} onChange={e => setForm(p => ({ ...p, department_id: e.target.value }))}>
                <option value="">Select</option>
                {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Visit Type</label>
              <select className="form-control" value={form.visit_type} onChange={e => setForm(p => ({ ...p, visit_type: e.target.value }))}>
                {['OPD', 'IPD', 'Emergency'].map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="required">Admission Date</label>
              <input type="date" className="form-control" value={form.admission_date} onChange={e => setForm(p => ({ ...p, admission_date: e.target.value }))} required />
            </div>
          </div>
          <div className="form-group">
            <label>Chief Complaint</label>
            <textarea className="form-control" rows={3} value={form.chief_complaint} onChange={e => setForm(p => ({ ...p, chief_complaint: e.target.value }))} />
          </div>
          <div className="form-row">
            <div className="form-group"><label>Room Number</label><input className="form-control" value={form.room_number} onChange={e => setForm(p => ({ ...p, room_number: e.target.value }))} /></div>
            <div className="form-group"><label>Bed Number</label><input className="form-control" value={form.bed_number} onChange={e => setForm(p => ({ ...p, bed_number: e.target.value }))} /></div>
          </div>
          <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>{saving ? 'Creating...' : 'Create Visit'}</button>
        </form>
      </Modal>
    </>
  );
};

export default VisitsPage;
