import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { billingAPI } from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import Topbar from '../../components/Layout/Topbar';
import { Loading, EmptyState, ErrorMessage, Badge, Pagination } from '../../components/Common';

const statusColors = { Pending: 'warning', Partial: 'info', Paid: 'success', Overdue: 'danger', Cancelled: 'danger' };

const InvoiceList = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');

  const fetchInvoices = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, per_page: 15 };
      if (statusFilter) params.payment_status = statusFilter;
      const res = await billingAPI.getAll(params);
      setInvoices(res.data.invoices || []);
      setTotal(res.data.total || 0);
    } catch { setInvoices([]); setTotal(0); }
    setLoading(false);
  }, [page, statusFilter]);

  useEffect(() => { fetchInvoices(); }, [fetchInvoices]);

  const canCreate = ['Admin', 'Staff'].includes(user.role);

  return (
    <>
      <Topbar title="Billing & Invoices" />
      <div className="page-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <select className="form-control" style={{ width: 200 }} value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }}>
            <option value="">All Statuses</option>
            {['Pending', 'Partial', 'Paid', 'Overdue', 'Cancelled'].map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          {canCreate && <button className="btn btn-primary" onClick={() => navigate('/billing/new')}>+ New Invoice</button>}
        </div>

        {error && <ErrorMessage message={error} onRetry={() => { setError(''); fetchInvoices(); }} />}
        {loading ? <Loading /> : invoices.length === 0 ? <EmptyState message="No invoices found" /> : (
          <>
            <div className="table-container">
              <table>
                <thead><tr><th>Invoice #</th>{user.role !== 'Patient' && <th>Patient</th>}<th>Date</th><th>Total</th><th>Paid</th><th>Balance</th><th>Status</th><th>Actions</th></tr></thead>
                <tbody>
                  {invoices.map(inv => (
                    <tr key={inv.id}>
                      <td><strong>{inv.invoice_number}</strong></td>
                      {user.role !== 'Patient' && <td>{inv.patient_name}</td>}
                      <td>{inv.invoice_date}</td>
                      <td>₹{(inv.total_amount || 0).toLocaleString()}</td>
                      <td>₹{(inv.paid_amount || 0).toLocaleString()}</td>
                      <td>₹{((inv.total_amount || 0) - (inv.paid_amount || 0)).toLocaleString()}</td>
                      <td><Badge status={statusColors[inv.payment_status]} text={inv.payment_status} /></td>
                      <td><button className="btn btn-outline btn-sm" onClick={() => navigate(`/billing/${inv.id}`)}>View</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={page} total={total} perPage={15} onPageChange={setPage} />
          </>
        )}
      </div>
    </>
  );
};

export default InvoiceList;
