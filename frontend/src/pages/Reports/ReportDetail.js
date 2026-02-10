import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { reportsAPI } from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import Topbar from '../../components/Layout/Topbar';
import { Loading, ErrorMessage, Badge, DetailItem } from '../../components/Common';

const ReportDetail = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchReport = async () => {
    setLoading(true);
    try {
      const res = await reportsAPI.getById(id);
      setReport(res.data);
    } catch { setReport(null); }
    setLoading(false);
  };

  useEffect(() => { fetchReport(); }, [id]);

  const handleVerify = async () => {
    try {
      await reportsAPI.verify(id);
      fetchReport();
    } catch (err) { setError(err.response?.data?.error || 'Failed to verify'); }
  };

  const handleDownload = async (fileId, fileName) => {
    try {
      const res = await reportsAPI.downloadFile(id, fileId);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch { setError('Failed to download file'); }
  };

  if (loading) return <><Topbar title="Report Detail" /><div className="page-content"><Loading /></div></>;
  if (error) return <><Topbar title="Report Detail" /><div className="page-content"><ErrorMessage message={error} onRetry={fetchReport} /></div></>;
  if (!report) return null;

  const statusColors = { Pending: 'warning', Completed: 'info', Verified: 'success' };
  const canVerify = ['Admin', 'Doctor'].includes(user.role) && report.status !== 'Verified';

  return (
    <>
      <Topbar title={report.title} />
      <div className="page-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
          <button className="btn btn-outline" onClick={() => navigate('/reports')}>← Back</button>
          {canVerify && <button className="btn btn-primary" onClick={handleVerify}>✓ Verify Report</button>}
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Report Information</h3>
            <Badge status={statusColors[report.status]} text={report.status} />
          </div>
          <div className="detail-grid">
            <DetailItem label="Type" value={report.report_type} />
            <DetailItem label="Date" value={report.report_date} />
            <DetailItem label="Patient" value={report.patient_name} />
            <DetailItem label="Doctor" value={`Dr. ${report.doctor_name}`} />
            {report.verified_by_name && <DetailItem label="Verified By" value={`Dr. ${report.verified_by_name}`} />}
            {report.verified_at && <DetailItem label="Verified At" value={report.verified_at} />}
          </div>
        </div>

        {report.content && (
          <div className="card">
            <div className="card-header"><h3>Report Content</h3></div>
            <div style={{ padding: 20, whiteSpace: 'pre-wrap', lineHeight: 1.8, fontSize: 14 }}>{report.content}</div>
          </div>
        )}

        {report.files && report.files.length > 0 && (
          <div className="card">
            <div className="card-header"><h3>Attached Files</h3></div>
            <div style={{ padding: 16 }}>
              {report.files.map(f => (
                <div key={f.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: '1px solid #eee' }}>
                  <div>
                    <strong>{f.file_name}</strong>
                    <span style={{ color: '#999', marginLeft: 12, fontSize: 13 }}>{f.file_type} • {(f.file_size / 1024).toFixed(1)} KB</span>
                  </div>
                  <button className="btn btn-outline btn-sm" onClick={() => handleDownload(f.id, f.file_name)}>Download</button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default ReportDetail;
