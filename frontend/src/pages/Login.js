import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Login = () => {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!identifier || !password) {
      setError('Please enter your credentials and password');
      return;
    }
    setLoading(true);
    try {
      await login(identifier, password);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="logo-section">
          <div className="logo-icon">🏥</div>
          <h1>Hospital Management System</h1>
          <p className="subtitle">Patient Portal & Staff Gateway</p>
        </div>

        {error && <div className="login-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="required">Username / Email / Phone</label>
            <input
              type="text"
              className="form-control"
              placeholder="Enter username, email or phone"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              autoFocus
            />
          </div>
          <div className="form-group">
            <label className="required">Password</label>
            <input
              type="password"
              className="form-control"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div style={{ marginTop: 16, textAlign: 'center' }}>
          <Link to="/forgot-password" style={{ color: '#2563eb', fontSize: 14, textDecoration: 'none' }}>
            Forgot Password?
          </Link>
        </div>

        <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid #e5e7eb', textAlign: 'center', fontSize: 13, color: '#666' }}>
          Contact hospital administration to create an account
        </div>
      </div>
    </div>
  );
};

export default Login;
