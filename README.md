# Hospital Patient Portal & Management System

A production-style Hospital Patient Portal and Hospital Management System built with React.js, Python Flask, and SQLite.

## Architecture

- **Frontend**: React.js (hooks, context API, protected routes)
- **Backend**: Python Flask (REST API, blueprints)
- **Database**: SQLite
- **Auth**: JWT-based authentication with role-based access control

## Roles

| Role    | Description |
|---------|-------------|
| Admin   | Full system access, user management, audit logs |
| Doctor  | View patients, add clinical data, prescriptions, reports |
| Staff   | Create patients, manage appointments, billing, uploads |
| Patient | View own records, appointments, reports, bills |

> **Important**: Patients cannot self-register. Only staff/admin can create patient accounts.

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm 9+

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python run.py
```

The backend starts on `http://localhost:5000`.

On first run, the database is automatically initialized with schema and seed data.

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

The frontend starts on `http://localhost:3000`.

### Default Login Credentials

| Role    | Username       | Password     |
|---------|----------------|--------------|
| Admin   | admin          | Admin@123    |
| Doctor  | dr.sharma      | Doctor@123   |
| Doctor  | dr.patel       | Doctor@123   |
| Staff   | staff1         | Staff@123    |
| Staff   | staff2         | Staff@123    |
| Patient | PAT-00001      | Patient@123  |
| Patient | PAT-00002      | Patient@123  |

## API Documentation

### Authentication
- `POST /api/auth/login` — Login (returns JWT)
- `POST /api/auth/change-password` — Change password
- `GET  /api/auth/me` — Get current user profile

### Users (Admin)
- `GET    /api/users` — List all users
- `POST   /api/users` — Create user
- `PUT    /api/users/:id` — Update user
- `DELETE /api/users/:id` — Deactivate user

### Patients
- `GET    /api/patients` — List patients
- `POST   /api/patients` — Create patient (Staff/Admin)
- `GET    /api/patients/:id` — Get patient details
- `PUT    /api/patients/:id` — Update patient

### Visits & Encounters
- `GET    /api/visits?patient_id=` — List visits
- `POST   /api/visits` — Create visit
- `PUT    /api/visits/:id` — Update visit

### Clinical Data
- `GET/POST   /api/diagnoses?patient_id=`
- `GET/POST   /api/vitals?patient_id=`
- `GET/POST   /api/allergies?patient_id=`
- `GET/POST   /api/clinical-notes?visit_id=`

### Prescriptions
- `GET    /api/prescriptions?patient_id=`
- `POST   /api/prescriptions`
- `GET    /api/prescriptions/:id`

### Reports & Documents
- `GET    /api/reports?patient_id=`
- `POST   /api/reports` (multipart)
- `GET    /api/reports/:id`
- `GET    /api/reports/files/:file_id/download`

### Appointments
- `GET    /api/appointments`
- `POST   /api/appointments`
- `PUT    /api/appointments/:id`

### Billing
- `GET    /api/invoices?patient_id=`
- `POST   /api/invoices`
- `GET    /api/invoices/:id`
- `POST   /api/invoices/:id/items`
- `PUT    /api/invoices/:id/payment`

### Notifications
- `GET    /api/notifications`
- `PUT    /api/notifications/:id/read`

### Audit Logs (Admin)
- `GET    /api/audit-logs`

### Dashboard
- `GET    /api/dashboard` — Role-specific dashboard data

## Project Structure

```
hosp/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask app factory
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # DB connection helpers
│   │   ├── middleware.py        # JWT auth middleware
│   │   ├── utils.py             # Utility functions
│   │   ├── seed.py              # Seed data
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── patients.py
│   │       ├── visits.py
│   │       ├── clinical.py
│   │       ├── prescriptions.py
│   │       ├── reports.py
│   │       ├── appointments.py
│   │       ├── billing.py
│   │       ├── notifications.py
│   │       ├── audit.py
│   │       └── dashboard.py
│   ├── migrations/
│   │   └── schema.sql
│   ├── uploads/
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   │   └── axios.js
│   │   ├── context/
│   │   │   └── AuthContext.js
│   │   ├── components/
│   │   │   ├── Layout/
│   │   │   ├── Common/
│   │   │   └── ProtectedRoute.js
│   │   ├── pages/
│   │   │   ├── Login.js
│   │   │   ├── Dashboard/
│   │   │   ├── Patients/
│   │   │   ├── Appointments/
│   │   │   ├── Clinical/
│   │   │   ├── Reports/
│   │   │   ├── Prescriptions/
│   │   │   ├── Billing/
│   │   │   ├── Users/
│   │   │   └── AuditLogs/
│   │   ├── App.js
│   │   └── index.js
│   └── package.json
└── README.md
```
