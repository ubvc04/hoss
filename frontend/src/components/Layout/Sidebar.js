import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { notificationsAPI } from '../../api/axios';
import { FiHome, FiUsers, FiCalendar, FiFileText, FiActivity, FiDollarSign,
         FiClipboard, FiSettings, FiLogOut, FiBell, FiUser, FiList,
         FiPlusCircle, FiHeart, FiShield } from 'react-icons/fi';

const Sidebar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const res = await notificationsAPI.list({ per_page: 1 });
        setUnreadCount(res.data.unread_count || 0);
      } catch {}
    };
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  const isActive = (path) => location.pathname.startsWith(path);

  const getNavItems = () => {
    const common = [
      { path: '/dashboard', icon: <FiHome />, label: 'Dashboard' },
    ];

    if (user.role === 'Admin') {
      return [
        ...common,
        { section: 'Management' },
        { path: '/users', icon: <FiShield />, label: 'User Management' },
        { path: '/patients', icon: <FiUsers />, label: 'Patients' },
        { section: 'Clinical' },
        { path: '/appointments', icon: <FiCalendar />, label: 'Appointments' },
        { path: '/visits', icon: <FiClipboard />, label: 'Visits' },
        { path: '/reports', icon: <FiFileText />, label: 'Reports' },
        { path: '/prescriptions', icon: <FiActivity />, label: 'Prescriptions' },
        { section: 'Finance' },
        { path: '/billing', icon: <FiDollarSign />, label: 'Billing' },
        { section: 'System' },
        { path: '/audit-logs', icon: <FiList />, label: 'Audit Logs' },
        { path: '/notifications', icon: <FiBell />, label: 'Notifications', badge: unreadCount },
      ];
    }

    if (user.role === 'Doctor') {
      return [
        ...common,
        { section: 'Patients' },
        { path: '/patients', icon: <FiUsers />, label: 'My Patients' },
        { section: 'Clinical' },
        { path: '/appointments', icon: <FiCalendar />, label: 'Appointments' },
        { path: '/visits', icon: <FiClipboard />, label: 'Visits' },
        { path: '/prescriptions', icon: <FiActivity />, label: 'Prescriptions' },
        { path: '/reports', icon: <FiFileText />, label: 'Reports' },
        { section: 'Other' },
        { path: '/notifications', icon: <FiBell />, label: 'Notifications', badge: unreadCount },
      ];
    }

    if (user.role === 'Staff') {
      return [
        ...common,
        { section: 'Patient Management' },
        { path: '/patients', icon: <FiUsers />, label: 'Patients' },
        { path: '/patients/new', icon: <FiPlusCircle />, label: 'Register Patient' },
        { section: 'Operations' },
        { path: '/appointments', icon: <FiCalendar />, label: 'Appointments' },
        { path: '/visits', icon: <FiClipboard />, label: 'Visits' },
        { path: '/reports', icon: <FiFileText />, label: 'Reports' },
        { section: 'Finance' },
        { path: '/billing', icon: <FiDollarSign />, label: 'Billing' },
        { section: 'Other' },
        { path: '/notifications', icon: <FiBell />, label: 'Notifications', badge: unreadCount },
      ];
    }

    // Patient
    return [
      ...common,
      { section: 'My Health' },
      { path: '/my-profile', icon: <FiUser />, label: 'My Profile' },
      { path: '/visits', icon: <FiClipboard />, label: 'My Visits' },
      { path: '/clinical', icon: <FiHeart />, label: 'Clinical Data' },
      { path: '/prescriptions', icon: <FiActivity />, label: 'Prescriptions' },
      { path: '/reports', icon: <FiFileText />, label: 'Reports' },
      { section: 'Services' },
      { path: '/appointments', icon: <FiCalendar />, label: 'Appointments' },
      { path: '/billing', icon: <FiDollarSign />, label: 'Bills' },
      { path: '/notifications', icon: <FiBell />, label: 'Notifications', badge: unreadCount },
    ];
  };

  const initials = user.first_name
    ? `${user.first_name[0]}${(user.last_name || '')[0] || ''}`.toUpperCase()
    : user.username[0].toUpperCase();

  const displayName = user.first_name
    ? `${user.first_name} ${user.last_name || ''}`
    : user.username;

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="logo">🏥</div>
        <div>
          <h2>HMS Portal</h2>
          <small>Hospital Management</small>
        </div>
      </div>

      <nav className="sidebar-nav">
        {getNavItems().map((item, idx) => {
          if (item.section) {
            return <div key={idx} className="nav-section">{item.section}</div>;
          }
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${isActive(item.path) ? 'active' : ''}`}
            >
              <span className="icon">{item.icon}</span>
              <span>{item.label}</span>
              {item.badge > 0 && (
                <span style={{
                  marginLeft: 'auto',
                  background: '#e74c3c',
                  color: '#fff',
                  fontSize: 10,
                  padding: '2px 6px',
                  borderRadius: 10,
                  fontWeight: 600,
                }}>{item.badge}</span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="user-info">
          <div className="avatar">{initials}</div>
          <div>
            <div className="user-name">{displayName}</div>
            <div className="user-role">{user.role}</div>
          </div>
        </div>
        <button className="btn-logout" onClick={logout}>
          <FiLogOut style={{ marginRight: 6 }} /> Sign Out
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
