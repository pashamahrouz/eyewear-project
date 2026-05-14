from flask import Flask, request, jsonify, send_from_directory, send_file
import sqlite3, uuid, os, json
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'db', 'eyewear.db')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

ALLOWED_EXT = {'pdf', 'jpg', 'jpeg', 'png'}

# ─── CORS (manual, no extra lib) ──────────────────────────────────────────────
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return resp

@app.after_request
def after_request(resp):
    return add_cors(resp)

@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        return add_cors(app.make_default_options_response())

def cors(f):
    return f

# ─── DB INIT ──────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS wholesale_requests (
            id TEXT PRIMARY KEY,
            store_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            license_file TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            updated_at TEXT,
            admin_note TEXT
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            type TEXT NOT NULL,
            retail_price INTEGER NOT NULL,
            wholesale_price INTEGER NOT NULL,
            stock INTEGER DEFAULT 100,
            active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            store_name TEXT,
            phone TEXT,
            product_ids TEXT,
            quantities TEXT,
            type TEXT DEFAULT 'retail',
            total INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL
        );
    ''')
    # Seed products if empty
    count = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    if count == 0:
        products = [
            ('Wayfarer Classic','Ray-Ban','sunny',2850000,1950000,200),
            ('RB5154 Clubmaster','Ray-Ban','medical',3100000,2150000,150),
            ('Holbrook XL','Oakley','sunny',4200000,2950000,80),
            ('Sylas Polarized','Oakley','sunny',3850000,2650000,120),
            ('GG0010S Gold','Gucci','sunny',12500000,8750000,30),
            ('GG0027O Optical','Gucci','medical',10800000,7500000,25),
            ('PR 17WS Runway','Prada','sunny',11200000,7800000,35),
            ('VPR 14Y Optical','Prada','medical',9500000,6600000,40),
            ('Champion 8012/S','Carrera','sunny',2450000,1700000,180),
            ('Carrera 1043/S','Carrera','sunny',2150000,1480000,200),
            ('CA6000 Optical','Carrera','medical',1980000,1350000,160),
            ('Aviator Large','Ray-Ban','sunny',3450000,2400000,130),
        ]
        conn.executemany(
            'INSERT INTO products (name,brand,type,retail_price,wholesale_price,stock) VALUES (?,?,?,?,?,?)',
            products
        )
    conn.commit()
    conn.close()

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def format_price(p):
    return f"{p:,}"

def fmt_req(row):
    return {
        'id': row['id'],
        'store_name': row['store_name'],
        'phone': row['phone'],
        'license_file': row['license_file'],
        'status': row['status'],
        'created_at': row['created_at'],
        'updated_at': row['updated_at'],
        'admin_note': row['admin_note'],
    }

# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET','OPTIONS'])
@cors
def index():
    return jsonify({'status': 'ok', 'message': 'Optic Vision API v1.0'})

# Products
@app.route('/api/products', methods=['GET','OPTIONS'])
@cors
def get_products():
    conn = get_db()
    rows = conn.execute('SELECT * FROM products WHERE active=1').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# Wholesale request submit
@app.route('/api/wholesale/apply', methods=['POST','OPTIONS'])
@cors
def apply_wholesale():
    if request.method == 'OPTIONS':
        return jsonify({})
    
    store_name = request.form.get('store_name', '').strip()
    phone = request.form.get('phone', '').strip()

    if not store_name or not phone:
        return jsonify({'error': 'نام فروشگاه و شماره تماس الزامی است'}), 400

    file_path = None
    if 'license' in request.files:
        f = request.files['license']
        if f and f.filename:
            if not allowed_file(f.filename):
                return jsonify({'error': 'فرمت فایل مجاز نیست. فقط PDF، JPG یا PNG قبول می‌شود'}), 400
            ext = f.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            f.save(os.path.join(UPLOAD_DIR, filename))
            file_path = filename

    req_id = str(uuid.uuid4())
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db()
    conn.execute(
        'INSERT INTO wholesale_requests (id,store_name,phone,license_file,created_at) VALUES (?,?,?,?,?)',
        (req_id, store_name, phone, file_path, now)
    )
    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'id': req_id,
        'message': 'درخواست شما ثبت شد. حداکثر ۲۴ ساعت بررسی می‌شود.'
    })

# Admin: list all requests
@app.route('/api/admin/requests', methods=['GET','OPTIONS'])
@cors
def admin_list():
    status = request.args.get('status', 'all')
    conn = get_db()
    if status == 'all':
        rows = conn.execute('SELECT * FROM wholesale_requests ORDER BY created_at DESC').fetchall()
    else:
        rows = conn.execute('SELECT * FROM wholesale_requests WHERE status=? ORDER BY created_at DESC', (status,)).fetchall()
    conn.close()
    return jsonify([fmt_req(r) for r in rows])

# Admin: approve/reject
@app.route('/api/admin/requests/<req_id>', methods=['PUT','OPTIONS'])
@cors
def admin_update(req_id):
    if request.method == 'OPTIONS':
        return jsonify({})
    data = request.get_json() or {}
    status = data.get('status')
    note = data.get('note', '')
    
    if status not in ('approved', 'rejected', 'pending'):
        return jsonify({'error': 'وضعیت نامعتبر'}), 400

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db()
    conn.execute(
        'UPDATE wholesale_requests SET status=?, admin_note=?, updated_at=? WHERE id=?',
        (status, note, now, req_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# Download license file
@app.route('/api/admin/file/<filename>', methods=['GET'])
def get_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# Stats for admin dashboard
@app.route('/api/admin/stats', methods=['GET','OPTIONS'])
@cors
def admin_stats():
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) FROM wholesale_requests').fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM wholesale_requests WHERE status='pending'").fetchone()[0]
    approved = conn.execute("SELECT COUNT(*) FROM wholesale_requests WHERE status='approved'").fetchone()[0]
    rejected = conn.execute("SELECT COUNT(*) FROM wholesale_requests WHERE status='rejected'").fetchone()[0]
    products = conn.execute('SELECT COUNT(*) FROM products WHERE active=1').fetchone()[0]
    conn.close()
    return jsonify({
        'total_requests': total,
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'products': products
    })

if __name__ == '__main__':
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    init_db()
    print("✅ Optic Vision Backend starting on http://localhost:5000")
    app.run(debug=True, port=5000)
add backend folder
