import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { notificationsAPI } from '../../api/axios';
import { FiBell } from 'react-icons/fi';

const Topbar = ({ title }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await notificationsAPI.list({ per_page: 5, unread: 'true' });
        setNotifications(res.data.notifications || []);
        setUnreadCount(res.data.unread_count || 0);
      } catch {}
    };
    fetch();
  }, []);

  useEffect(() => {
    const handleClick = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleMarkRead = async (id) => {
    try {
      await notificationsAPI.markRead(id);
      setNotifications(prev => prev.filter(n => n.id !== id));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch {}
  };

  return (
    <div className="topbar">
      <h1>{title}</h1>
      <div className="topbar-actions">
        <div ref={dropdownRef} style={{ position: 'relative' }}>
          <div className="notification-badge" onClick={() => setShowDropdown(!showDropdown)}>
            <FiBell />
            {unreadCount > 0 && <span className="badge">{unreadCount}</span>}
          </div>
          {showDropdown && (
            <div style={{
              position: 'absolute', right: 0, top: 36, width: 340,
              background: '#fff', borderRadius: 8, boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
              zIndex: 100, overflow: 'hidden',
            }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid #eee', fontWeight: 600, fontSize: 14, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Notifications</span>
                <span onClick={() => navigate('/notifications')} style={{ fontSize: 12, color: '#2980b9', cursor: 'pointer' }}>View All</span>
              </div>
              {notifications.length === 0 ? (
                <div style={{ padding: 20, textAlign: 'center', color: '#999', fontSize: 13 }}>No new notifications</div>
              ) : (
                notifications.map(n => (
                  <div key={n.id} style={{ padding: '10px 16px', borderBottom: '1px solid #f5f5f5', cursor: 'pointer', fontSize: 13 }}
                       onClick={() => handleMarkRead(n.id)}>
                    <div style={{ fontWeight: 500, marginBottom: 2 }}>{n.title}</div>
                    <div style={{ color: '#888', fontSize: 12 }}>{n.message}</div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Topbar;
