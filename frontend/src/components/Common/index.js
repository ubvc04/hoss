import React from 'react';

export const Loading = () => (
  <div className="loading"><div className="spinner"></div></div>
);

export const EmptyState = ({ icon = '📋', message = 'No data found' }) => (
  <div className="empty-state">
    <div className="icon">{icon}</div>
    <p>{message}</p>
  </div>
);

export const ErrorMessage = ({ message }) => (
  <div style={{ padding: 20, textAlign: 'center', color: '#e74c3c' }}>
    <p>⚠️ {message || 'Something went wrong'}</p>
  </div>
);

export const Badge = ({ status }) => {
  const map = {
    Active: 'badge-success', Confirmed: 'badge-success', Paid: 'badge-success', Verified: 'badge-success', Resolved: 'badge-success', Completed: 'badge-success',
    Pending: 'badge-warning', Requested: 'badge-warning', Partial: 'badge-warning', Filed: 'badge-warning',
    Cancelled: 'badge-danger', Rejected: 'badge-danger', Overdue: 'badge-danger', 'No-Show': 'badge-danger', 'Life-threatening': 'badge-danger', Critical: 'badge-danger', Severe: 'badge-danger',
    Rescheduled: 'badge-info', Transferred: 'badge-info', 'In-Person': 'badge-info', Online: 'badge-primary',
    Discharged: 'badge-secondary', Inactive: 'badge-secondary', Chronic: 'badge-secondary',
    Mild: 'badge-success', Moderate: 'badge-warning',
  };
  const cls = map[status] || 'badge-secondary';
  return <span className={`badge ${cls}`}>{status}</span>;
};

export const Pagination = ({ page, totalPages, onPageChange }) => {
  if (totalPages <= 1) return null;
  return (
    <div className="pagination">
      <button disabled={page <= 1} onClick={() => onPageChange(page - 1)}>Previous</button>
      <span>Page {page} of {totalPages}</span>
      <button disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>Next</button>
    </div>
  );
};

export const Modal = ({ show, onClose, title, children, footer, large }) => {
  if (!show) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className={`modal ${large ? 'modal-lg' : ''}`} onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
};

export const DetailItem = ({ label, value }) => (
  <div className="detail-item">
    <div className="label">{label}</div>
    <div className="value">{value || '—'}</div>
  </div>
);

export const StatCard = ({ icon, color, value, label }) => (
  <div className="stat-card">
    <div className={`stat-icon ${color}`}>{icon}</div>
    <div className="stat-info">
      <h4>{value}</h4>
      <p>{label}</p>
    </div>
  </div>
);
