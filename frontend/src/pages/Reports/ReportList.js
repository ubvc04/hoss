import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { reportsAPI, patientsAPI } from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import Topbar from '../../components/Layout/Topbar';
import { Loading, EmptyState, ErrorMessage, Badge, Pagination, Modal } from '../../components/Common';

const typeColors = { 'Lab': 'info', 'Scan': 'warning', 'X-Ray': 'secondary', 'MRI': 'warning', 'CT': 'warning', 'Ultrasound': 'info', 'Discharge Summary': 'success', 'Referral Letter': 'secondary', 'Consent Form': 'secondary', 'Other': 'secondary' };
const statusColors = { Pending: 'warning', Verified: 'success', Rejected: 'danger' };

const ReportList = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [typeFilter, setTypeFilter] = useState('');
  const [showUpload, setShowUpload] = useState(false);
  const [uploadForm, setUploadForm] = useState({ title: '', report_type: 'Lab', patient_id: '', ordering_doctor_id: '', visit_id: '', description: '' });
  const [file, setFile] = useState(null);
  const [saving, setSaving] = useState(false);
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);

  const fetchReports = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, per_page: 15 };
      if (typeFilter) params.report_type = typeFilter;
      const res = await reportsAPI.getAll(params);
      setReports(res.data.reports || []);
      setTotal(res.data.total || 0);
    } catch { setReports([]); setTotal(0); }
    setLoading(false);
  }, [page, typeFilter]);

  useEffect(() => { fetchReports(); }, [fetchReports]);

  const openUpload = async () => {
    try {
      const [pRes, dRes] = await Promise.all([patientsAPI.getAll({ per_page: 200 }), patientsAPI.getDoctors()]);
      setPatients(pRes.data.patients || []);
      setDoctors(dRes.data.doctors || []);
    } catch {}
    setShowUpload(true);
  };

  // Auto-open upload form if patient_id is in URL
  useEffect(() => {
    const pid = searchParams.get('patient_id');
    if (pid) {
      setUploadForm(f => ({ ...f, patient_id: pid }));
      openUpload();
      setSearchParams({}, { replace: true });
    }
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const formData = new FormData();
      Object.entries(uploadForm).forEach(([k, v]) => { if (v) formData.append(k, v); });
      if (file) formData.append('files', file);
      await reportsAPI.create(formData);
      setShowUpload(false);
      setUploadForm({ title: '', report_type: 'Lab', patient_id: '', ordering_doctor_id: '', visit_id: '', description: '' });
      setFile(null);
      fetchReports();
    } catch (err) { setError(err.response?.data?.error || 'Failed to upload report'); }
    setSaving(false);
  };

  const canCreate = ['Admin', 'Staff', 'Doctor'].includes(user.role);

  return (
    <>
      <Topbar title="Medical Reports" />
      <div className="page-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <select className="form-control" style={{ width: 200 }} value={typeFilter} onChange={e => { setTypeFilter(e.target.value); setPage(1); }}>
            <option value="">All Types</option>
            {['Lab', 'Scan', 'X-Ray', 'MRI', 'CT', 'Ultrasound', 'Discharge Summary', 'Referral Letter', 'Consent Form', 'Other'].map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          {canCreate && <button className="btn btn-primary" onClick={openUpload}>+ New Report</button>}
        </div>

        {error && <ErrorMessage message={error} onRetry={() => { setError(''); fetchReports(); }} />}
        {loading ? <Loading /> : reports.length === 0 ? <EmptyState message="No reports found" /> : (
          <>
            <div className="table-container">
              <table>
                <thead><tr><th>Title</th><th>Type</th>{user.role !== 'Patient' && <th>Patient</th>}<th>Doctor</th><th>Date</th><th>Status</th><th>Actions</th></tr></thead>
                <tbody>
                  {reports.map(r => (
                    <tr key={r.id}>
                      <td>{r.title}</td>
                      <td><Badge status={typeColors[r.report_type] || 'secondary'} text={r.report_type} /></td>
                      {user.role !== 'Patient' && <td>{r.patient_name}</td>}
                      <td>Dr. {r.doctor_name}</td>
                      <td>{r.report_date}</td>
                      <td><Badge status={statusColors[r.verification_status]} text={r.verification_status} /></td>
                      <td><button className="btn btn-outline btn-sm" onClick={() => navigate(`/reports/${r.id}`)}>View</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={page} total={total} perPage={15} onPageChange={setPage} />
          </>
        )}
      </div>

      <Modal show={showUpload} title="Create Report" onClose={() => setShowUpload(false)}>
        <form onSubmit={handleUpload}>
          <div className="form-group"><label className="required">Title</label><input className="form-control" value={uploadForm.title} onChange={e => setUploadForm(p => ({ ...p, title: e.target.value }))} required /></div>
          <div className="form-row">
            <div className="form-group">
              <label className="required">Patient</label>
              <select className="form-control" value={uploadForm.patient_id} onChange={e => setUploadForm(p => ({ ...p, patient_id: e.target.value }))} required>
                <option value="">Select Patient</option>
                {patients.map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name} ({p.mrn})</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="required">Doctor</label>
              <select className="form-control" value={uploadForm.ordering_doctor_id} onChange={e => setUploadForm(p => ({ ...p, ordering_doctor_id: e.target.value }))} required>
                <option value="">Select Doctor</option>
                {doctors.map(d => <option key={d.id} value={d.id}>Dr. {d.first_name} {d.last_name}</option>)}
              </select>
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Type</label>
              <select className="form-control" value={uploadForm.report_type} onChange={e => setUploadForm(p => ({ ...p, report_type: e.target.value }))}>
                {['Lab', 'Scan', 'X-Ray', 'MRI', 'CT', 'Ultrasound', 'Discharge Summary', 'Referral Letter', 'Consent Form', 'Other'].map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="form-group"><label>Visit ID</label><input type="number" className="form-control" value={uploadForm.visit_id} onChange={e => setUploadForm(p => ({ ...p, visit_id: e.target.value }))} /></div>
          </div>
          <div className="form-group"><label>Description / Notes</label><textarea className="form-control" rows={4} value={uploadForm.description} onChange={e => setUploadForm(p => ({ ...p, description: e.target.value }))} /></div>
          <div className="form-group"><label>Attach File</label><input type="file" className="form-control" onChange={e => setFile(e.target.files[0])} /></div>
          <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>{saving ? 'Creating...' : 'Create Report'}</button>
        </form>
      </Modal>
    </>
  );
};

export default ReportList;
