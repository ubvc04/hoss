import os
import uuid
import re
from datetime import datetime
from .config import Config


def allowed_file(filename):
    """Check if a file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def save_upload(file, subfolder='general'):
    """Save an uploaded file and return the saved filename and path."""
    if not file or not file.filename:
        return None, None, None, None

    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'bin'
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    folder = os.path.join(Config.UPLOAD_FOLDER, subfolder)
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, safe_name)
    file.save(file_path)
    file_size = os.path.getsize(file_path)
    return safe_name, os.path.join(subfolder, safe_name), file_size, file.content_type or 'application/octet-stream'


def generate_mrn():
    """Generate a unique MRN like PAT-00001."""
    from .database import query_db
    row = query_db("SELECT mrn FROM patients ORDER BY id DESC LIMIT 1", one=True)
    if row and row['mrn']:
        num = int(row['mrn'].split('-')[1]) + 1
    else:
        num = 1
    return f"PAT-{num:05d}"


def generate_invoice_number():
    """Generate unique invoice number like INV-20260101-001."""
    from .database import query_db
    today = datetime.now().strftime('%Y%m%d')
    row = query_db("SELECT invoice_number FROM invoices WHERE invoice_number LIKE ? ORDER BY id DESC LIMIT 1",
                   [f"INV-{today}-%"], one=True)
    if row:
        seq = int(row['invoice_number'].split('-')[2]) + 1
    else:
        seq = 1
    return f"INV-{today}-{seq:03d}"


def validate_required(data, fields):
    """Validate that required fields are present and non-empty."""
    missing = [f for f in fields if not data.get(f)]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    return True, None


def validate_email(email):
    """Basic email validation."""
    if not email:
        return True
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone):
    """Basic phone validation."""
    if not phone:
        return True
    return bool(re.match(r'^[\d\s\+\-\(\)]{7,20}$', phone))


def paginate_query(base_query, args, page=1, per_page=20):
    """Add pagination to a query."""
    offset = (page - 1) * per_page
    return f"{base_query} LIMIT {per_page} OFFSET {offset}", args


def parse_pagination(request):
    """Parse page and per_page from request args."""
    page = max(1, request.args.get('page', 1, type=int))
    per_page = min(100, max(1, request.args.get('per_page', 20, type=int)))
    return page, per_page
