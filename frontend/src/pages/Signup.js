import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authAPI } from '../api/axios';

const Signup = () => {
  const navigate = useNavigate();
  const [roles, setRoles] = useState([]);
  const [form, setForm] = useState({
    first_name: '', last_name: '', username: '', email: '', phone: '',
    password: '', confirm_password: '', role_id: '', admin_password: '',
    gender: '', date_of_birth: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    authAPI.getRoles().then(res => setRoles(res.data.roles || [])).catch(() => {});
  }, []);

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (form.password !== form.confirm_password) {
      setError('Passwords do not match');
      return;
    }
    if (form.password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    if (!form.admin_password) {
      setError('Admin password is required to create accounts');
      return;
    }

    setLoading(true);
    try {
      const { confirm_password, ...payload } = form;
      await authAPI.signup(payload);
      setSuccess('Account created successfully! Redirecting to login...');
      setTimeout(() => navigate('/login'), 2000);
    } catch (err) {
      setError(err.response?.data?.error || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card" style={{ maxWidth: 520 }}>
        <div className="logo-section">
          <div className="logo-icon">🏥</div>
          <h1>Create Account</h1>
          <p className="subtitle">Hospital Management System</p>
        </div>

        {error && <div className="login-error">{error}</div>}
        {success && <div style={{ background: '#dcfce7', color: '#166534', padding: '12px 16px', borderRadius: 8, marginBottom: 16, fontSize: 14 }}>{success}</div>}

        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div className="form-group">
              <label className="required">First Name</label>
              <input className="form-control" name="first_name" value={form.first_name} onChange={handleChange} placeholder="First name" required />
            </div>
            <div className="form-group">
              <label className="required">Last Name</label>
              <input className="form-control" name="last_name" value={form.last_name} onChange={handleChange} placeholder="Last name" required />
            </div>
          </div>

          <div className="form-group">
            <label className="required">Username</label>
            <input className="form-control" name="username" value={form.username} onChange={handleChange} placeholder="Choose a unique username" required />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div className="form-group">
              <label className="required">Email</label>
              <input className="form-control" type="email" name="email" value={form.email} onChange={handleChange} placeholder="Email address" required />
            </div>
            <div className="form-group">
              <label className="required">Phone</label>
              <input className="form-control" name="phone" value={form.phone} onChange={handleChange} placeholder="Phone number" required />
            </div>
          </div>

          <div className="form-group">
            <label className="required">Role</label>
            <select className="form-control" name="role_id" value={form.role_id} onChange={handleChange} required>
              <option value="">Select role</option>
              {roles.map(r => (
                <option key={r.id} value={r.id}>{r.name} — {r.description}</option>
              ))}
            </select>
          </div>

          {roles.find(r => String(r.id) === String(form.role_id) && r.name === 'Patient') && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="form-group">
                <label className="required">Date of Birth</label>
                <input className="form-control" type="date" name="date_of_birth" value={form.date_of_birth} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label className="required">Gender</label>
                <select className="form-control" name="gender" value={form.gender} onChange={handleChange} required>
                  <option value="">Select gender</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div className="form-group">
              <label className="required">Password</label>
              <input className="form-control" type="password" name="password" value={form.password} onChange={handleChange} placeholder="Min 6 characters" required />
            </div>
            <div className="form-group">
              <label className="required">Confirm Password</label>
              <input className="form-control" type="password" name="confirm_password" value={form.confirm_password} onChange={handleChange} placeholder="Confirm password" required />
            </div>
          </div>

          <div style={{ marginTop: 8, padding: 16, background: '#fef3c7', borderRadius: 8, border: '1px solid #fbbf24' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="required" style={{ color: '#92400e', fontWeight: 600 }}>🔒 Admin Password</label>
              <input className="form-control" type="password" name="admin_password" value={form.admin_password} onChange={handleChange} placeholder="Enter admin password to authorize" required />
              <small style={{ color: '#92400e', fontSize: 12 }}>Only the hospital admin can authorize new account creation.</small>
            </div>
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: 16 }} disabled={loading}>
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <div style={{ marginTop: 20, textAlign: 'center' }}>
          <span style={{ fontSize: 14, color: '#666' }}>Already have an account? </span>
          <Link to="/login" style={{ color: '#2563eb', fontSize: 14, fontWeight: 600, textDecoration: 'none' }}>
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Signup;
