import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { visitsAPI, clinicalAPI } from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import Topbar from '../../components/Layout/Topbar';
import { Loading, ErrorMessage, Badge, DetailItem, Modal } from '../../components/Common';

const VisitDetail = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [visit, setVisit] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('overview');
  const [vitals, setVitals] = useState([]);
  const [notes, setNotes] = useState([]);
  const [showDischarge, setShowDischarge] = useState(false);
  const [dischargeForm, setDischargeForm] = useState({ discharge_date: new Date().toISOString().split('T')[0], discharge_summary: '' });
  const [showAddNote, setShowAddNote] = useState(false);
  const [noteForm, setNoteForm] = useState({ note_type: 'Progress Note', content: '' });
  const [showAddVitals, setShowAddVitals] = useState(false);
  const [vitalsForm, setVitalsForm] = useState({ temperature: '', blood_pressure_systolic: '', blood_pressure_diastolic: '', heart_rate: '', respiratory_rate: '', oxygen_saturation: '', weight: '', height: '' });
  const [saving, setSaving] = useState(false);

  const fetchVisit = async () => {
    setLoading(true);
    try {
      const res = await visitsAPI.get(id);
      setVisit(res.data);
    } catch { setVisit(null); }
    setLoading(false);
  };

  useEffect(() => { fetchVisit(); }, [id]);

  const fetchTabData = async (t) => {
    try {
      if (t === 'vitals') { const r = await clinicalAPI.vitals({ visit_id: id }); setVitals(r.data.vitals || []); }
      else if (t === 'notes') { const r = await clinicalAPI.notes({ visit_id: id }); setNotes(r.data.clinical_notes || []); }
    } catch {}
  };

  useEffect(() => { if (tab !== 'overview') fetchTabData(tab); }, [tab]);

  const handleDischarge = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await visitsAPI.update(id, { ...dischargeForm, status: 'Discharged' });
      setShowDischarge(false);
      fetchVisit();
    } catch (err) { setError(err.response?.data?.error || 'Failed'); }
    setSaving(false);
  };

  const handleAddNote = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await clinicalAPI.createNote({ visit_id: parseInt(id), patient_id: visit.patient_id, ...noteForm });
      setShowAddNote(false);
      setNoteForm({ note_type: 'Progress Note', content: '' });
      fetchTabData('notes');
    } catch (err) { setError(err.response?.data?.error || 'Failed'); }
    setSaving(false);
  };

  const handleAddVitals = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = { visit_id: parseInt(id), patient_id: visit.patient_id };
      Object.entries(vitalsForm).forEach(([k, v]) => { if (v) payload[k] = parseFloat(v); });
      await clinicalAPI.createVitals(payload);
      setShowAddVitals(false);
      setVitalsForm({ temperature: '', blood_pressure_systolic: '', blood_pressure_diastolic: '', heart_rate: '', respiratory_rate: '', oxygen_saturation: '', weight: '', height: '' });
      fetchTabData('vitals');
    } catch (err) { setError(err.response?.data?.error || 'Failed'); }
    setSaving(false);
  };

  const canEdit = ['Admin', 'Staff', 'Doctor'].includes(user.role);

  if (loading) return <><Topbar title="Visit Details" /><div className="page-content"><Loading /></div></>;
  if (error) return <><Topbar title="Visit Details" /><div className="page-content"><ErrorMessage message={error} onRetry={fetchVisit} /></div></>;
  if (!visit) return null;

  return (
    <>
      <Topbar title={`Visit #${visit.id}`} />
      <div className="page-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
          <button className="btn btn-outline" onClick={() => navigate('/visits')}>← Back</button>
          {canEdit && visit.status === 'Active' && <button className="btn btn-primary" onClick={() => setShowDischarge(true)}>Discharge Patient</button>}
        </div>

        <div className="tab-nav">
          {['overview', 'vitals', 'notes'].map(t => (
            <button key={t} className={`tab-btn ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {tab === 'overview' && (
          <div className="card">
            <div className="card-header"><h3>Visit Information</h3><Badge status={visit.status === 'Active' ? 'info' : 'success'} text={visit.status} /></div>
            <div className="detail-grid">
              <DetailItem label="Patient" value={visit.patient_name} />
              <DetailItem label="Doctor" value={`Dr. ${visit.doctor_name}`} />
              <DetailItem label="Department" value={visit.department_name || '-'} />
              <DetailItem label="Visit Type" value={visit.visit_type} />
              <DetailItem label="Admission" value={visit.admission_date} />
              <DetailItem label="Discharge" value={visit.discharge_date || '-'} />
              <DetailItem label="Room" value={visit.room_number || '-'} />
              <DetailItem label="Bed" value={visit.bed_number || '-'} />
            </div>
            {visit.chief_complaint && <div style={{ marginTop: 16 }}><strong>Chief Complaint:</strong><p>{visit.chief_complaint}</p></div>}
            {visit.discharge_summary && <div style={{ marginTop: 16 }}><strong>Discharge Summary:</strong><p>{visit.discharge_summary}</p></div>}
          </div>
        )}

        {tab === 'vitals' && (
          <div className="card">
            <div className="card-header"><h3>Vitals</h3>{canEdit && <button className="btn btn-primary btn-sm" onClick={() => setShowAddVitals(true)}>+ Record Vitals</button>}</div>
            {vitals.length === 0 ? <p style={{ color: '#999', padding: 20 }}>No vitals recorded</p> : (
              <table><thead><tr><th>Date</th><th>Temp (°F)</th><th>BP</th><th>HR</th><th>RR</th><th>SpO2</th><th>Weight</th></tr></thead>
                <tbody>{vitals.map(v => <tr key={v.id}><td>{v.recorded_at?.split('T')[0]}</td><td>{v.temperature || '-'}</td><td>{v.blood_pressure_systolic && v.blood_pressure_diastolic ? `${v.blood_pressure_systolic}/${v.blood_pressure_diastolic}` : '-'}</td><td>{v.heart_rate || '-'}</td><td>{v.respiratory_rate || '-'}</td><td>{v.oxygen_saturation ? `${v.oxygen_saturation}%` : '-'}</td><td>{v.weight ? `${v.weight} kg` : '-'}</td></tr>)}</tbody>
              </table>
            )}
          </div>
        )}

        {tab === 'notes' && (
          <div className="card">
            <div className="card-header"><h3>Clinical Notes</h3>{canEdit && <button className="btn btn-primary btn-sm" onClick={() => setShowAddNote(true)}>+ Add Note</button>}</div>
            {notes.length === 0 ? <p style={{ color: '#999', padding: 20 }}>No notes</p> : notes.map(n => (
              <div key={n.id} style={{ borderBottom: '1px solid #eee', padding: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}><strong>{n.note_type}</strong><span style={{ color: '#999', fontSize: 13 }}>by {n.author_name} on {n.created_at?.split('T')[0]}</span></div>
                <p style={{ whiteSpace: 'pre-wrap' }}>{n.content}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal show={showDischarge} title="Discharge Patient" onClose={() => setShowDischarge(false)}>
        <form onSubmit={handleDischarge}>
          <div className="form-group"><label className="required">Discharge Date</label><input type="date" className="form-control" value={dischargeForm.discharge_date} onChange={e => setDischargeForm(p => ({ ...p, discharge_date: e.target.value }))} required /></div>
          <div className="form-group"><label>Discharge Summary</label><textarea className="form-control" rows={4} value={dischargeForm.discharge_summary} onChange={e => setDischargeForm(p => ({ ...p, discharge_summary: e.target.value }))} /></div>
          <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>{saving ? 'Discharging...' : 'Discharge'}</button>
        </form>
      </Modal>

      <Modal show={showAddNote} title="Add Clinical Note" onClose={() => setShowAddNote(false)}>
        <form onSubmit={handleAddNote}>
          <div className="form-group">
            <label>Note Type</label>
            <select className="form-control" value={noteForm.note_type} onChange={e => setNoteForm(p => ({ ...p, note_type: e.target.value }))}>
              {['Progress Note', 'Admission Note', 'Discharge Note', 'Consultation Note', 'Procedure Note', 'Operative Note'].map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div className="form-group"><label className="required">Content</label><textarea className="form-control" rows={6} value={noteForm.content} onChange={e => setNoteForm(p => ({ ...p, content: e.target.value }))} required /></div>
          <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>{saving ? 'Saving...' : 'Add Note'}</button>
        </form>
      </Modal>

      <Modal show={showAddVitals} title="Record Vitals" onClose={() => setShowAddVitals(false)}>
        <form onSubmit={handleAddVitals}>
          <div className="form-row">
            <div className="form-group"><label>Temperature (°F)</label><input type="number" step="0.1" className="form-control" value={vitalsForm.temperature} onChange={e => setVitalsForm(p => ({ ...p, temperature: e.target.value }))} /></div>
            <div className="form-group"><label>Heart Rate</label><input type="number" className="form-control" value={vitalsForm.heart_rate} onChange={e => setVitalsForm(p => ({ ...p, heart_rate: e.target.value }))} /></div>
          </div>
          <div className="form-row">
            <div className="form-group"><label>BP Systolic</label><input type="number" className="form-control" value={vitalsForm.blood_pressure_systolic} onChange={e => setVitalsForm(p => ({ ...p, blood_pressure_systolic: e.target.value }))} /></div>
            <div className="form-group"><label>BP Diastolic</label><input type="number" className="form-control" value={vitalsForm.blood_pressure_diastolic} onChange={e => setVitalsForm(p => ({ ...p, blood_pressure_diastolic: e.target.value }))} /></div>
          </div>
          <div className="form-row">
            <div className="form-group"><label>Respiratory Rate</label><input type="number" className="form-control" value={vitalsForm.respiratory_rate} onChange={e => setVitalsForm(p => ({ ...p, respiratory_rate: e.target.value }))} /></div>
            <div className="form-group"><label>SpO2 (%)</label><input type="number" step="0.1" className="form-control" value={vitalsForm.oxygen_saturation} onChange={e => setVitalsForm(p => ({ ...p, oxygen_saturation: e.target.value }))} /></div>
          </div>
          <div className="form-row">
            <div className="form-group"><label>Weight (kg)</label><input type="number" step="0.1" className="form-control" value={vitalsForm.weight} onChange={e => setVitalsForm(p => ({ ...p, weight: e.target.value }))} /></div>
            <div className="form-group"><label>Height (cm)</label><input type="number" step="0.1" className="form-control" value={vitalsForm.height} onChange={e => setVitalsForm(p => ({ ...p, height: e.target.value }))} /></div>
          </div>
          <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>{saving ? 'Saving...' : 'Record Vitals'}</button>
        </form>
      </Modal>
    </>
  );
};

export default VisitDetail;
