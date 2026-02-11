import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { patientsAPI } from '../../api/axios';
import Topbar from '../../components/Layout/Topbar';
import { Modal } from '../../components/Common';

const PatientRegister = () => {
  const navigate = useNavigate();
  
  // Step 1: Account creation, Step 2: Patient details
  const [step, setStep] = useState(1);
  
  // Step 1 form - Account details
  const [account, setAccount] = useState({
    first_name: '',
    last_name: '',
    username: '',
    email: '',
    phone: '',
    password: '',
  });

  // Step 2 form - Patient details (after account created)
  const [form, setForm] = useState({
    date_of_birth: '', gender: '', blood_group: '',
    marital_status: '', address_line1: '', address_line2: '', city: '', state: '',
    postal_code: '', country: 'India',
    emergency_contact_name: '', emergency_contact_phone: '', emergency_contact_relation: '',
    national_id: '', hospital_id: '',
  });
  
  const [insurance, setInsurance] = useState({ 
    provider_name: '', policy_number: '', plan_type: '', 
    coverage_start: '', coverage_end: '', max_coverage_amount: '' 
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const handleAccountChange = (e) => {
    setAccount(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleInsuranceChange = (e) => {
    setInsurance(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  // Step 1: Validate and proceed to step 2
  const handleCreateAccount = (e) => {
    e.preventDefault();
    setError('');
    
    if (!account.first_name || !account.last_name) {
      setError('First name and last name are required');
      return;
    }
    
    if (!account.username) {
      setError('Username is required for patient login');
      return;
    }
    
    if (!account.password) {
      setError('Password is required');
      return;
    }
    
    // Move to step 2 - patient details
    setStep(2);
  };

  // Step 2: Submit full patient data
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!form.date_of_birth || !form.gender) {
      setError('Date of birth and gender are required');
      return;
    }
    
    setLoading(true);
    try {
      const payload = {
        ...account,
        ...form,
      };
      
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
                <p><strong>Name:</strong> {account.first_name} {account.last_name}</p>
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

        {/* Step Indicator */}
        <div className="card" style={{ marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', padding: '16px 20px' }}>
            <div style={{ 
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              width: 32, height: 32, borderRadius: '50%', 
              background: step >= 1 ? '#4f46e5' : '#e5e7eb', 
              color: step >= 1 ? '#fff' : '#6b7280',
              fontWeight: 600, fontSize: 14
            }}>1</div>
            <span style={{ marginLeft: 8, fontWeight: step === 1 ? 600 : 400, color: step === 1 ? '#4f46e5' : '#6b7280' }}>
              Create Account
            </span>
            <div style={{ flex: 1, height: 2, background: step >= 2 ? '#4f46e5' : '#e5e7eb', margin: '0 16px' }}></div>
            <div style={{ 
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              width: 32, height: 32, borderRadius: '50%', 
              background: step >= 2 ? '#4f46e5' : '#e5e7eb', 
              color: step >= 2 ? '#fff' : '#6b7280',
              fontWeight: 600, fontSize: 14
            }}>2</div>
            <span style={{ marginLeft: 8, fontWeight: step === 2 ? 600 : 400, color: step === 2 ? '#4f46e5' : '#6b7280' }}>
              Patient Details
            </span>
          </div>
        </div>

        {error && <div className="login-error" style={{ marginBottom: 16 }}>{error}</div>}

        {/* Step 1: Account Creation */}
        {step === 1 && (
          <form onSubmit={handleCreateAccount}>
            <div className="card">
              <div className="card-header"><h3>Create Patient Account</h3></div>
              <p style={{ padding: '0 20px', color: '#666', marginBottom: 16 }}>
                First, create a login account for the patient. They will use these credentials to access the portal.
              </p>
              <div className="form-row">
                <div className="form-group">
                  <label className="required">First Name</label>
                  <input 
                    name="first_name" 
                    className="form-control" 
                    value={account.first_name} 
                    onChange={handleAccountChange} 
                    placeholder="Enter first name"
                    required 
                  />
                </div>
                <div className="form-group">
                  <label className="required">Last Name</label>
                  <input 
                    name="last_name" 
                    className="form-control" 
                    value={account.last_name} 
                    onChange={handleAccountChange} 
                    placeholder="Enter last name"
                    required 
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Email</label>
                  <input 
                    type="email" 
                    name="email" 
                    className="form-control" 
                    value={account.email} 
                    onChange={handleAccountChange} 
                    placeholder="patient@example.com"
                  />
                </div>
                <div className="form-group">
                  <label>Phone</label>
                  <input 
                    name="phone" 
                    className="form-control" 
                    value={account.phone} 
                    onChange={handleAccountChange} 
                    placeholder="Enter phone number"
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="required">Username</label>
                  <input 
                    name="username" 
                    className="form-control" 
                    value={account.username} 
                    onChange={handleAccountChange} 
                    placeholder="Enter username for patient login"
                    required
                  />
                  <small style={{ color: '#666' }}>Patient will use this username to login</small>
                </div>
                <div className="form-group">
                  <label className="required">Password</label>
                  <input 
                    name="password" 
                    className="form-control" 
                    value={account.password} 
                    onChange={handleAccountChange} 
                    placeholder="Enter password"
                    required
                  />
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              <button type="submit" className="btn btn-primary btn-lg">
                Next: Add Patient Details →
              </button>
              <button type="button" className="btn btn-outline btn-lg" onClick={() => navigate('/patients')}>
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Step 2: Patient Details */}
        {step === 2 && (
          <form onSubmit={handleSubmit}>
            {/* Patient Info Banner */}
            <div className="card" style={{ background: '#f0f9ff', borderLeft: '4px solid #4f46e5', marginBottom: 20 }}>
              <div style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{ 
                  width: 50, height: 50, borderRadius: '50%', 
                  background: '#4f46e5', color: '#fff',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 20, fontWeight: 600
                }}>
                  {account.first_name.charAt(0)}{account.last_name.charAt(0)}
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: 18 }}>{account.first_name} {account.last_name}</h3>
                  <p style={{ margin: 0, color: '#666', fontSize: 14 }}>
                    {account.email && <span>{account.email}</span>}
                    {account.email && account.phone && <span> • </span>}
                    {account.phone && <span>{account.phone}</span>}
                  </p>
                </div>
                <button 
                  type="button" 
                  className="btn btn-outline btn-sm" 
                  style={{ marginLeft: 'auto' }}
                  onClick={() => setStep(1)}
                >
                  Edit Account
                </button>
              </div>
            </div>

            <div className="card">
              <div className="card-header"><h3>Personal Information</h3></div>
              <div className="form-row">
                <div className="form-group">
                  <label className="required">Date of Birth</label>
                  <input 
                    type="date" 
                    name="date_of_birth" 
                    className="form-control" 
                    value={form.date_of_birth} 
                    onChange={handleChange} 
                    required 
                  />
                </div>
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
              </div>
              <div className="form-row">
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
                <div className="form-group">
                  <label>National ID (Aadhaar)</label>
                  <input name="national_id" className="form-control" value={form.national_id} onChange={handleChange} placeholder="Enter Aadhaar number" />
                </div>
                <div className="form-group">
                  <label>Hospital ID</label>
                  <input name="hospital_id" className="form-control" value={form.hospital_id} onChange={handleChange} placeholder="If applicable" />
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-header"><h3>Address</h3></div>
              <div className="form-row">
                <div className="form-group"><label>Address Line 1</label><input name="address_line1" className="form-control" value={form.address_line1} onChange={handleChange} placeholder="Street address" /></div>
                <div className="form-group"><label>Address Line 2</label><input name="address_line2" className="form-control" value={form.address_line2} onChange={handleChange} placeholder="Apartment, suite, etc." /></div>
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
                <div className="form-group"><label>Name</label><input name="emergency_contact_name" className="form-control" value={form.emergency_contact_name} onChange={handleChange} placeholder="Contact person name" /></div>
                <div className="form-group"><label>Phone</label><input name="emergency_contact_phone" className="form-control" value={form.emergency_contact_phone} onChange={handleChange} placeholder="Contact phone" /></div>
                <div className="form-group"><label>Relation</label><input name="emergency_contact_relation" className="form-control" value={form.emergency_contact_relation} onChange={handleChange} placeholder="e.g. Spouse, Parent" /></div>
              </div>
            </div>

            <div className="card">
              <div className="card-header"><h3>Insurance (Optional)</h3></div>
              <div className="form-row">
                <div className="form-group"><label>Provider</label><input name="provider_name" className="form-control" value={insurance.provider_name} onChange={handleInsuranceChange} placeholder="Insurance company" /></div>
                <div className="form-group"><label>Policy Number</label><input name="policy_number" className="form-control" value={insurance.policy_number} onChange={handleInsuranceChange} /></div>
                <div className="form-group"><label>Plan Type</label><input name="plan_type" className="form-control" value={insurance.plan_type} onChange={handleInsuranceChange} placeholder="e.g. Family Floater" /></div>
              </div>
              <div className="form-row">
                <div className="form-group"><label>Coverage Start</label><input type="date" name="coverage_start" className="form-control" value={insurance.coverage_start} onChange={handleInsuranceChange} /></div>
                <div className="form-group"><label>Coverage End</label><input type="date" name="coverage_end" className="form-control" value={insurance.coverage_end} onChange={handleInsuranceChange} /></div>
                <div className="form-group"><label>Max Coverage (₹)</label><input type="number" name="max_coverage_amount" className="form-control" value={insurance.max_coverage_amount} onChange={handleInsuranceChange} /></div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              <button type="button" className="btn btn-outline btn-lg" onClick={() => setStep(1)}>
                ← Back
              </button>
              <button type="submit" className="btn btn-primary btn-lg" disabled={loading}>
                {loading ? 'Registering...' : 'Register Patient'}
              </button>
              <button type="button" className="btn btn-outline btn-lg" onClick={() => navigate('/patients')}>
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    </>
  );
};

export default PatientRegister;
