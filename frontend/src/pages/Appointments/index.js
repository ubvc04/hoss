import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { appointmentsAPI, patientsAPI } from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import Topbar from '../../components/Layout/Topbar';
import { Loading, EmptyState, ErrorMessage, Badge, Pagination, Modal } from '../../components/Common';

const statusColors = { Requested: 'warning', Confirmed: 'info', Completed: 'success', Cancelled: 'danger', 'No-Show': 'danger' };

const AppointmentsPage = () => {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [showManage, setShowManage] = useState(null);
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [form, setForm] = useState({ patient_id: '', doctor_id: '', appointment_date: '', appointment_time: '', appointment_type: 'Consultation', reason: '' });
  const [manageForm, setManageForm] = useState({ status: '', notes: '', new_date: '', new_time: '' });
  const [saving, setSaving] = useState(false);

  const fetchAppointments = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, per_page: 15 };
      if (statusFilter) params.status = statusFilter;
      const res = await appointmentsAPI.getAll(params);
      setAppointments(res.data.appointments || []);
      setTotal(res.data.total || 0);
    } catch { setAppointments([]); setTotal(0); }
    setLoading(false);
  }, [page, statusFilter]);

  useEffect(() => { fetchAppointments(); }, [fetchAppointments]);

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
      const [pRes, dRes] = await Promise.all([patientsAPI.getAll({ per_page: 200 }), patientsAPI.getDoctors()]);
      setPatients(pRes.data.patients || []);
      setDoctors(dRes.data.doctors || []);
    } catch {}
    setShowCreate(true);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await appointmentsAPI.create(form);
      setShowCreate(false);
      setForm({ patient_id: '', doctor_id: '', appointment_date: '', appointment_time: '', appointment_type: 'Consultation', reason: '' });
      fetchAppointments();
    } catch (err) { setError(err.response?.data?.error || 'Failed to create appointment'); }
    setSaving(false);
  };

  const openManage = (apt) => {
    setManageForm({ status: apt.status, notes: apt.notes || '', new_date: apt.appointment_date, new_time: apt.appointment_time });
    setShowManage(apt);
  };

  const handleManage = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = { status: manageForm.status, notes: manageForm.notes };
      if (manageForm.status === 'Confirmed' && (manageForm.new_date !== showManage.appointment_date || manageForm.new_time !== showManage.appointment_time)) {
        payload.new_date = manageForm.new_date;
        payload.new_time = manageForm.new_time;
      }
      await appointmentsAPI.update(showManage.id, payload);
      setShowManage(null);
      fetchAppointments();
    } catch (err) { setError(err.response?.data?.error || 'Failed to update appointment'); }
    setSaving(false);
  };

  const canCreate = ['Admin', 'Staff', 'Patient'].includes(user.role);
  const canManage = ['Admin', 'Staff', 'Doctor'].includes(user.role);

  return (
    <>
      <Topbar title="Appointments" />
      <div className="page-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <select className="form-control" style={{ width: 200 }} value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }}>
            <option value="">All Statuses</option>
            {['Requested', 'Confirmed', 'Completed', 'Cancelled', 'No-Show'].map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          {canCreate && <button className="btn btn-primary" onClick={openCreate}>+ New Appointment</button>}
        </div>

        {error && <ErrorMessage message={error} onRetry={() => { setError(''); fetchAppointments(); }} />}
        {loading ? <Loading /> : appointments.length === 0 ? <EmptyState message="No appointments found" /> : (
          <>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Date & Time</th>
                    {user.role !== 'Patient' && <th>Patient</th>}
                    {user.role !== 'Doctor' && <th>Doctor</th>}
                    <th>Type</th>
                    <th>Reason</th>
                    <th>Status</th>
                    {canManage && <th>Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {appointments.map(a => (
                    <tr key={a.id}>
                      <td>{a.appointment_date} {a.appointment_time}</td>
                      {user.role !== 'Patient' && <td>{a.patient_name}</td>}
                      {user.role !== 'Doctor' && <td>{a.doctor_name}</td>}
                      <td>{a.appointment_type}</td>
                      <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.reason || '-'}</td>
                      <td><Badge status={statusColors[a.status]} text={a.status} /></td>
                      {canManage && <td><button className="btn btn-outline btn-sm" onClick={() => openManage(a)}>Manage</button></td>}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={page} total={total} perPage={15} onPageChange={setPage} />
          </>
        )}
      </div>

      <Modal show={showCreate} title="New Appointment" onClose={() => setShowCreate(false)}>
        <form onSubmit={handleCreate}>
          {user.role !== 'Patient' && (
            <div className="form-group">
              <label className="required">Patient</label>
              <select className="form-control" value={form.patient_id} onChange={e => setForm(p => ({ ...p, patient_id: e.target.value }))} required>
                <option value="">Select Patient</option>
                {patients.map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name} ({p.mrn})</option>)}
              </select>
            </div>
          )}
          <div className="form-group">
            <label className="required">Doctor</label>
            <select className="form-control" value={form.doctor_id} onChange={e => setForm(p => ({ ...p, doctor_id: e.target.value }))} required>
              <option value="">Select Doctor</option>
              {doctors.map(d => <option key={d.id} value={d.id}>Dr. {d.first_name} {d.last_name} - {d.specialization}</option>)}
            </select>
          </div>
          <div className="form-row">
            <div className="form-group"><label className="required">Date</label><input type="date" className="form-control" value={form.appointment_date} onChange={e => setForm(p => ({ ...p, appointment_date: e.target.value }))} required /></div>
            <div className="form-group"><label className="required">Time</label><input type="time" className="form-control" value={form.appointment_time} onChange={e => setForm(p => ({ ...p, appointment_time: e.target.value }))} required /></div>
          </div>
          <div className="form-group">
            <label>Type</label>
            <select className="form-control" value={form.appointment_type} onChange={e => setForm(p => ({ ...p, appointment_type: e.target.value }))}>
              {['Consultation', 'Follow-up', 'Emergency', 'Surgery', 'Lab Work', 'Imaging'].map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div className="form-group"><label>Reason</label><textarea className="form-control" rows={3} value={form.reason} onChange={e => setForm(p => ({ ...p, reason: e.target.value }))} /></div>
          <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>{saving ? 'Creating...' : 'Create Appointment'}</button>
        </form>
      </Modal>

      <Modal show={!!showManage} title="Manage Appointment" onClose={() => setShowManage(null)}>
        {showManage && (
          <form onSubmit={handleManage}>
            <div className="form-group">
              <label>Status</label>
              <select className="form-control" value={manageForm.status} onChange={e => setManageForm(p => ({ ...p, status: e.target.value }))}>
                {['Requested', 'Confirmed', 'Completed', 'Cancelled', 'No-Show'].map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            {manageForm.status === 'Confirmed' && (
              <div className="form-row">
                <div className="form-group"><label>Reschedule Date</label><input type="date" className="form-control" value={manageForm.new_date} onChange={e => setManageForm(p => ({ ...p, new_date: e.target.value }))} /></div>
                <div className="form-group"><label>Reschedule Time</label><input type="time" className="form-control" value={manageForm.new_time} onChange={e => setManageForm(p => ({ ...p, new_time: e.target.value }))} /></div>
              </div>
            )}
            <div className="form-group"><label>Notes</label><textarea className="form-control" rows={3} value={manageForm.notes} onChange={e => setManageForm(p => ({ ...p, notes: e.target.value }))} /></div>
            <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>{saving ? 'Saving...' : 'Update Appointment'}</button>
          </form>
        )}
      </Modal>
    </>
  );
};

export default AppointmentsPage;
