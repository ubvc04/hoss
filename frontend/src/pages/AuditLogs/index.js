import React, { useState, useEffect, useCallback } from 'react';
import { auditAPI } from '../../api/axios';
import Topbar from '../../components/Layout/Topbar';
import { Loading, EmptyState, ErrorMessage, Pagination } from '../../components/Common';

const AuditLogsPage = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [actionFilter, setActionFilter] = useState('');

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, per_page: 25 };
      if (actionFilter) params.action = actionFilter;
      const res = await auditAPI.getAll(params);
      setLogs(res.data.logs || []);
      setTotal(res.data.total || 0);
    } catch { setLogs([]); setTotal(0); }
    setLoading(false);
  }, [page, actionFilter]);

  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  const actionColors = {
    LOGIN: '#3b82f6', LOGOUT: '#6b7280', CREATE: '#22c55e', UPDATE: '#f59e0b',
    DELETE: '#ef4444', VIEW: '#8b5cf6', UPLOAD: '#06b6d4', VERIFY: '#10b981',
    PAYMENT: '#f97316'
  };

  return (
    <>
      <Topbar title="Audit Logs" />
      <div className="page-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
          <select className="form-control" style={{ width: 200 }} value={actionFilter} onChange={e => { setActionFilter(e.target.value); setPage(1); }}>
            <option value="">All Actions</option>
            {['LOGIN', 'LOGOUT', 'CREATE', 'UPDATE', 'DELETE', 'VIEW', 'UPLOAD', 'VERIFY', 'PAYMENT'].map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>

        {error && <ErrorMessage message={error} onRetry={() => { setError(''); fetchLogs(); }} />}
        {loading ? <Loading /> : logs.length === 0 ? <EmptyState message="No audit logs found" /> : (
          <>
            <div className="table-container">
              <table>
                <thead><tr><th>Timestamp</th><th>User</th><th>Action</th><th>Resource</th><th>Details</th><th>IP Address</th></tr></thead>
                <tbody>
                  {logs.map(log => (
                    <tr key={log.id}>
                      <td style={{ whiteSpace: 'nowrap', fontSize: 13 }}>{log.created_at?.replace('T', ' ').substring(0, 19)}</td>
                      <td>{log.username || 'System'}</td>
                      <td>
                        <span style={{ background: actionColors[log.action] || '#6b7280', color: '#fff', padding: '2px 8px', borderRadius: 4, fontSize: 12, fontWeight: 600 }}>
                          {log.action}
                        </span>
                      </td>
                      <td>{log.resource_type}{log.resource_id ? ` #${log.resource_id}` : ''}</td>
                      <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 13 }}>{log.details || '-'}</td>
                      <td style={{ fontSize: 13 }}>{log.ip_address || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={page} total={total} perPage={25} onPageChange={setPage} />
          </>
        )}
      </div>
    </>
  );
};

export default AuditLogsPage;
