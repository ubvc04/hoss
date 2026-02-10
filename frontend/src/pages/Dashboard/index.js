import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { dashboardAPI } from '../../api/axios';
import Topbar from '../../components/Layout/Topbar';
import { Loading, StatCard, Badge } from '../../components/Common';
import { FiUsers, FiCalendar, FiFileText, FiDollarSign, FiActivity, FiClipboard, FiUserCheck, FiAlertCircle } from 'react-icons/fi';
import { Link, useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await dashboardAPI.get();
        setData(res.data);
      } catch {}
      setLoading(false);
    };
    fetch();
  }, []);

  if (loading) return <><Topbar title="Dashboard" /><div className="page-content"><Loading /></div></>;

  const stats = data?.stats || {};

  return (
    <>
      <Topbar title={`Welcome, ${user.first_name || user.username}`} />
      <div className="page-content">
        {/* ADMIN DASHBOARD */}
        {user.role === 'Admin' && (
          <>
            <div className="stats-grid">
              <StatCard icon={<FiUsers />} color="blue" value={stats.total_patients} label="Total Patients" />
              <StatCard icon={<FiUserCheck />} color="green" value={stats.total_doctors} label="Active Doctors" />
              <StatCard icon={<FiClipboard />} color="orange" value={stats.active_visits} label="Active Visits" />
              <StatCard icon={<FiCalendar />} color="purple" value={stats.today_appointments} label="Today's Appointments" />
              <StatCard icon={<FiAlertCircle />} color="red" value={stats.pending_appointments} label="Pending Requests" />
              <StatCard icon={<FiDollarSign />} color="green" value={`₹${(stats.total_revenue || 0).toLocaleString()}`} label="Total Revenue" />
            </div>

            {/* All Patients Table */}
            <div className="card" style={{ marginBottom: 20 }}>
              <div className="card-header">
                <h3>All Patients ({(data?.all_patients || []).length})</h3>
                <Link to="/signup" className="btn btn-primary btn-sm">+ Create Patient Account</Link>
              </div>
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>MRN</th>
                      <th>Name</th>
                      <th>Gender</th>
                      <th>DOB</th>
                      <th>Phone</th>
                      <th>Email</th>
                      <th>Username</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data?.all_patients || []).length === 0 ? (
                      <tr><td colSpan={8} style={{ textAlign: 'center', color: '#999', padding: 30 }}>No patients registered yet</td></tr>
                    ) : (
                      (data?.all_patients || []).map(p => (
                        <tr key={p.id}>
                          <td><strong>{p.mrn}</strong></td>
                          <td>{p.first_name} {p.last_name}</td>
                          <td>{p.gender}</td>
                          <td>{p.date_of_birth}</td>
                          <td>{p.phone || '-'}</td>
                          <td>{p.email || '-'}</td>
                          <td>{p.username || '-'}</td>
                          <td>
                            <button className="btn btn-outline btn-sm" onClick={() => navigate(`/patients/${p.id}`)}>
                              View / Add Records
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="card">
              <div className="card-header"><h3>Recent Audit Activity</h3><Link to="/audit-logs" className="btn btn-outline btn-sm">View All</Link></div>
              <div className="table-wrapper">
                <table>
                  <thead><tr><th>User</th><th>Action</th><th>Resource</th><th>Time</th></tr></thead>
                  <tbody>
                    {(data?.recent_audit_logs || []).map(log => (
                      <tr key={log.id}>
                        <td>{log.username}</td>
                        <td>{log.action}</td>
                        <td>{log.resource_type} {log.resource_id && `#${log.resource_id}`}</td>
                        <td>{new Date(log.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {/* DOCTOR DASHBOARD */}
        {user.role === 'Doctor' && (
          <>
            <div className="stats-grid">
              <StatCard icon={<FiUsers />} color="blue" value={stats.my_patients} label="My Patients" />
              <StatCard icon={<FiClipboard />} color="orange" value={stats.active_visits} label="Active Visits" />
              <StatCard icon={<FiCalendar />} color="green" value={stats.today_appointments} label="Today's Appointments" />
            </div>
            <div className="card">
              <div className="card-header"><h3>Upcoming Appointments</h3><Link to="/appointments" className="btn btn-outline btn-sm">View All</Link></div>
              <div className="table-wrapper">
                <table>
                  <thead><tr><th>Patient</th><th>MRN</th><th>Date</th><th>Time</th><th>Status</th></tr></thead>
                  <tbody>
                    {(data?.upcoming_appointments || []).map(a => (
                      <tr key={a.id}>
                        <td>{a.patient_name}</td>
                        <td>{a.mrn}</td>
                        <td>{a.appointment_date}</td>
                        <td>{a.appointment_time}</td>
                        <td><Badge status={a.status} /></td>
                      </tr>
                    ))}
                    {(!data?.upcoming_appointments || data.upcoming_appointments.length === 0) && (
                      <tr><td colSpan={5} style={{ textAlign: 'center', color: '#999' }}>No upcoming appointments</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {/* STAFF DASHBOARD */}
        {user.role === 'Staff' && (
          <>
            <div className="stats-grid">
              <StatCard icon={<FiUsers />} color="blue" value={stats.total_patients} label="Total Patients" />
              <StatCard icon={<FiCalendar />} color="green" value={stats.today_appointments} label="Today's Appointments" />
              <StatCard icon={<FiAlertCircle />} color="orange" value={stats.pending_appointments} label="Pending Requests" />
              <StatCard icon={<FiClipboard />} color="purple" value={stats.active_visits} label="Active Visits" />
              <StatCard icon={<FiDollarSign />} color="red" value={stats.pending_invoices} label="Pending Invoices" />
              <StatCard icon={<FiFileText />} color="blue" value={stats.pending_reports} label="Pending Reports" />
            </div>
            <div className="card">
              <div className="card-header"><h3>Recently Registered Patients</h3><Link to="/patients/new" className="btn btn-primary btn-sm">+ Register Patient</Link></div>
              <div className="table-wrapper">
                <table>
                  <thead><tr><th>MRN</th><th>Name</th><th>Gender</th><th>Phone</th><th>Registered</th></tr></thead>
                  <tbody>
                    {(data?.recent_patients || []).map(p => (
                      <tr key={p.id}>
                        <td><Link to={`/patients/${p.id}`}>{p.mrn}</Link></td>
                        <td>{p.first_name} {p.last_name}</td>
                        <td>{p.gender}</td>
                        <td>{p.phone}</td>
                        <td>{p.registration_date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {/* PATIENT DASHBOARD */}
        {user.role === 'Patient' && (
          <>
            <div className="stats-grid">
              <StatCard icon={<FiClipboard />} color="blue" value={stats.total_visits} label="Total Visits" />
              <StatCard icon={<FiCalendar />} color="green" value={stats.upcoming_appointments} label="Upcoming Appointments" />
              <StatCard icon={<FiFileText />} color="orange" value={stats.total_reports} label="Reports" />
              <StatCard icon={<FiActivity />} color="purple" value={stats.active_prescriptions} label="Active Prescriptions" />
              <StatCard icon={<FiDollarSign />} color="red" value={stats.pending_bills} label="Pending Bills" />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
              <div className="card">
                <div className="card-header"><h3>Upcoming Appointments</h3><Link to="/appointments" className="btn btn-outline btn-sm">View All</Link></div>
                {(data?.upcoming_appointments || []).length === 0 ? (
                  <p style={{ color: '#999', fontSize: 13 }}>No upcoming appointments</p>
                ) : (
                  data.upcoming_appointments.map(a => (
                    <div key={a.id} style={{ padding: '10px 0', borderBottom: '1px solid #f0f0f0', fontSize: 13 }}>
                      <div style={{ fontWeight: 500 }}>{a.appointment_date} at {a.appointment_time}</div>
                      <div style={{ color: '#666' }}>{a.doctor_name} — {a.department_name}</div>
                      <Badge status={a.status} />
                    </div>
                  ))
                )}
              </div>

              <div className="card">
                <div className="card-header"><h3>Recent Reports</h3><Link to="/reports" className="btn btn-outline btn-sm">View All</Link></div>
                {(data?.recent_reports || []).length === 0 ? (
                  <p style={{ color: '#999', fontSize: 13 }}>No reports available</p>
                ) : (
                  data.recent_reports.map(r => (
                    <div key={r.id} style={{ padding: '10px 0', borderBottom: '1px solid #f0f0f0', fontSize: 13 }}>
                      <div style={{ fontWeight: 500 }}>{r.title}</div>
                      <div style={{ color: '#666' }}>{r.report_type} — {r.report_date}</div>
                      <Badge status={r.verification_status} />
                    </div>
                  ))
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
};

export default Dashboard;
