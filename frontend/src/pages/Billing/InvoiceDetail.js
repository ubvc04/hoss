import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { billingAPI } from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import Topbar from '../../components/Layout/Topbar';
import { Loading, ErrorMessage, Badge, DetailItem, Modal } from '../../components/Common';

const InvoiceDetail = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showPayment, setShowPayment] = useState(false);
  const [paymentForm, setPaymentForm] = useState({ amount: '', payment_method: 'Cash', transaction_reference: '' });
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);

  const fetchInvoice = async () => {
    setLoading(true);
    try {
      const res = await billingAPI.get(id);
      setInvoice(res.data.invoice);
    } catch { setInvoice(null); }
    setLoading(false);
  };

  useEffect(() => { fetchInvoice(); }, [id]);

  const handlePayment = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await billingAPI.updatePayment(id, {
        paid_amount: parseFloat(paymentForm.amount),
        payment_method: paymentForm.payment_method,
        payment_status: 'Paid',
        payment_date: new Date().toISOString()
      });
      setShowPayment(false);
      setPaymentForm({ amount: '', payment_method: 'Cash', transaction_reference: '' });
      fetchInvoice();
    } catch (err) { setError(err.response?.data?.error || 'Failed to record payment'); }
    setSaving(false);
  };

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    setUploading(true);
    try {
      const formData = new FormData();
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }
      await billingAPI.uploadFiles(id, formData);
      fetchInvoice();
    } catch (err) { setError(err.response?.data?.error || 'Failed to upload file'); }
    setUploading(false);
    e.target.value = '';
  };

  const handleDownloadFile = async (fileId, fileName) => {
    try {
      const res = await billingAPI.downloadFile(fileId);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch { setError('Failed to download file'); }
  };

  const handleDeleteFile = async (fileId) => {
    if (!window.confirm('Are you sure you want to delete this file?')) return;
    try {
      await billingAPI.deleteFile(id, fileId);
      fetchInvoice();
    } catch { setError('Failed to delete file'); }
  };

  if (loading) return <><Topbar title="Invoice Detail" /><div className="page-content"><Loading /></div></>;
  if (error && !invoice) return <><Topbar title="Invoice Detail" /><div className="page-content"><ErrorMessage message={error} onRetry={fetchInvoice} /></div></>;
  if (!invoice) return null;

  const statusColors = { Pending: 'warning', Partial: 'info', Paid: 'success', Overdue: 'danger', Cancelled: 'danger' };
  const balance = (invoice.total_amount || 0) - (invoice.paid_amount || 0);
  const canPay = ['Admin', 'Staff'].includes(user.role) && balance > 0 && invoice.payment_status !== 'Cancelled';
  const canUpload = ['Admin', 'Staff'].includes(user.role);

  return (
    <>
      <Topbar title={`Invoice ${invoice.invoice_number}`} />
      <div className="page-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
          <button className="btn btn-outline" onClick={() => navigate('/billing')}>← Back</button>
          <div style={{ display: 'flex', gap: 10 }}>
            {canUpload && (
              <label className="btn btn-outline" style={{ cursor: 'pointer', margin: 0 }}>
                {uploading ? 'Uploading...' : '📎 Upload Bill Copy'}
                <input type="file" multiple style={{ display: 'none' }} onChange={handleFileUpload} accept=".pdf,.png,.jpg,.jpeg,.doc,.docx" disabled={uploading} />
              </label>
            )}
            {canPay && <button className="btn btn-primary" onClick={() => { setPaymentForm(p => ({ ...p, amount: balance.toString() })); setShowPayment(true); }}>Record Payment</button>}
          </div>
        </div>

        {error && <div style={{ background: '#fee2e2', color: '#dc2626', padding: '10px 16px', borderRadius: 8, marginBottom: 16 }}>{error}</div>}

        <div className="card">
          <div className="card-header">
            <h3>{invoice.invoice_number}</h3>
            <Badge status={statusColors[invoice.payment_status]} text={invoice.payment_status} />
          </div>
          <div className="detail-grid">
            <DetailItem label="Patient" value={invoice.patient_name} />
            <DetailItem label="Invoice Date" value={invoice.invoice_date} />
            <DetailItem label="Due Date" value={invoice.due_date || 'N/A'} />
            <DetailItem label="Visit ID" value={invoice.visit_id ? `#${invoice.visit_id}` : 'N/A'} />
          </div>
        </div>

        <div className="card">
          <div className="card-header"><h3>Line Items</h3></div>
          {(!invoice.items || invoice.items.length === 0) ? (
            <p style={{ color: '#999', padding: 20 }}>No items</p>
          ) : (
            <div className="table-container">
              <table>
                <thead><tr><th>Description</th><th>Category</th><th>Qty</th><th>Unit Price</th><th>Total</th></tr></thead>
                <tbody>
                  {invoice.items.map((item, i) => (
                    <tr key={i}>
                      <td>{item.description}</td>
                      <td>{item.category || '-'}</td>
                      <td>{item.quantity}</td>
                      <td>₹{(item.unit_price || 0).toLocaleString()}</td>
                      <td>₹{(item.total_price || 0).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
          <div className="stat-card"><div className="stat-value">₹{(invoice.total_amount || 0).toLocaleString()}</div><div className="stat-label">Total Amount</div></div>
          <div className="stat-card"><div className="stat-value">₹{(invoice.discount_amount || 0).toLocaleString()}</div><div className="stat-label">Discount</div></div>
          <div className="stat-card"><div className="stat-value" style={{ color: '#22c55e' }}>₹{(invoice.paid_amount || 0).toLocaleString()}</div><div className="stat-label">Paid</div></div>
          <div className="stat-card"><div className="stat-value" style={{ color: balance > 0 ? '#ef4444' : '#22c55e' }}>₹{balance.toLocaleString()}</div><div className="stat-label">Balance</div></div>
        </div>

        {invoice.insurance_claim_status && (
          <div className="card">
            <div className="card-header"><h3>Insurance</h3></div>
            <div className="detail-grid">
              <DetailItem label="Claim Status" value={invoice.insurance_claim_status} />
              <DetailItem label="Insurance Amount" value={invoice.insurance_amount ? `₹${invoice.insurance_amount.toLocaleString()}` : 'N/A'} />
            </div>
          </div>
        )}

        {/* BILL SOFT COPIES */}
        <div className="card">
          <div className="card-header">
            <h3>Bill Documents</h3>
            {canUpload && (
              <label className="btn btn-primary btn-sm" style={{ cursor: 'pointer', margin: 0 }}>
                + Upload File
                <input type="file" multiple style={{ display: 'none' }} onChange={handleFileUpload} accept=".pdf,.png,.jpg,.jpeg,.doc,.docx" disabled={uploading} />
              </label>
            )}
          </div>
          {(!invoice.files || invoice.files.length === 0) ? (
            <p style={{ color: '#999', padding: 20 }}>No bill documents uploaded yet</p>
          ) : (
            <div className="table-container">
              <table>
                <thead><tr><th>File Name</th><th>Size</th><th>Type</th><th>Actions</th></tr></thead>
                <tbody>
                  {invoice.files.map(f => (
                    <tr key={f.id}>
                      <td>{f.original_name}</td>
                      <td>{f.file_size ? `${(f.file_size / 1024).toFixed(1)} KB` : '—'}</td>
                      <td>{f.mime_type || '—'}</td>
                      <td style={{ display: 'flex', gap: 8 }}>
                        <button className="btn btn-outline btn-sm" onClick={() => handleDownloadFile(f.id, f.original_name)}>Download</button>
                        {canUpload && <button className="btn btn-outline btn-sm" style={{ color: '#dc2626', borderColor: '#dc2626' }} onClick={() => handleDeleteFile(f.id)}>Delete</button>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {invoice.notes && (
          <div className="card">
            <div className="card-header"><h3>Notes</h3></div>
            <p style={{ padding: 16 }}>{invoice.notes}</p>
          </div>
        )}
      </div>

      <Modal show={showPayment} title="Record Payment" onClose={() => setShowPayment(false)}>
        <form onSubmit={handlePayment}>
          <div className="form-group"><label className="required">Amount (₹)</label><input type="number" step="0.01" className="form-control" value={paymentForm.amount} onChange={e => setPaymentForm(p => ({ ...p, amount: e.target.value }))} required /></div>
          <div className="form-group">
            <label>Payment Method</label>
            <select className="form-control" value={paymentForm.payment_method} onChange={e => setPaymentForm(p => ({ ...p, payment_method: e.target.value }))}>
              {['Cash', 'Card', 'UPI', 'Net Banking', 'Insurance', 'Cheque'].map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div className="form-group"><label>Transaction Reference</label><input className="form-control" value={paymentForm.transaction_reference} onChange={e => setPaymentForm(p => ({ ...p, transaction_reference: e.target.value }))} /></div>
          <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>{saving ? 'Processing...' : 'Record Payment'}</button>
        </form>
      </Modal>
    </>
  );
};

export default InvoiceDetail;
