import React, { useState, useEffect, useCallback } from 'react';
import { usersAPI } from '../../api/axios';
import Topbar from '../../components/Layout/Topbar';
import { Loading, EmptyState, ErrorMessage, Badge, Pagination, Modal } from '../../components/Common';

const roleColors = { admin: 'danger', doctor: 'info', staff: 'warning', patient: 'success' };

const UsersPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [roleFilter, setRoleFilter] = useState('');
  const [search, setSearch] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState(null);
  const [form, setForm] = useState({ username: '', password: '', first_name: '', last_name: '', email: '', phone: '', role_id: '' });
  const [saving, setSaving] = useState(false);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, per_page: 15 };
      if (roleFilter) params.role = roleFilter;
      if (search) params.search = search;
      const res = await usersAPI.getAll(params);
      setUsers(res.data.users || []);
      setTotal(res.data.total || 0);
    } catch { setUsers([]); setTotal(0); }
    setLoading(false);
  }, [page, roleFilter, search]);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await usersAPI.create(form);
      setShowCreate(false);
      setForm({ username: '', password: '', first_name: '', last_name: '', email: '', phone: '', role_id: '' });
      fetchUsers();
    } catch (err) { setError(err.response?.data?.error || 'Failed to create user'); }
    setSaving(false);
  };

  const handleEdit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const { password, username, ...payload } = form;
      if (password) payload.password = password;
      await usersAPI.update(showEdit.id, payload);
      setShowEdit(null);
      fetchUsers();
    } catch (err) { setError(err.response?.data?.error || 'Failed to update user'); }
    setSaving(false);
  };

  const handleToggleStatus = async (u) => {
    try {
      await usersAPI.update(u.id, { is_active: !u.is_active });
      fetchUsers();
    } catch (err) { setError(err.response?.data?.error || 'Failed'); }
  };

  const openEdit = (u) => {
    setForm({ username: u.username, password: '', first_name: u.first_name, last_name: u.last_name, email: u.email || '', phone: u.phone || '', role_id: u.role_id || '' });
    setShowEdit(u);
  };

  return (
    <>
      <Topbar title="User Management" />
      <div className="page-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, gap: 12, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', gap: 12 }}>
            <input className="form-control" placeholder="Search users..." style={{ width: 220 }} value={search} onChange={e => setSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && setPage(1)} />
            <select className="form-control" style={{ width: 160 }} value={roleFilter} onChange={e => { setRoleFilter(e.target.value); setPage(1); }}>
              <option value="">All Roles</option>
              {['Admin', 'Doctor', 'Staff', 'Patient'].map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <button className="btn btn-primary" onClick={() => { setForm({ username: '', password: '', first_name: '', last_name: '', email: '', phone: '', role_id: '' }); setShowCreate(true); }}>+ Add User</button>
        </div>

        {error && <ErrorMessage message={error} onRetry={() => { setError(''); fetchUsers(); }} />}
        {loading ? <Loading /> : users.length === 0 ? <EmptyState message="No users found" /> : (
          <>
            <div className="table-container">
              <table>
                <thead><tr><th>Username</th><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Actions</th></tr></thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id}>
                      <td>{u.username}</td>
                      <td>{u.first_name} {u.last_name}</td>
                      <td>{u.email || '-'}</td>
                      <td><Badge status={roleColors[u.role_name] || 'secondary'} text={u.role_name} /></td>
                      <td><Badge status={u.is_active ? 'success' : 'danger'} text={u.is_active ? 'Active' : 'Inactive'} /></td>
                      <td style={{ display: 'flex', gap: 8 }}>
                        <button className="btn btn-outline btn-sm" onClick={() => openEdit(u)}>Edit</button>
                        <button className={`btn btn-sm ${u.is_active ? 'btn-danger' : 'btn-primary'}`} style={{ fontSize: 12, padding: '4px 8px' }} onClick={() => handleToggleStatus(u)}>
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={page} total={total} perPage={15} onPageChange={setPage} />
          </>
        )}
      </div>

      <Modal show={showCreate} title="Create User" onClose={() => setShowCreate(false)}>
        <form onSubmit={handleCreate}>
          <div className="form-row">
            <div className="form-group"><label className="required">Username</label><input className="form-control" value={form.username} onChange={e => setForm(p => ({ ...p, username: e.target.value }))} required /></div>
            <div className="form-group"><label className="required">Password</label><input type="password" className="form-control" value={form.password} onChange={e => setForm(p => ({ ...p, password: e.target.value }))} required /></div>
          </div>
          <div className="form-row">
            <div className="form-group"><label className="required">First Name</label><input className="form-control" value={form.first_name} onChange={e => setForm(p => ({ ...p, first_name: e.target.value }))} required /></div>
            <div className="form-group"><label className="required">Last Name</label><input className="form-control" value={form.last_name} onChange={e => setForm(p => ({ ...p, last_name: e.target.value }))} required /></div>
          </div>
          <div className="form-row">
            <div className="form-group"><label>Email</label><input type="email" className="form-control" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} /></div>
            <div className="form-group"><label>Phone</label><input className="form-control" value={form.phone} onChange={e => setForm(p => ({ ...p, phone: e.target.value }))} /></div>
          </div>
          <div className="form-group">
            <label className="required">Role</label>
            <select className="form-control" value={form.role_id} onChange={e => setForm(p => ({ ...p, role_id: e.target.value }))} required>
              <option value="">Select Role</option>
              <option value="1">Admin</option>
              <option value="2">Doctor</option>
              <option value="3">Staff</option>
              <option value="4">Patient</option>
            </select>
          </div>
          <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>{saving ? 'Creating...' : 'Create User'}</button>
        </form>
      </Modal>

      <Modal show={!!showEdit} title="Edit User" onClose={() => setShowEdit(null)}>
        <form onSubmit={handleEdit}>
          <div className="form-row">
            <div className="form-group"><label>First Name</label><input className="form-control" value={form.first_name} onChange={e => setForm(p => ({ ...p, first_name: e.target.value }))} /></div>
            <div className="form-group"><label>Last Name</label><input className="form-control" value={form.last_name} onChange={e => setForm(p => ({ ...p, last_name: e.target.value }))} /></div>
          </div>
          <div className="form-row">
            <div className="form-group"><label>Email</label><input type="email" className="form-control" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} /></div>
            <div className="form-group"><label>Phone</label><input className="form-control" value={form.phone} onChange={e => setForm(p => ({ ...p, phone: e.target.value }))} /></div>
          </div>
          <div className="form-group"><label>New Password (leave blank to keep)</label><input type="password" className="form-control" value={form.password} onChange={e => setForm(p => ({ ...p, password: e.target.value }))} /></div>
          <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>{saving ? 'Saving...' : 'Update User'}</button>
        </form>
      </Modal>
    </>
  );
};

export default UsersPage;
