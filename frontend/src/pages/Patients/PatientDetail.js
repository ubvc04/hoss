import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { patientsAPI, visitsAPI, prescriptionsAPI, reportsAPI, billingAPI, appointmentsAPI } from '../../api/axios';
import Topbar from '../../components/Layout/Topbar';
import { Loading, DetailItem, Badge, EmptyState } from '../../components/Common';

const PatientDetail = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('overview');
  const [tabData, setTabData] = useState({});

  const patientId = user.role === 'Patient' ? user.patient_id : parseInt(id);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await patientsAPI.get(patientId);
        setPatient(res.data.patient);
      } catch {}
      setLoading(false);
    };
    fetch();
  }, [patientId]);

  useEffect(() => {
    if (!patientId) return;
    const fetchTab = async () => {
      try {
        if (tab === 'visits' && !tabData.visits) {
          const res = await visitsAPI.list({ patient_id: patientId });
          setTabData(prev => ({ ...prev, visits: res.data.visits }));
        }
        if (tab === 'prescriptions' && !tabData.prescriptions) {
          const res = await prescriptionsAPI.list({ patient_id: patientId });
          setTabData(prev => ({ ...prev, prescriptions: res.data.prescriptions }));
        }
        if (tab === 'reports' && !tabData.reports) {
          const res = await reportsAPI.list({ patient_id: patientId });
          setTabData(prev => ({ ...prev, reports: res.data.reports }));
        }
        if (tab === 'billing' && !tabData.invoices) {
          const res = await billingAPI.list({ patient_id: patientId });
          setTabData(prev => ({ ...prev, invoices: res.data.invoices }));
        }
        if (tab === 'appointments' && !tabData.appointments) {
          const res = await appointmentsAPI.list({ patient_id: patientId });
          setTabData(prev => ({ ...prev, appointments: res.data.appointments }));
        }
      } catch {}
    };
    fetchTab();
  }, [tab, patientId, tabData]);

  if (loading) return <><Topbar title="Patient Details" /><div className="page-content"><Loading /></div></>;
  if (!patient) return <><Topbar title="Patient Details" /><div className="page-content"><EmptyState message="Patient not found" /></div></>;

  const tabs = ['overview', 'visits', 'prescriptions', 'reports', 'billing', 'appointments'];
  const canManage = ['Admin', 'Staff', 'Doctor'].includes(user.role);

  return (
    <>
      <Topbar title={`${patient.first_name} ${patient.last_name} — ${patient.mrn}`} />
      <div className="page-content">
        <div className="tabs">
          {tabs.map(t => (
            <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {/* OVERVIEW */}
        {tab === 'overview' && (
          <div className="card">
            <div className="card-header"><h3>Patient Information</h3></div>
            <div className="detail-grid">
              <DetailItem label="MRN" value={patient.mrn} />
              <DetailItem label="Full Name" value={`${patient.first_name} ${patient.last_name}`} />
              <DetailItem label="Date of Birth" value={patient.date_of_birth} />
              <DetailItem label="Gender" value={patient.gender} />
              <DetailItem label="Blood Group" value={patient.blood_group} />
              <DetailItem label="Marital Status" value={patient.marital_status} />
              <DetailItem label="Phone" value={patient.phone} />
              <DetailItem label="Email" value={patient.email} />
              <DetailItem label="Address" value={[patient.address_line1, patient.address_line2, patient.city, patient.state, patient.postal_code].filter(Boolean).join(', ')} />
              <DetailItem label="Country" value={patient.country} />
              <DetailItem label="National ID" value={patient.national_id} />
              <DetailItem label="Hospital ID" value={patient.hospital_id} />
              <DetailItem label="Registration Date" value={patient.registration_date} />
            </div>

            <h3 style={{ marginTop: 24, marginBottom: 12, fontSize: 15 }}>Emergency Contact</h3>
            <div className="detail-grid">
              <DetailItem label="Name" value={patient.emergency_contact_name} />
              <DetailItem label="Phone" value={patient.emergency_contact_phone} />
              <DetailItem label="Relation" value={patient.emergency_contact_relation} />
            </div>

            {patient.insurance && patient.insurance.length > 0 && (
              <>
                <h3 style={{ marginTop: 24, marginBottom: 12, fontSize: 15 }}>Insurance</h3>
                {patient.insurance.map(ins => (
                  <div key={ins.id} className="detail-grid" style={{ marginBottom: 12 }}>
                    <DetailItem label="Provider" value={ins.provider_name} />
                    <DetailItem label="Policy #" value={ins.policy_number} />
                    <DetailItem label="Plan Type" value={ins.plan_type} />
                    <DetailItem label="Coverage" value={`${ins.coverage_start} to ${ins.coverage_end}`} />
                    <DetailItem label="Max Coverage" value={ins.max_coverage_amount ? `₹${ins.max_coverage_amount.toLocaleString()}` : '—'} />
                  </div>
                ))}
              </>
            )}
          </div>
        )}

        {/* VISITS */}
        {tab === 'visits' && (
          <div className="card">
            <div className="card-header">
              <h3>Visits & Encounters</h3>
              {canManage && <button className="btn btn-primary btn-sm" onClick={() => navigate(`/visits?patient_id=${patientId}`)}>+ New Visit</button>}
            </div>
            {!tabData.visits ? <Loading /> : tabData.visits.length === 0 ? <EmptyState message="No visits recorded" /> : (
              <div className="table-wrapper">
                <table>
                  <thead><tr><th>ID</th><th>Type</th><th>Status</th><th>Date</th><th>Doctor</th><th>Department</th><th>Chief Complaint</th><th>Ward/Bed</th></tr></thead>
                  <tbody>
                    {tabData.visits.map(v => (
                      <tr key={v.id}>
                        <td>#{v.id}</td>
                        <td><Badge status={v.visit_type} /></td>
                        <td><Badge status={v.status} /></td>
                        <td>{v.admission_date?.split(' ')[0]}</td>
                        <td>{v.doctor_name || '—'}</td>
                        <td>{v.department_name || '—'}</td>
                        <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{v.chief_complaint || '—'}</td>
                        <td>{v.ward ? `${v.ward} / ${v.bed_number || '—'}` : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* PRESCRIPTIONS */}
        {tab === 'prescriptions' && (
          <div className="card">
            <div className="card-header">
              <h3>Prescriptions</h3>
              {canManage && <button className="btn btn-primary btn-sm" onClick={() => navigate(`/prescriptions?patient_id=${patientId}`)}>+ New Prescription</button>}
            </div>
            {!tabData.prescriptions ? <Loading /> : tabData.prescriptions.length === 0 ? <EmptyState message="No prescriptions" /> : (
              <div className="table-wrapper">
                <table>
                  <thead><tr><th>ID</th><th>Date</th><th>Doctor</th><th>Status</th><th>Actions</th></tr></thead>
                  <tbody>
                    {tabData.prescriptions.map(p => (
                      <tr key={p.id}>
                        <td>#{p.id}</td>
                        <td>{p.prescription_date}</td>
                        <td>{p.doctor_name}</td>
                        <td><Badge status={p.status} /></td>
                        <td><Link to={`/prescriptions/${p.id}`} className="btn btn-outline btn-sm">View</Link></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* REPORTS */}
        {tab === 'reports' && (
          <div className="card">
            <div className="card-header">
              <h3>Reports & Documents</h3>
              {canManage && <button className="btn btn-primary btn-sm" onClick={() => navigate(`/reports?patient_id=${patientId}`)}>+ Upload Report</button>}
            </div>
            {!tabData.reports ? <Loading /> : tabData.reports.length === 0 ? <EmptyState message="No reports" /> : (
              <div className="table-wrapper">
                <table>
                  <thead><tr><th>Title</th><th>Type</th><th>Date</th><th>Status</th><th>Actions</th></tr></thead>
                  <tbody>
                    {tabData.reports.map(r => (
                      <tr key={r.id}>
                        <td><strong>{r.title}</strong></td>
                        <td>{r.report_type}</td>
                        <td>{r.report_date}</td>
                        <td><Badge status={r.verification_status} /></td>
                        <td><Link to={`/reports/${r.id}`} className="btn btn-outline btn-sm">View</Link></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* BILLING */}
        {tab === 'billing' && (
          <div className="card">
            <div className="card-header">
              <h3>Invoices & Billing</h3>
              {['Admin', 'Staff'].includes(user.role) && <button className="btn btn-primary btn-sm" onClick={() => navigate(`/billing?patient_id=${patientId}`)}>+ New Invoice</button>}
            </div>
            {!tabData.invoices ? <Loading /> : tabData.invoices.length === 0 ? <EmptyState message="No invoices" /> : (
              <div className="table-wrapper">
                <table>
                  <thead><tr><th>Invoice #</th><th>Date</th><th>Total</th><th>Paid</th><th>Status</th><th>Actions</th></tr></thead>
                  <tbody>
                    {tabData.invoices.map(inv => (
                      <tr key={inv.id}>
                        <td><strong>{inv.invoice_number}</strong></td>
                        <td>{inv.invoice_date}</td>
                        <td>₹{(inv.total_amount || 0).toLocaleString()}</td>
                        <td>₹{(inv.paid_amount || 0).toLocaleString()}</td>
                        <td><Badge status={inv.payment_status} /></td>                        <td><Link to={`/billing/${inv.id}`} className="btn btn-outline btn-sm">View</Link></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* APPOINTMENTS */}
        {tab === 'appointments' && (
          <div className="card">
            <div className="card-header">
              <h3>Appointments</h3>
              {canManage && <button className="btn btn-primary btn-sm" onClick={() => navigate(`/appointments?patient_id=${patientId}`)}>+ Book Appointment</button>}
            </div>
            {!tabData.appointments ? <Loading /> : tabData.appointments.length === 0 ? <EmptyState message="No appointments" /> : (
              <div className="table-wrapper">
                <table>
                  <thead><tr><th>Date</th><th>Time</th><th>Doctor</th><th>Department</th><th>Type</th><th>Status</th></tr></thead>
                  <tbody>
                    {tabData.appointments.map(a => (
                      <tr key={a.id}>
                        <td>{a.appointment_date}</td>
                        <td>{a.appointment_time}</td>
                        <td>{a.doctor_name || '—'}</td>
                        <td>{a.department_name || '—'}</td>
                        <td><Badge status={a.visit_type} /></td>
                        <td><Badge status={a.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
};

export default PatientDetail;
