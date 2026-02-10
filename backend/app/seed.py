import bcrypt
from .database import get_db, query_db, execute_db


def seed_data():
    """Seed the database with initial data."""
    # Check if already seeded
    existing = query_db("SELECT COUNT(*) as cnt FROM roles", one=True)
    if existing and existing['cnt'] > 0:
        print("Database already seeded. Skipping.")
        return

    conn = get_db()
    try:
        # Roles
        conn.execute("INSERT INTO roles (name, description) VALUES ('Admin', 'System Administrator')")
        conn.execute("INSERT INTO roles (name, description) VALUES ('Doctor', 'Medical Doctor')")
        conn.execute("INSERT INTO roles (name, description) VALUES ('Staff', 'Hospital Staff')")
        conn.execute("INSERT INTO roles (name, description) VALUES ('Patient', 'Hospital Patient')")

        # Departments
        departments = [
            ('General Medicine', 'General medical care and internal medicine'),
            ('Cardiology', 'Heart and cardiovascular system'),
            ('Orthopedics', 'Bones, joints, and musculoskeletal system'),
            ('Pediatrics', 'Medical care for children'),
            ('Neurology', 'Brain and nervous system'),
            ('Dermatology', 'Skin conditions'),
            ('ENT', 'Ear, nose, and throat'),
            ('Ophthalmology', 'Eye care'),
            ('Radiology', 'Imaging and diagnostics'),
            ('Pathology', 'Laboratory diagnostics'),
            ('Emergency Medicine', 'Emergency and trauma care'),
            ('Gynecology', 'Women reproductive health'),
        ]
        for name, desc in departments:
            conn.execute("INSERT INTO departments (name, description) VALUES (?, ?)", [name, desc])

        # Helper to hash password
        def pw(plain):
            return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Admin user
        conn.execute(
            "INSERT INTO users (username, password_hash, email, phone, role_id, must_change_password) VALUES (?,?,?,?,1,0)",
            ['admin', pw('Admin@123'), 'baveshchowdary1@gmail.com', '']
        )

        # Sample Doctors (user accounts + doctor profiles)
        doctor_data = [
            ('dr.sharma', 'Doctor@123', 'sharma@hospital.com', '9876543210', 'Rajesh', 'Sharma', 'Cardiologist', 'MD, DM Cardiology', 2, 'LIC-1001', 500),
            ('dr.patel', 'Doctor@123', 'patel@hospital.com', '9876543211', 'Priya', 'Patel', 'General Physician', 'MBBS, MD Medicine', 1, 'LIC-1002', 300),
            ('dr.kumar', 'Doctor@123', 'kumar@hospital.com', '9876543212', 'Anil', 'Kumar', 'Orthopedic Surgeon', 'MS Orthopedics', 3, 'LIC-1003', 600),
            ('dr.reddy', 'Doctor@123', 'reddy@hospital.com', '9876543213', 'Sujatha', 'Reddy', 'Pediatrician', 'MD Pediatrics', 4, 'LIC-1004', 400),
            ('dr.singh', 'Doctor@123', 'singh@hospital.com', '9876543214', 'Harpreet', 'Singh', 'Neurologist', 'DM Neurology', 5, 'LIC-1005', 700),
            ('dr.gupta', 'Doctor@123', 'gupta@hospital.com', '9876543215', 'Meena', 'Gupta', 'Dermatologist', 'MD Dermatology', 6, 'LIC-1006', 350),
            ('dr.wilson', 'Doctor@123', 'wilson@hospital.com', '9876543216', 'David', 'Wilson', 'ENT Specialist', 'MS ENT', 7, 'LIC-1007', 450),
            ('dr.joseph', 'Doctor@123', 'joseph@hospital.com', '9876543217', 'Mary', 'Joseph', 'Ophthalmologist', 'MS Ophthalmology', 8, 'LIC-1008', 500),
            ('dr.khan', 'Doctor@123', 'khan@hospital.com', '9876543218', 'Imran', 'Khan', 'Radiologist', 'MD Radiology', 9, 'LIC-1009', 400),
            ('dr.ravi', 'Doctor@123', 'ravi@hospital.com', '9876543219', 'Lakshmi', 'Ravi', 'Emergency Physician', 'MD Emergency Medicine', 11, 'LIC-1010', 500),
            ('dr.nair', 'Doctor@123', 'nair@hospital.com', '9876543220', 'Suresh', 'Nair', 'Gynecologist', 'MS Gynecology', 12, 'LIC-1011', 550),
            ('dr.das', 'Doctor@123', 'das@hospital.com', '9876543221', 'Ananya', 'Das', 'Pathologist', 'MD Pathology', 10, 'LIC-1012', 350),
        ]

        for i, (username, password, email, phone, fname, lname, spec, qual, dept_id, lic, fee) in enumerate(doctor_data):
            conn.execute(
                "INSERT INTO users (username, password_hash, email, phone, role_id, must_change_password, first_name, last_name) VALUES (?,?,?,?,2,0,?,?)",
                [username, pw(password), email, phone, fname, lname]
            )
            user_id = i + 2  # admin is 1, doctors start from 2
            conn.execute(
                "INSERT INTO doctors (user_id, employee_id, first_name, last_name, specialization, qualification, department_id, license_number, consultation_fee) VALUES (?,?,?,?,?,?,?,?,?)",
                [user_id, f'EMP-{1001+i}', fname, lname, spec, qual, dept_id, lic, fee]
            )

        conn.commit()
        print("Database seeded successfully with sample data.")

    except Exception as e:
        conn.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        conn.close()
