import sqlite3
import os
import hashlib

# Database Path
DB_PATH = 'ehsan.db'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH) # Start fresh
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Users Table (Enhanced Roles)
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT CHECK(role IN ('admin', 'researcher', 'sharia_committee', 'finance')) NOT NULL,
            name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Beneficiaries Table (Workflow Driven)
    # status: pending_research, pending_sharia, approved, rejected
    cursor.execute('''
        CREATE TABLE beneficiaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            national_id TEXT UNIQUE NOT NULL, 
            name TEXT NOT NULL,
            family_size INTEGER NOT NULL,
            case_type TEXT CHECK(case_type IN ('orphan', 'widow', 'needy', 'patient')) NOT NULL,
            income DECIMAL(10,2) NOT NULL,
            need_score REAL DEFAULT 0,
            phone TEXT NOT NULL,
            address TEXT,
            status TEXT DEFAULT 'pending_research',
            researcher_notes TEXT,
            sharia_fatwa TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Aid Types Table (Conditional Logic)
    # requires_approval: 1 (Needs Sharia/Finance), 0 (Immediate/Ramadan Baskets)
    cursor.execute('''
        CREATE TABLE aid_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT CHECK(category IN ('financial', 'food', 'medical')) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            sponsor TEXT,
            requires_approval INTEGER DEFAULT 1
        )
    ''')

    # 4. Distributions Table
    cursor.execute('''
        CREATE TABLE distributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            beneficiary_id INTEGER NOT NULL,
            aid_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            distribution_date DATE NOT NULL,
            FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id),
            FOREIGN KEY (aid_id) REFERENCES aid_types(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # --- Insert Sample Roles ---
    sample_users = [
        ('admin', hash_password('admin123'), 'admin', 'الآدمن العام'),
        ('researcher', hash_password('res123'), 'researcher', 'الباحث الميداني'),
        ('sharia', hash_password('sharia123'), 'sharia_committee', 'اللجنة الشرعية'),
        ('finance', hash_password('fin123'), 'finance', 'اللجنة المالية')
    ]
    cursor.executemany('INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)', sample_users)

    # --- Insert Sample Aid Types ---
    sample_aid = [
        ('منحة مالية دورية (راتب)', 'financial', 1000, 'صندوق الزكاة', 1), # Requires Approval
        ('سلة غذائية رمضانية (عامة)', 'food', 250, 'متبرع غامض', 0), # Immediate
        ('أدوية أمراض مزمنة', 'medical', 400, 'الهلال الأحمر', 1) # Requires Approval
    ]
    cursor.executemany('INSERT INTO aid_types (name, category, amount, sponsor, requires_approval) VALUES (?, ?, ?, ?, ?)', sample_aid)

    # --- Insert Sample Beneficiaries (Diverse States) ---
    sample_beneficiaries = [
        ('119900012345', 'علي محمد بن ناصر', 6, 'orphan', 350.0, 3.2, '0911234567', 'طرابلس - حي الأندلس', 'pending_research', None, None),
        ('219950067890', 'سارة محمود الخروفي', 4, 'widow', 150.0, 3.4, '0922345678', 'بنغازي - الكويفية', 'approved', 'تم التحقق من عجز الأسرة وتهالك السكن.', 'تستحق الصرف الشهري للأيتام والمنحة المالية.'),
        ('120000011223', 'حسين عمر المبروك', 8, 'needy', 1200.0, 1.8, '0944556677', 'مصراتة - المركز', 'pending_sharia', 'الدخل ضعيف والأسرة كبيرة، يحتاج لفتوى لصرف المنحة الاستثنائية.', None)
    ]
    cursor.executemany('''
        INSERT INTO beneficiaries (national_id, name, family_size, case_type, income, need_score, phone, address, status, researcher_notes, sharia_fatwa)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_beneficiaries)

    conn.commit()
    conn.close()
    print("Multi-Role Institutional Database 'ehsan.db' has been initialized.")

if __name__ == '__main__':
    init_db()
