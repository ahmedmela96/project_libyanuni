import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

css = """
/* Notifications (Toasts) Elevating Design */
.toast {
    background: white; border-right: 5px solid var(--primary); color: var(--navy);
    padding: 15px 25px; border-radius: 12px; font-weight: 800; font-size: 0.95rem;
    box-shadow: 0 10px 25px -5px rgba(0,0,0,0.15); display: flex; align-items: center; justify-content: space-between;
    min-width: 300px; animation: slideInX 0.4s cubic-bezier(0.18, 0.89, 0.32, 1.28);
}
.toast.error { border-right-color: var(--danger); }
.toast span { flex: 1; }
.toast-close { cursor: pointer; color: var(--text-muted); font-size: 1.4rem; padding-right: 15px; border-right: 1px solid var(--border); margin-right: 15px; }
@keyframes slideInX { from { opacity: 0; transform: translateX(100%); } to { opacity: 1; transform: translateX(0); } }
"""

with open('style.css', 'a', encoding='utf-8') as f:
    f.write(css)

conn = sqlite3.connect('ehsan.db')
c = conn.cursor()
c.execute("INSERT OR IGNORE INTO users (username, password, role, name, status) VALUES ('sharia', ?, 'sharia_committee', 'اللجنة الشرعية الرسمية', 'active')", (hash_password('sharia123'),))
c.execute("INSERT OR IGNORE INTO users (username, password, role, name, status) VALUES ('finance', ?, 'finance', 'قسم المالية الرسمي', 'active')", (hash_password('finance123'),))
c.execute("INSERT OR IGNORE INTO users (username, password, role, name, status) VALUES ('researcher', ?, 'researcher', 'محمد الباحث - فرع طرابلس', 'active')", (hash_password('res123'),))
conn.commit()
conn.close()
print("تم تنفيذ التعديلات بنجاح")
