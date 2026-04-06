import sqlite3

conn = sqlite3.connect('ehsan.db')
cur = conn.cursor()

# Check if notifications table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notifications'")
exists = cur.fetchone()
print('notifications table exists:', exists)

if not exists:
    cur.execute('''CREATE TABLE notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_role TEXT DEFAULT 'admin',
        message TEXT,
        is_read INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    print('Created notifications table.')

# Add a test notification to verify it works
cur.execute("INSERT INTO notifications (target_role, message) VALUES ('admin', 'اختبار: الإشعارات تعمل!')")
conn.commit()

cur.execute('SELECT * FROM notifications')
rows = cur.fetchall()
print('All notifications:', rows)
conn.close()
print('Done.')
