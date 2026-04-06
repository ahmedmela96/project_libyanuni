import sqlite3
import json

DB_PATH = 'ehsan.db'

def run_migration():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Check if permissions column exists
    cur.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cur.fetchall()]
    
    if 'permissions' not in columns:
        print("Adding permissions column...")
        cur.execute("ALTER TABLE users ADD COLUMN permissions TEXT DEFAULT '[]'")
        
        # Give admin full permissions by default
        admin_perms = json.dumps([
            'overview-view', 'entry-view', 'research-view', 'sharia-view', 
            'finance-view', 'reports-view', 'user-approvals-view', 'settings-view'
        ])
        cur.execute("UPDATE users SET permissions = ? WHERE role = 'admin'", (admin_perms,))
        
        # Give other default roles their basic permissions to not break existing logins
        sharia_perms = json.dumps(['overview-view', 'sharia-view'])
        cur.execute("UPDATE users SET permissions = ? WHERE role = 'sharia_committee'", (sharia_perms,))
        
        finance_perms = json.dumps(['overview-view', 'finance-view'])
        cur.execute("UPDATE users SET permissions = ? WHERE role = 'finance'", (finance_perms,))
        
        researcher_perms = json.dumps(['overview-view', 'entry-view', 'research-view'])
        cur.execute("UPDATE users SET permissions = ? WHERE role = 'researcher'", (researcher_perms,))
        
        conn.commit()
        print("Migration completed.")
    else:
        print("Column 'permissions' already exists.")
        
    conn.close()

if __name__ == '__main__':
    run_migration()
