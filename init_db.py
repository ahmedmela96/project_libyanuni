import sqlite3
import os
import hashlib

DB_PATH = 'ehsan.db'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH) # Fresh start for v2.2 to ensure new schema is clean
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Users Table (Core Auth & Roles)
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL, -- admin, researcher, sharia_committee, finance
        name TEXT NOT NULL,
        status TEXT DEFAULT 'pending', -- pending, active, rejected
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # 2. Beneficiaries Table (Advanced v2.2)
    cursor.execute('''CREATE TABLE IF NOT EXISTS beneficiaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        national_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        gender TEXT, -- male/female
        family_status TEXT, -- married, widow, orphan...
        family_status_other TEXT, -- For custom 'Other' status text
        guardian TEXT, -- mother, father, brother...
        family_size INTEGER,
        income REAL,
        occupation TEXT,
        case_type TEXT, -- AR: نوع الحالة (e.g. Orphans, Widows...) assigned by researcher
        phone TEXT,
        address TEXT,
        status TEXT DEFAULT 'pending_research', -- pending_research, pending_sharia, approved, rejected
        researcher_notes TEXT,
        sharia_fatwa TEXT,
        need_score REAL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # 3. Aid Types (Lookup for financial aid)
    cursor.execute('''CREATE TABLE IF NOT EXISTS aid_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, -- e.g. Monthly, Emergency...
        amount REAL NOT NULL
    )''')

    # 4. Distributions (Financial Transactions)
    cursor.execute('''CREATE TABLE IF NOT EXISTS distributions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        beneficiary_id INTEGER,
        aid_id INTEGER,
        user_id INTEGER, -- Who processed it
        amount REAL,
        distribution_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(beneficiary_id) REFERENCES beneficiaries(id),
        FOREIGN KEY(aid_id) REFERENCES aid_types(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # 5. System Settings & Branding
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')

    # 6. Notifications System
    cursor.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_role TEXT, -- admin, researcher...
        message TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 7. Lookup Data (NEW v2.2 - Dynamic Lists for Admin)
    cursor.execute('''CREATE TABLE IF NOT EXISTS lookup_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL, -- family_status, case_type
        label TEXT NOT NULL,
        value TEXT NOT NULL UNIQUE
    )''')

    # 8. Audit Logs (NEW v2.2 - History/Timeline Tracking)
    cursor.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        beneficiary_id INTEGER,
        action TEXT NOT NULL, -- Registration, Visit, Fatwa, Payment
        notes TEXT,
        user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(beneficiary_id) REFERENCES beneficiaries(id)
    )''')

    # 9. Password Reset Requests (NEW v2.2)
    cursor.execute('''CREATE TABLE IF NOT EXISTS reset_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        status TEXT DEFAULT 'pending', -- pending, resolved
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # --- Initial Data Seeding ---

    # Default Admin
    cursor.execute("INSERT INTO users (username, password, role, name, status) VALUES (?, ?, ?, ?, ?)",
                   ('admin', hash_password('admin123'), 'admin', 'المدير العام', 'active'))

    # Default Settings
    settings = [
        ('org_name', 'منصة إحسان للأعمال الخيرية'),
        ('tax_id', 'EH-2026-LY'),
        ('org_motto', 'نحو عمل خيري مؤسسي ومنظم'),
        ('org_phone1', '+218 91 0000000'),
        ('org_phone2', '+218 92 0000000'),
        ('org_type', 'جمعية أهلية ليبية')
    ]
    cursor.executemany("INSERT INTO settings (key, value) VALUES (?, ?)", settings)

    # Default Aid Types
    aids = [
        ('إعانة شهرية', 500),
        ('إعانة مالية طارئة', 1000),
        ('إعانة زواج', 5000),
        ('إعانة ترميم بناء', 7000)
    ]
    cursor.executemany("INSERT INTO aid_types (name, amount) VALUES (?, ?)", aids)

    # Initial Lookup Data (Dynamic Lists)
    lookups = [
        ('family_status', 'متزوج', 'married'),
        ('family_status', 'أرمل', 'widow'),
        ('family_status', 'مطلق', 'divorced'),
        ('family_status', 'أعزب', 'single'),
        ('case_type', 'أرامل', 'widows'),
        ('case_type', 'أيتام', 'orphans'),
        ('case_type', 'مرضى أمراض مزمنة', 'chronic_illness'),
        ('case_type', 'منكوبي كوارث', 'disaster_relief')
    ]
    cursor.executemany("INSERT INTO lookup_data (category, label, value) VALUES (?, ?, ?)", lookups)

    conn.commit()
    conn.close()
    print("Database Ehsan v2.2 Initialized Successfully!")

if __name__ == '__main__':
    init_db()
