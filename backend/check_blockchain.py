import sqlite3

conn = sqlite3.connect('hospital.db')
conn.row_factory = sqlite3.Row

# Check what tables exist
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
table_names = [t[0] for t in tables]
print('=== EXISTING TABLES ===')
print(table_names)
print()

print('=== BLOCKCHAIN RECORDS (record_blockchain_map) ===')
records = conn.execute('SELECT * FROM record_blockchain_map ORDER BY created_at DESC LIMIT 20').fetchall()
if records:
    for r in records:
        ipfs = r['ipfs_hash'] if r['ipfs_hash'] else 'None'
        print(f"Type: {r['record_type']}, ID: {r['record_id']}, Hash: {r['record_hash'][:30]}..., IPFS: {ipfs}, TxID: {r['transaction_id'] or 'None'}")
else:
    print('No blockchain records found')

print()
print('=== BLOCKCHAIN AUDIT LOG ===')
txns = conn.execute('SELECT * FROM blockchain_audit_log ORDER BY created_at DESC LIMIT 10').fetchall()
if txns:
    for t in txns:
        print(f"Operation: {t['operation_type']}, Type: {t['record_type']}, ID: {t['record_id']}, Status: {t['status']}, Result: {t['verification_result'] or 'N/A'}")
else:
    print('No audit log entries found')

print()
print('=== REPORTS WITH FILES ===')
reports = conn.execute('''
    SELECT r.id, r.patient_id, r.title, rf.file_path, rf.original_name 
    FROM reports r 
    LEFT JOIN report_files rf ON r.id = rf.report_id 
    ORDER BY r.id DESC LIMIT 10
''').fetchall()
if reports:
    for r in reports:
        print(f"Report ID: {r['id']}, Patient: {r['patient_id']}, Title: {r['title']}, File: {r['original_name'] or 'None'}")
else:
    print('No reports found')

conn.close()
