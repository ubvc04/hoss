"""
Backfill existing records to blockchain for patient 8 (PAT-00008)
"""
from app.blockchain import get_blockchain_service
from app.database import query_db, dict_from_row

bs = get_blockchain_service()
patient_id = 8

print(f"=== Backfilling blockchain records for patient {patient_id} ===\n")

# Store patient
patient = query_db('SELECT * FROM patients WHERE id=?', [patient_id], one=True)
if patient:
    result = bs.store_patient(patient_id, dict_from_row(patient))
    print(f"Patient: {result['success']}, Hash: {result['hash'][:30]}...")
    print(f"  TxID: {result['transactionId']}")

# Store all visits for patient
print("\n--- Visits ---")
visits = query_db('SELECT * FROM visits WHERE patient_id=?', [patient_id])
for v in visits:
    result = bs.store_visit(v['id'], patient_id, dict_from_row(v))
    print(f"Visit {v['id']}: {result['success']}, Hash: {result['hash'][:30]}...")

# Store all prescriptions for patient
print("\n--- Prescriptions ---")
prescriptions = query_db('SELECT * FROM prescriptions WHERE patient_id=?', [patient_id])
for p in prescriptions:
    # Get medications for this prescription
    medications = query_db('SELECT * FROM medications WHERE prescription_id=?', [p['id']])
    meds_list = [dict_from_row(m) for m in medications] if medications else []
    result = bs.store_prescription(p['id'], patient_id, dict_from_row(p), meds_list)
    print(f"Prescription {p['id']}: {result['success']}, Hash: {result['hash'][:30]}...")

# Store all appointments for patient
print("\n--- Appointments ---")
appointments = query_db('SELECT * FROM appointments WHERE patient_id=?', [patient_id])
for a in appointments:
    result = bs.store_appointment(a['id'], patient_id, dict_from_row(a))
    print(f"Appointment {a['id']}: {result['success']}, Hash: {result['hash'][:30]}...")

# Store all invoices for patient
print("\n--- Invoices ---")
invoices = query_db('SELECT * FROM invoices WHERE patient_id=?', [patient_id])
for i in invoices:
    # Get invoice items
    items = query_db('SELECT * FROM invoice_items WHERE invoice_id=?', [i['id']])
    items_list = [dict_from_row(item) for item in items] if items else []
    result = bs.store_invoice(i['id'], patient_id, dict_from_row(i), items_list)
    print(f"Invoice {i['id']}: {result['success']}, Hash: {result['hash'][:30]}...")

# Store reports for patient (with IPFS upload)
print("\n--- Reports (with IPFS) ---")
reports = query_db('SELECT * FROM reports WHERE patient_id=?', [patient_id])
for r in reports:
    report_data = dict_from_row(r)
    # Get file if exists
    file_rec = query_db('SELECT * FROM report_files WHERE report_id=?', [r['id']], one=True)
    file_data = None
    filename = None
    if file_rec:
        filepath = file_rec['file_path']
        filename = file_rec['original_name']
        # Try different path formats
        import os
        # Normalize the path
        normalized_path = filepath.replace('\\', '/')
        possible_paths = [
            filepath,
            os.path.join('uploads', filepath),
            os.path.join('uploads', normalized_path),
            'uploads/' + normalized_path,
        ]
        for path in possible_paths:
            path = path.replace('\\', os.sep).replace('/', os.sep)
            if os.path.exists(path):
                try:
                    with open(path, 'rb') as f:
                        file_data = f.read()
                    print(f"  Found file: {filename} ({len(file_data)} bytes)")
                    break
                except Exception as e:
                    pass
        if not file_data:
            print(f"  File not found: {filepath}")
    
    result = bs.store_report(r['id'], patient_id, report_data, 
                             file_data=file_data, filename=filename, upload_to_ipfs=True)
    if result.get('success'):
        print(f"Report {r['id']}: Success, Hash: {result.get('hash', 'N/A')[:30]}...")
        if result.get('ipfsHash'):
            print(f"  IPFS Hash: {result['ipfsHash']}")
    else:
        print(f"Report {r['id']}: Failed - {result.get('error', 'Unknown error')}")

print("\n=== Backfill complete! ===")
print("\nRun 'python check_blockchain.py' to see all records.")
