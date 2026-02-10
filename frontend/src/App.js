import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './components/Layout/AppLayout';

// Pages
import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Dashboard from './pages/Dashboard';
import PatientList from './pages/Patients/PatientList';
import PatientDetail from './pages/Patients/PatientDetail';
import PatientRegister from './pages/Patients/PatientRegister';
import AppointmentsPage from './pages/Appointments';
import VisitList from './pages/Visits/VisitList';
import VisitDetail from './pages/Visits/VisitDetail';
import ReportList from './pages/Reports/ReportList';
import ReportDetail from './pages/Reports/ReportDetail';
import PrescriptionList from './pages/Prescriptions/PrescriptionList';
import PrescriptionDetail from './pages/Prescriptions/PrescriptionDetail';
import InvoiceList from './pages/Billing/InvoiceList';
import InvoiceDetail from './pages/Billing/InvoiceDetail';
import UsersPage from './pages/Users';
import AuditLogsPage from './pages/AuditLogs';
import NotificationsPage from './pages/Notifications';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />

          {/* Protected routes inside layout */}
          <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            {/* Dashboard */}
            <Route path="/dashboard" element={<Dashboard />} />

            {/* Patients — admin, doctor, staff can list/view; admin & staff can register */}
            <Route path="/patients" element={
              <ProtectedRoute roles={['Admin', 'Doctor', 'Staff']}>
                <PatientList />
              </ProtectedRoute>
            } />
            <Route path="/patients/register" element={
              <ProtectedRoute roles={['Admin', 'Staff']}>
                <PatientRegister />
              </ProtectedRoute>
            } />
            <Route path="/patients/:id" element={
              <ProtectedRoute roles={['Admin', 'Doctor', 'Staff', 'Patient']}>
                <PatientDetail />
              </ProtectedRoute>
            } />

            {/* My Profile — for patients to view their own record */}
            <Route path="/my-profile" element={
              <ProtectedRoute roles={['Patient']}>
                <PatientDetail />
              </ProtectedRoute>
            } />
            <Route path="/clinical" element={
              <ProtectedRoute roles={['Patient']}>
                <PatientDetail />
              </ProtectedRoute>
            } />

            {/* Appointments — all roles */}
            <Route path="/appointments" element={<AppointmentsPage />} />

            {/* Visits */}
            <Route path="/visits" element={<VisitList />} />
            <Route path="/visits/:id" element={<VisitDetail />} />

            {/* Reports */}
            <Route path="/reports" element={<ReportList />} />
            <Route path="/reports/:id" element={<ReportDetail />} />

            {/* Prescriptions */}
            <Route path="/prescriptions" element={<PrescriptionList />} />
            <Route path="/prescriptions/:id" element={<PrescriptionDetail />} />

            {/* Billing */}
            <Route path="/billing" element={<InvoiceList />} />
            <Route path="/billing/:id" element={<InvoiceDetail />} />

            {/* Notifications */}
            <Route path="/notifications" element={<NotificationsPage />} />

            {/* Admin only */}
            <Route path="/users" element={
              <ProtectedRoute roles={['Admin']}>
                <UsersPage />
              </ProtectedRoute>
            } />
            <Route path="/audit-logs" element={
              <ProtectedRoute roles={['Admin']}>
                <AuditLogsPage />
              </ProtectedRoute>
            } />
          </Route>

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
      <ToastContainer position="top-right" autoClose={3000} />
    </AuthProvider>
  );
}

export default App;
