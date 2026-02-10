import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { billingAPI, patientsAPI } from '../../api/axios';
import Topbar from '../../components/Layout/Topbar';
import { Loading } from '../../components/Common';

const emptyItem = { item_type: 'Consultation', description: '', quantity: 1, unit_price: '' };

const InvoiceCreate = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [patients, setPatients] = useState([]);
  const [loadingPatients, setLoadingPatients] = useState(true);

  const [form, setForm] = useState({
    patient_id: searchParams.get('patient_id') || '',
    visit_id: '',
    due_date: '',
    notes: '',
  });
  const [items, setItems] = useState([{ ...emptyItem }]);

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const res = await patientsAPI.list({ per_page: 500 });
        setPatients(res.data.patients || []);
      } catch {}
      setLoadingPatients(false);
    };
    fetchPatients();
  }, []);

  const handleItemChange = (index, field, value) => {
    setItems(prev => prev.map((item, i) => i === index ? { ...item, [field]: value } : item));
  };

  const addItem = () => setItems(prev => [...prev, { ...emptyItem }]);
  const removeItem = (index) => setItems(prev => prev.filter((_, i) => i !== index));

  const getTotal = () => items.reduce((sum, item) => sum + (parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0), 0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!form.patient_id) {
      setError('Please select a patient');
      return;
    }

    const validItems = items.filter(i => i.description && i.unit_price);
    if (validItems.length === 0) {
      setError('Please add at least one line item with description and unit price');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        patient_id: parseInt(form.patient_id),
        visit_id: form.visit_id ? parseInt(form.visit_id) : null,
        due_date: form.due_date || null,
        notes: form.notes || null,
        items: validItems.map(i => ({
          item_type: i.item_type,
          description: i.description,
          quantity: parseInt(i.quantity) || 1,
          unit_price: parseFloat(i.unit_price),
        })),
      };

      const res = await billingAPI.create(payload);
      navigate(`/billing/${res.data.id}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create invoice');
    }
    setSaving(false);
  };

  return (
    <>
      <Topbar title="Create New Invoice" />
      <div className="page-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
          <button className="btn btn-outline" onClick={() => navigate('/billing')}>← Back</button>
        </div>

        {error && (
          <div style={{ background: '#fee2e2', color: '#dc2626', padding: '10px 16px', borderRadius: 8, marginBottom: 16 }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Patient Selection */}
          <div className="card">
            <div className="card-header"><h3>Invoice Details</h3></div>
            <div style={{ padding: 20 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div className="form-group">
                  <label className="required">Patient</label>
                  {loadingPatients ? <Loading /> : (
                    <select
                      className="form-control"
                      value={form.patient_id}
                      onChange={e => setForm(p => ({ ...p, patient_id: e.target.value }))}
                      required
                    >
                      <option value="">-- Select Patient --</option>
                      {patients.map(p => (
                        <option key={p.id} value={p.id}>
                          {p.first_name} {p.last_name} ({p.mrn})
                        </option>
                      ))}
                    </select>
                  )}
                </div>
                <div className="form-group">
                  <label>Visit ID (optional)</label>
                  <input
                    type="number"
                    className="form-control"
                    value={form.visit_id}
                    onChange={e => setForm(p => ({ ...p, visit_id: e.target.value }))}
                    placeholder="Link to a visit"
                  />
                </div>
                <div className="form-group">
                  <label>Due Date</label>
                  <input
                    type="date"
                    className="form-control"
                    value={form.due_date}
                    onChange={e => setForm(p => ({ ...p, due_date: e.target.value }))}
                  />
                </div>
                <div className="form-group">
                  <label>Notes</label>
                  <input
                    className="form-control"
                    value={form.notes}
                    onChange={e => setForm(p => ({ ...p, notes: e.target.value }))}
                    placeholder="Optional notes"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Line Items */}
          <div className="card">
            <div className="card-header">
              <h3>Line Items</h3>
              <button type="button" className="btn btn-primary btn-sm" onClick={addItem}>+ Add Item</button>
            </div>
            <div style={{ padding: 20 }}>
              {items.map((item, index) => (
                <div key={index} style={{ display: 'grid', gridTemplateColumns: '150px 1fr 80px 120px 40px', gap: 10, marginBottom: 12, alignItems: 'end' }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    {index === 0 && <label>Category</label>}
                    <select className="form-control" value={item.item_type} onChange={e => handleItemChange(index, 'item_type', e.target.value)}>
                      {['Consultation', 'Lab', 'Scan', 'Procedure', 'Medication', 'Room', 'Other'].map(t => (
                        <option key={t} value={t}>{t}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    {index === 0 && <label className="required">Description</label>}
                    <input className="form-control" value={item.description} onChange={e => handleItemChange(index, 'description', e.target.value)} placeholder="Item description" required />
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    {index === 0 && <label>Qty</label>}
                    <input type="number" min="1" className="form-control" value={item.quantity} onChange={e => handleItemChange(index, 'quantity', e.target.value)} />
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    {index === 0 && <label className="required">Unit Price (₹)</label>}
                    <input type="number" step="0.01" min="0" className="form-control" value={item.unit_price} onChange={e => handleItemChange(index, 'unit_price', e.target.value)} placeholder="0.00" required />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', paddingBottom: 2 }}>
                    {items.length > 1 && (
                      <button type="button" className="btn btn-outline btn-sm" style={{ color: '#dc2626', borderColor: '#dc2626', padding: '4px 8px' }} onClick={() => removeItem(index)}>✕</button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Total & Submit */}
          <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 20 }}>
            <div style={{ fontSize: 18, fontWeight: 600 }}>
              Total: ₹{getTotal().toLocaleString()}
            </div>
            <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>
              {saving ? 'Creating Invoice...' : 'Create Invoice'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
};

export default InvoiceCreate;
