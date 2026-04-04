import sqlite3
import os
import hashlib

# Database Path
DB_PATH = 'ehsan.db'

def hash_password(password):
    # Simple SHA-256 hashing for the demonstration
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH) # Start fresh
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT CHECK(role IN ('admin', 'manager', 'clerk')) NOT NULL,
            name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Beneficiaries Table
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Aid Types Table
    cursor.execute('''
        CREATE TABLE aid_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT CHECK(category IN ('financial', 'food', 'medical')) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            sponsor TEXT
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

    # Insert Sample Users with Hashed Passwords
    sample_users = [
        ('admin', hash_password('admin123'), 'admin', 'أدمن النظام'),
        ('ahmed', hash_password('mngr123'), 'manager', 'أحمد محمود'),
        ('sara', hash_password('clrk123'), 'clerk', 'سارة علي')
    ]
    cursor.executemany('INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)', sample_users)

    # Insert Sample Aid Types
    sample_aid = [
        ('منحة مالية عاجلة', 'financial', 500, 'الجمعية الرئيسية'),
        ('سلة غذائية رمضانية', 'food', 150, 'متبرع فاعل خير'),
        ('أدوية مزمنة', 'medical', 200, 'وزارة الصحة')
    ]
    cursor.executemany('INSERT INTO aid_types (name, category, amount, sponsor) VALUES (?, ?, ?, ?)', sample_aid)

    conn.commit()
    conn.close()
    print("Secure Database 'ehsan.db' has been initialized with hashed passwords.")

if __name__ == '__main__':
    init_db()
