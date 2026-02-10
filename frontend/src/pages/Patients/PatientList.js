import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { patientsAPI } from '../../api/axios';
import Topbar from '../../components/Layout/Topbar';
import { Loading, EmptyState, Pagination, Badge } from '../../components/Common';

const PatientList = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const perPage = 15;

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const res = await patientsAPI.list({ search, page, per_page: perPage });
        setPatients(res.data.patients || []);
        setTotal(res.data.total || 0);
      } catch {}
      setLoading(false);
    };
    fetch();
  }, [search, page]);

  return (
    <>
      <Topbar title="Patients" />
      <div className="page-content">
        <div className="card">
          <div className="toolbar">
            <div className="search-box">
              <input
                type="text"
                className="form-control"
                placeholder="Search by name, MRN, phone..."
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1); }}
              />
            </div>
            {['Admin', 'Staff'].includes(user.role) && (
              <button className="btn btn-primary" onClick={() => navigate('/patients/new')}>
                + Register Patient
              </button>
            )}
          </div>

          {loading ? <Loading /> : patients.length === 0 ? <EmptyState message="No patients found" /> : (
            <>
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>MRN</th><th>Name</th><th>DOB</th><th>Gender</th><th>Blood Group</th><th>Phone</th><th>City</th><th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {patients.map(p => (
                      <tr key={p.id}>
                        <td><strong>{p.mrn}</strong></td>
                        <td>{p.first_name} {p.last_name}</td>
                        <td>{p.date_of_birth}</td>
                        <td>{p.gender}</td>
                        <td>{p.blood_group || '—'}</td>
                        <td>{p.phone || '—'}</td>
                        <td>{p.city || '—'}</td>
                        <td>
                          <Link to={`/patients/${p.id}`} className="btn btn-outline btn-sm">View</Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={page} totalPages={Math.ceil(total / perPage)} onPageChange={setPage} />
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default PatientList;
