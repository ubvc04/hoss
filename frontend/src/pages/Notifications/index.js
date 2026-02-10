import React, { useState, useEffect } from 'react';
import { notificationsAPI } from '../../api/axios';
import Topbar from '../../components/Layout/Topbar';
import { Loading, EmptyState, ErrorMessage } from '../../components/Common';

const NotificationsPage = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const res = await notificationsAPI.getAll();
      setNotifications(res.data.notifications || []);
    } catch { setNotifications([]); }
    setLoading(false);
  };

  useEffect(() => { fetchNotifications(); }, []);

  const handleMarkRead = async (id) => {
    try {
      await notificationsAPI.markRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch {}
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsAPI.markAllRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch {}
  };

  const typeIcons = {
    appointment: '📅', prescription: '💊', report: '📋', billing: '💰',
    visit: '🏥', general: '🔔', system: '⚙️'
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <>
      <Topbar title="Notifications" />
      <div className="page-content">
        {unreadCount > 0 && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <span style={{ color: '#666' }}>{unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}</span>
            <button className="btn btn-outline" onClick={handleMarkAllRead}>Mark All as Read</button>
          </div>
        )}

        {error && <ErrorMessage message={error} onRetry={() => { setError(''); fetchNotifications(); }} />}
        {loading ? <Loading /> : notifications.length === 0 ? <EmptyState message="No notifications" /> : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {notifications.map(n => (
              <div
                key={n.id}
                style={{
                  display: 'flex', alignItems: 'flex-start', gap: 16, padding: 16,
                  background: n.is_read ? '#fff' : '#f0f7ff', borderRadius: 8,
                  border: `1px solid ${n.is_read ? '#e5e7eb' : '#bfdbfe'}`, cursor: n.is_read ? 'default' : 'pointer',
                  transition: 'all 0.2s'
                }}
                onClick={() => !n.is_read && handleMarkRead(n.id)}
              >
                <div style={{ fontSize: 24, flexShrink: 0 }}>{typeIcons[n.type] || '🔔'}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <strong style={{ fontSize: 14 }}>{n.title}</strong>
                    <span style={{ fontSize: 12, color: '#999' }}>{n.created_at?.replace('T', ' ').substring(0, 16)}</span>
                  </div>
                  <p style={{ margin: 0, fontSize: 13, color: '#555', lineHeight: 1.5 }}>{n.message}</p>
                </div>
                {!n.is_read && <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#3b82f6', flexShrink: 0, marginTop: 6 }} />}
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
};

export default NotificationsPage;
