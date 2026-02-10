import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor — attach JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ============ AUTH ============
export const authAPI = {
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
  changePassword: (data) => api.post('/auth/change-password', data),
  signup: (data) => api.post('/auth/signup', data),
  forgotPassword: (data) => api.post('/auth/forgot-password', data),
  resetPassword: (data) => api.post('/auth/reset-password', data),
  getRoles: () => api.get('/auth/roles'),
};

// ============ USERS ============
export const usersAPI = {
  list: (params) => api.get('/users', { params }),
  getAll: (params) => api.get('/users', { params }),
  create: (data) => api.post('/users', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  deactivate: (id) => api.delete(`/users/${id}`),
  roles: () => api.get('/users/roles'),
};

// ============ PATIENTS ============
export const patientsAPI = {
  list: (params) => api.get('/patients', { params }),
  getAll: (params) => api.get('/patients', { params }),
  get: (id) => api.get(`/patients/${id}`),
  create: (data) => api.post('/patients', data),
  update: (id, data) => api.put(`/patients/${id}`, data),
  departments: () => api.get('/patients/departments'),
  getDepartments: () => api.get('/patients/departments'),
  doctors: (params) => api.get('/patients/doctors', { params }),
  getDoctors: (params) => api.get('/patients/doctors', { params }),
};

// ============ VISITS ============
export const visitsAPI = {
  list: (params) => api.get('/visits', { params }),
  getAll: (params) => api.get('/visits', { params }),
  get: (id) => api.get(`/visits/${id}`),
  create: (data) => api.post('/visits', data),
  update: (id, data) => api.put(`/visits/${id}`, data),
};

// ============ CLINICAL ============
export const clinicalAPI = {
  allergies: (params) => api.get('/allergies', { params }),
  createAllergy: (data) => api.post('/allergies', data),
  vitals: (params) => api.get('/vitals', { params }),
  createVitals: (data) => api.post('/vitals', data),
  notes: (params) => api.get('/clinical-notes', { params }),
  createNote: (data) => api.post('/clinical-notes', data),
};

// ============ PRESCRIPTIONS ============
export const prescriptionsAPI = {
  list: (params) => api.get('/prescriptions', { params }),
  getAll: (params) => api.get('/prescriptions', { params }),
  get: (id) => api.get(`/prescriptions/${id}`),
  create: (data) => api.post('/prescriptions', data),
};

// ============ REPORTS ============
export const reportsAPI = {
  list: (params) => api.get('/reports', { params }),
  getAll: (params) => api.get('/reports', { params }),
  get: (id) => api.get(`/reports/${id}`),
  create: (formData) => api.post('/reports', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  verify: (id, data) => api.put(`/reports/${id}/verify`, data),
  downloadFile: (fileId) => api.get(`/reports/files/${fileId}/download`, { responseType: 'blob' }),
};

// ============ APPOINTMENTS ============
export const appointmentsAPI = {
  list: (params) => api.get('/appointments', { params }),
  getAll: (params) => api.get('/appointments', { params }),
  get: (id) => api.get(`/appointments/${id}`),
  create: (data) => api.post('/appointments', data),
  update: (id, data) => api.put(`/appointments/${id}`, data),
};

// ============ BILLING ============
export const billingAPI = {
  list: (params) => api.get('/invoices', { params }),
  getAll: (params) => api.get('/invoices', { params }),
  get: (id) => api.get(`/invoices/${id}`),
  getById: (id) => api.get(`/invoices/${id}`),
  create: (data) => api.post('/invoices', data),
  addItems: (id, data) => api.post(`/invoices/${id}/items`, data),
  updatePayment: (id, data) => api.put(`/invoices/${id}/payment`, data),
  recordPayment: (id, data) => api.put(`/invoices/${id}/payment`, data),
  uploadFiles: (id, formData) => api.post(`/invoices/${id}/files`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  downloadFile: (fileId) => api.get(`/invoices/files/${fileId}/download`, { responseType: 'blob' }),
  deleteFile: (invoiceId, fileId) => api.delete(`/invoices/${invoiceId}/files/${fileId}`),
};

// ============ NOTIFICATIONS ============
export const notificationsAPI = {
  list: (params) => api.get('/notifications', { params }),
  getAll: (params) => api.get('/notifications', { params }),
  markRead: (id) => api.put(`/notifications/${id}/read`),
  markAllRead: () => api.put('/notifications/read-all'),
};

// ============ AUDIT ============
export const auditAPI = {
  list: (params) => api.get('/audit-logs', { params }),
  getAll: (params) => api.get('/audit-logs', { params }),
};

// ============ DASHBOARD ============
export const dashboardAPI = {
  get: () => api.get('/dashboard'),
};

export default api;
