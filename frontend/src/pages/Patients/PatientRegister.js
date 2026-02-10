import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { patientsAPI } from '../../api/axios';
import Topbar from '../../components/Layout/Topbar';
import { Modal } from '../../components/Common';

const PatientRegister = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    first_name: '', last_name: '', date_of_birth: '', gender: '', blood_group: '',
    marital_status: '', address_line1: '', address_line2: '', city: '', state: '',
    postal_code: '', country: 'India', phone: '', email: '',
    emergency_contact_name: '', emergency_contact_phone: '', emergency_contact_relation: '',
    national_id: '', hospital_id: '', password: 'Patient@123',
  });
  const [insurance, setInsurance] = useState({ provider_name: '', policy_number: '', plan_type: '', coverage_start: '', coverage_end: '', max_coverage_amount: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleInsuranceChange = (e) => {
    setInsurance(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!form.first_name || !form.last_name || !form.date_of_birth || !form.gender) {
      setError('First name, last name, DOB, and gender are required');
      return;
    }
    setLoading(true);
    try {
      const payload = { ...form };
      if (insurance.provider_name && insurance.policy_number) {
        payload.insurance = insurance;
      }
      const res = await patientsAPI.create(payload);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to register patient');
    }
    setLoading(false);
  };

  return (
    <>
      <Topbar title="Register New Patient" />
      <div className="page-content">
        {result && (
          <Modal show={true} title="Patient Registered Successfully" onClose={() => navigate(`/patients/${result.patient_id}`)}>
            <div style={{ textAlign: 'center', padding: 20 }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
              <h3 style={{ marginBottom: 16 }}>Patient account created!</h3>
              <div style={{ background: '#f8f9fa', borderRadius: 8, padding: 16, marginBottom: 16, textAlign: 'left' }}>
                <p><strong>MRN:</strong> {result.mrn}</p>
                <p><strong>Username:</strong> {result.username}</p>
                <p><strong>Password:</strong> {result.password}</p>
              </div>
              <p style={{ fontSize: 13, color: '#666' }}>Please provide these credentials to the patient. They can use them to log in to the portal.</p>
              <button className="btn btn-primary btn-lg" style={{ marginTop: 16 }} onClick={() => navigate(`/patients/${result.patient_id}`)}>
                View Patient Profile
              </button>
            </div>
          </Modal>
        )}

        <form onSubmit={handleSubmit}>
          {error && <div className="login-error" style={{ marginBottom: 16 }}>{error}</div>}

          <div className="card">
            <div className="card-header"><h3>Personal Information</h3></div>
            <div className="form-row">
              <div className="form-group"><label className="required">First Name</label><input name="first_name" className="form-control" value={form.first_name} onChange={handleChange} required /></div>
              <div className="form-group"><label className="required">Last Name</label><input name="last_name" className="form-control" value={form.last_name} onChange={handleChange} required /></div>
              <div className="form-group"><label className="required">Date of Birth</label><input type="date" name="date_of_birth" className="form-control" value={form.date_of_birth} onChange={handleChange} required /></div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="required">Gender</label>
                <select name="gender" className="form-control" value={form.gender} onChange={handleChange} required>
                  <option value="">Select</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div className="form-group">
                <label>Blood Group</label>
                <select name="blood_group" className="form-control" value={form.blood_group} onChange={handleChange}>
                  <option value="">Select</option>
                  {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map(bg => <option key={bg} value={bg}>{bg}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Marital Status</label>
                <select name="marital_status" className="form-control" value={form.marital_status} onChange={handleChange}>
                  <option value="">Select</option>
                  <option value="Single">Single</option>
                  <option value="Married">Married</option>
                  <option value="Divorced">Divorced</option>
                  <option value="Widowed">Widowed</option>
                </select>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header"><h3>Contact Details</h3></div>
            <div className="form-row">
              <div className="form-group"><label>Phone</label><input name="phone" className="form-control" value={form.phone} onChange={handleChange} /></div>
              <div className="form-group"><label>Email</label><input type="email" name="email" className="form-control" value={form.email} onChange={handleChange} /></div>
            </div>
            <div className="form-row">
              <div className="form-group"><label>Address Line 1</label><input name="address_line1" className="form-control" value={form.address_line1} onChange={handleChange} /></div>
              <div className="form-group"><label>Address Line 2</label><input name="address_line2" className="form-control" value={form.address_line2} onChange={handleChange} /></div>
            </div>
            <div className="form-row">
              <div className="form-group"><label>City</label><input name="city" className="form-control" value={form.city} onChange={handleChange} /></div>
              <div className="form-group"><label>State</label><input name="state" className="form-control" value={form.state} onChange={handleChange} /></div>
              <div className="form-group"><label>Postal Code</label><input name="postal_code" className="form-control" value={form.postal_code} onChange={handleChange} /></div>
              <div className="form-group"><label>Country</label><input name="country" className="form-control" value={form.country} onChange={handleChange} /></div>
            </div>
          </div>

          <div className="card">
            <div className="card-header"><h3>Emergency Contact</h3></div>
            <div className="form-row">
              <div className="form-group"><label>Name</label><input name="emergency_contact_name" className="form-control" value={form.emergency_contact_name} onChange={handleChange} /></div>
              <div className="form-group"><label>Phone</label><input name="emergency_contact_phone" className="form-control" value={form.emergency_contact_phone} onChange={handleChange} /></div>
              <div className="form-group"><label>Relation</label><input name="emergency_contact_relation" className="form-control" value={form.emergency_contact_relation} onChange={handleChange} /></div>
            </div>
          </div>

          <div className="card">
            <div className="card-header"><h3>Identification</h3></div>
            <div className="form-row">
              <div className="form-group"><label>National ID (Aadhaar)</label><input name="national_id" className="form-control" value={form.national_id} onChange={handleChange} /></div>
              <div className="form-group"><label>Hospital ID</label><input name="hospital_id" className="form-control" value={form.hospital_id} onChange={handleChange} /></div>
              <div className="form-group"><label>Initial Password</label><input name="password" className="form-control" value={form.password} onChange={handleChange} /></div>
            </div>
          </div>

          <div className="card">
            <div className="card-header"><h3>Insurance (Optional)</h3></div>
            <div className="form-row">
              <div className="form-group"><label>Provider</label><input name="provider_name" className="form-control" value={insurance.provider_name} onChange={handleInsuranceChange} /></div>
              <div className="form-group"><label>Policy Number</label><input name="policy_number" className="form-control" value={insurance.policy_number} onChange={handleInsuranceChange} /></div>
              <div className="form-group"><label>Plan Type</label><input name="plan_type" className="form-control" value={insurance.plan_type} onChange={handleInsuranceChange} /></div>
            </div>
            <div className="form-row">
              <div className="form-group"><label>Coverage Start</label><input type="date" name="coverage_start" className="form-control" value={insurance.coverage_start} onChange={handleInsuranceChange} /></div>
              <div className="form-group"><label>Coverage End</label><input type="date" name="coverage_end" className="form-control" value={insurance.coverage_end} onChange={handleInsuranceChange} /></div>
              <div className="form-group"><label>Max Coverage (₹)</label><input type="number" name="max_coverage_amount" className="form-control" value={insurance.max_coverage_amount} onChange={handleInsuranceChange} /></div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <button type="submit" className="btn btn-primary btn-lg" disabled={loading}>
              {loading ? 'Registering...' : 'Register Patient'}
            </button>
            <button type="button" className="btn btn-outline btn-lg" onClick={() => navigate('/patients')}>Cancel</button>
          </div>
        </form>
      </div>
    </>
  );
};

export default PatientRegister;
