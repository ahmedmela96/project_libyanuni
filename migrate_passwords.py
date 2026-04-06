import sqlite3

DB_PATH = 'ehsan.db'

def run_migration():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # We will reset known users and default others to something known just in case,
    # because they cannot be unhashed.
    
    updates = [
        ('admin', 'admin123'),
        ('sharia', 'sharia123'),
        ('finance', 'finance123'),
        ('researcher', 'res123')
    ]
    
    for u, p in updates:
        cur.execute("UPDATE users SET password=? WHERE username=?", (p, u))
        
    # For any user not in the list, just set it to 'pass123' if it looks like a hash (length 64)
    cur.execute("SELECT id, password FROM users")
    for row in cur.fetchall():
        uid, pwd = row
        if len(pwd) == 64:  # Likely SHA-256 hash
            cur.execute("UPDATE users SET password='pass123' WHERE id=?", (uid,))
            
    conn.commit()
    conn.close()
    print("Passwords successfully migrated to plain text.")

if __name__ == '__main__':
    run_migration()
