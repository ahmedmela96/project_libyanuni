import http.server
import socketserver
import json
import sqlite3
import urllib.parse
from datetime import datetime

PORT = 8000
DB_PATH = 'ehsan.db'

class EhsanHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path.startswith('/api/'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            
            # Auth & User Management
            if self.path == '/api/login': self.handle_login(data)
            elif self.path == '/api/forgot_password': self.handle_forgot_password(data)
            elif self.path == '/api/register': self.handle_register(data)
            elif self.path == '/api/users/add': self.handle_admin_add_user(data) # v2.2.2 Admin Internal Add
            elif self.path == '/api/users/approve': self.handle_user_approval(data)
            elif self.path == '/api/users/update_permissions': self.handle_update_permissions(data)
            elif self.path == '/api/notifications/clear': self.handle_clear_notifications(data)
            elif self.path == '/api/users/update': self.handle_user_update(data)
            
            # Beneficiaries & Lifecycle Logic
            elif self.path == '/api/beneficiaries': self.handle_add_beneficiary(data)
            elif self.path == '/api/research/verify': self.handle_verify_research(data)
            elif self.path == '/api/sharia/approve': self.handle_sharia_decision(data)
            elif self.path == '/api/distributions': self.handle_distribute(data)
            
            # Settings & Dynamic Options
            elif self.path == '/api/settings': self.handle_update_settings(data)
            elif self.path == '/api/options': self.handle_update_options(data)
            else: self.send_error_response(404, "Endpoint not found")
        else:
            super().do_POST()

    def do_GET(self):
        if self.path.startswith('/api/'):
            if self.path == '/api/beneficiaries': self.handle_get_beneficiaries()
            elif self.path.startswith('/api/beneficiaries/') and self.path.endswith('/history'):
                bid = self.path.split('/')[-2]; self.handle_get_history(bid)
            
            elif self.path == '/api/aid_types': self.handle_get_aid_types()
            elif self.path == '/api/stats': self.handle_get_stats()
            elif self.path == '/api/options': self.handle_get_options()
            
            elif self.path == '/api/users/all': self.handle_get_all_users()
            elif self.path == '/api/users/pending': self.handle_get_pending_users()
            
            elif self.path == '/api/settings': self.handle_get_settings()
            elif self.path.startswith('/api/notifications'): self.handle_get_notifications()
            elif self.path == '/api/finance': self.handle_get_finance()
            elif self.path.startswith('/api/search?'):
                query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q', [''])[0]
                self.handle_search(query)
            else: self.send_error_response(404, "Endpoint not found")
        else:
            super().do_GET()

    def _is_admin(self, uid):
        if not uid: return False
        try: uid = int(uid)
        except: return False
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT role FROM users WHERE id=?", (uid,))
        res = cur.fetchone(); conn.close()
        return res and res[0] == 'admin'

    # --- v2.2.2 Logic Handlers ---

    def handle_login(self, data):
        u, p = data.get('username'), data.get('password')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, name, status, permissions FROM users WHERE username=? AND password=?", (u, p))
        user = cursor.fetchone(); conn.close()
        if user:
            if user[4] != 'active': return self.send_error_response(403, f"عفواً، حسابك حالياً في حالة ({user[4]}). يرجى مراجعة المدير.")
            perms = json.loads(user[5]) if user[5] else []
            self.send_json_response({"id":user[0], "username":user[1], "role":user[2], "name":user[3], "permissions":perms})
        else: self.send_error_response(401, "خطأ في بيانات الدخول.")

    def handle_register(self, data):
        u, p, r, n = data.get('username'), data.get('password'), data.get('role'), data.get('name')
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            # New external registrations start as 'pending'
            cur.execute("INSERT INTO users (username, password, role, name, status) VALUES (?,?,?,?, 'pending')", (u, p, r, n))
            cur.execute("INSERT INTO notifications (target_role, message) VALUES ('admin', ?)", (f"طلب انضمام جديد: {n} كـ {r}",))
            conn.commit(); conn.close()
            self.send_json_response({"message": "تم إرسال طلب الانضمام بنجاح."})
        except: self.send_error_response(400, "اسم المستخدم محجوز بالفعل.")

    def handle_admin_add_user(self, data):
        if not self._is_admin(data.get('requester_id')): return self.send_error_response(403, "صلاحية مقيدة: للمدير فقط")
        u, p, r, n = data.get('username'), data.get('password'), data.get('role'), data.get('name')
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, password, role, name, status) VALUES (?,?,?,?, 'active')", (u, p, r, n))
            conn.commit(); conn.close()
            self.send_json_response({"message": "تمت إضافة الموظف واعتماده فوراً بنجاح ✅"})
        except: self.send_error_response(400, "اسم المستخدم محجوز بالفعل.")

    def handle_add_beneficiary(self, data):
        nid = data.get('nationalId'); name = data.get('name'); gender = data.get('gender')
        f_status = data.get('family_status'); f_other = data.get('family_status_other', '')
        size = int(data.get('family_size', 1)); income = float(data.get('income', 0))
        phone = data.get('phone'); address = data.get('address')
        
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT id FROM beneficiaries WHERE national_id = ?", (nid,))
        if cur.fetchone():
            conn.close()
            return self.send_error_response(400, "هذا الرقم الوطني مسجل بالفعل في قاعدة البيانات.")

        try:
            cur.execute('''INSERT INTO beneficiaries 
                           (national_id, name, gender, family_status, family_status_other, family_size, income, phone, address) 
                           VALUES (?,?,?,?,?,?,?,?,?)''', 
                           (nid, name, gender, f_status, f_other, size, income, phone, address))
            bid = cur.lastrowid
            cur.execute("INSERT INTO audit_logs (beneficiary_id, action, notes) VALUES (?, 'تسجيل ملف', 'تم إدراج البيانات الأولية بنجاح')", (bid,))
            cur.execute("INSERT INTO notifications (target_role, message) VALUES ('researcher', ?)", (f"ملف جديد بانتظار التدقيق: {name}",))
            conn.commit(); conn.close()
            self.send_json_response({"message": "تم تسجيل الملف وبدء رحلة الحوكمة بنجاح ✅"})
        except Exception as e:
            conn.close(); self.send_error_response(500, f"خطأ في الحفظ: {str(e)}")

    def handle_get_history(self, bid):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute('''SELECT l.action, l.notes, l.created_at, u.name as actor_name
                       FROM audit_logs l LEFT JOIN users u ON l.user_id = u.id
                       WHERE l.beneficiary_id = ? ORDER BY l.created_at ASC''', (bid,))
        result = [dict(zip(['action', 'notes', 'date', 'actor'], row)) for row in cur.fetchall()]; conn.close()
        self.send_json_response(result)

    def handle_verify_research(self, data):
        bid, notes, c_type, uid = data.get('beneficiaryId'), data.get('notes'), data.get('case_type'), data.get('userId')
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("UPDATE beneficiaries SET researcher_notes=?, case_type=?, status='pending_sharia' WHERE id=?", (notes, c_type, bid))
        cur.execute("INSERT INTO audit_logs (beneficiary_id, action, notes, user_id) VALUES (?, 'زيارة ميدانية', ?, ?)", 
                    (bid, f"تم تحديد الحالة كـ ({c_type}) - ملاحظات: {notes}", uid))
        cur.execute("SELECT name FROM beneficiaries WHERE id=?", (bid,))
        bname = (cur.fetchone() or ['?'])[0]
        cur.execute("INSERT INTO notifications (target_role, message) VALUES ('sharia_committee', ?)",
                    (f"⚖️ ملف ينتظر الفتوى: {bname}",))
        conn.commit(); conn.close()
        self.send_json_response({"message": "تم توثيق الزيارة وإحالة الملف للجنة الشرعية."})

    def handle_sharia_decision(self, data):
        bid, decision, fatwa, uid = data.get('beneficiaryId'), data.get('decision'), data.get('fatwa'), data.get('userId')
        status = 'approved' if decision == 'approve' else 'rejected'
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("UPDATE beneficiaries SET sharia_fatwa=?, status=? WHERE id=?", (fatwa, status, bid))
        action_text = "اعتماد نهائي ✅" if decision == 'approve' else "رفض الملف ❌"
        cur.execute("INSERT INTO audit_logs (beneficiary_id, action, notes, user_id) VALUES (?, ?, ?, ?)", 
                    (bid, action_text, f"قرار اللجنة: {fatwa}", uid))
        if decision == 'approve':
            cur.execute("SELECT name FROM beneficiaries WHERE id=?", (bid,))
            bname = (cur.fetchone() or ['?'])[0]
            cur.execute("INSERT INTO notifications (target_role, message) VALUES ('finance', ?)",
                        (f"💰 ملف جاهز للصرف: {bname} - تم اعتماده شرعياً",))
        conn.commit(); conn.close()
        self.send_json_response({"message": "تم تسجيل قرار اللجنة الشرعية بنجاح."})

    def handle_distribute(self, data):
        bid, aid_id, uid = data.get('beneficiaryId'), data.get('aidId'), data.get('userId')
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT name, amount FROM aid_types WHERE id=?", (aid_id,))
        aid = cur.fetchone()
        cur.execute("INSERT INTO distributions (beneficiary_id, aid_id, user_id, amount) VALUES (?,?,?,?)", (bid, aid_id, uid, aid[1]))
        cur.execute("INSERT INTO audit_logs (beneficiary_id, action, notes, user_id) VALUES (?, 'صرف معونة', ?, ?)", 
                    (bid, f"صرف ({aid[0]}) بقيمة ({aid[1]} ل.د) - تم بنجاح", uid))
        conn.commit(); conn.close()
        self.send_json_response({"message": "تم تأكيد الصرف وتوثيق العملية في سجل المستفيد ✅"})

    def handle_update_settings(self, data):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        for key, value in data.items():
            cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit(); conn.close()
        self.send_json_response({"message": "تم تحديث كافة بيانات الهوية بنجاح ✅"})

    # --- Core Helpers ---

    def handle_get_settings(self):
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        cursor.execute("SELECT * FROM settings"); rows = cursor.fetchall()
        result = {row[0]: row[1] for row in rows}; conn.close()
        self.send_json_response(result)

    def handle_get_notifications(self):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT id, message, created_at FROM notifications ORDER BY created_at DESC LIMIT 5")
        result = [dict(zip(['id', 'message', 'created_at'], row)) for row in cur.fetchall()]
        conn.close(); self.send_json_response(result)

    def handle_get_aid_types(self):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT id, name, amount FROM aid_types")
        result = [dict(zip(['id', 'name', 'amount'], row)) for row in cur.fetchall()]
        conn.close(); self.send_json_response(result)

    def handle_get_finance(self):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute('''SELECT d.id, b.national_id, b.name as b_name, a.name as aid_name, d.amount, d.created_at, u.name as u_name
                       FROM distributions d 
                       JOIN beneficiaries b ON d.beneficiary_id = b.id
                       JOIN aid_types a ON d.aid_id = a.id
                       JOIN users u ON d.user_id = u.id ORDER BY d.created_at DESC''')
        result = [dict(zip(['id', 'national_id', 'name', 'family_status', 'amount', 'date', 'status'], 
                           [row[0], row[1], row[2], f"{row[3]} ({row[4]} د.ل)", row[4], row[5], f"صرف: {row[6]}"])) for row in cur.fetchall()]
        conn.close(); self.send_json_response(result)

    def handle_get_stats(self):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        res = {
            "total": cur.execute("SELECT COUNT(*) FROM beneficiaries").fetchone()[0],
            "pending": cur.execute("SELECT COUNT(*) FROM beneficiaries WHERE status='pending_research'").fetchone()[0],
            "sharia": cur.execute("SELECT COUNT(*) FROM beneficiaries WHERE status='pending_sharia'").fetchone()[0],
            "approved": cur.execute("SELECT COUNT(*) FROM beneficiaries WHERE status='approved'").fetchone()[0]
        }
        conn.close(); self.send_json_response(res)

    def handle_get_beneficiaries(self):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT * FROM beneficiaries ORDER BY id DESC")
        result = [dict(zip([c[0] for c in cur.description], row)) for row in cur.fetchall()]
        conn.close(); self.send_json_response(result)

    def handle_get_options(self):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT category, label, value FROM lookup_data")
        result = [dict(zip(['category', 'label', 'value'], row)) for row in cur.fetchall()]
        conn.close(); self.send_json_response(result)

    def handle_update_options(self, data):
        cat, label, val = data.get('category'), data.get('label'), data.get('value')
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO lookup_data (category, label, value) VALUES (?, ?, ?)", (cat, label, val))
            conn.commit(); self.send_json_response({"message": "تمت إضافة الخيار."})
        except: self.send_error_response(400, "موجود مسبقاً.")
        finally: conn.close()

    def handle_get_all_users(self):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT id, username, password, role, name, status, created_at, permissions FROM users")
        result = []
        for row in cur.fetchall():
            d = dict(zip([c[0] for c in cur.description], row))
            d['permissions'] = json.loads(d['permissions']) if d['permissions'] else []
            result.append(d)
        conn.close(); self.send_json_response(result)

    def handle_user_approval(self, data):
        if not self._is_admin(data.get('requester_id')): return self.send_error_response(403, "صلاحية مقيدة: للمدير فقط")
        uid, dec = data.get('id'), data.get('decision')
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("UPDATE users SET status=? WHERE id=?", ('active' if dec=='approve' else 'rejected', uid))
        conn.commit(); conn.close(); self.send_json_response({"message": "تم التحديث."})

    def handle_user_update(self, data):
        if not self._is_admin(data.get('requester_id')): return self.send_error_response(403, "صلاحية مقيدة: للمدير فقط")
        uid, n, r, s, p = data.get('id'), data.get('name'), data.get('role'), data.get('status'), data.get('password')
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("UPDATE users SET name=?, role=?, status=?, password=? WHERE id=?", (n, r, s, p, uid))
        conn.commit(); conn.close(); self.send_json_response({"message": "تم تحديث الموظف بنجاح."})

    def handle_forgot_password(self, data):
        ident = data.get('identifier')
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT id, name FROM users WHERE username=?", (ident,))
        u = cur.fetchone()
        if u:
            cur.execute("INSERT INTO notifications (target_role, message) VALUES ('admin', ?)", (f"طلب استعادة كلمة مرور للموظف: {u[1]}",))
            conn.commit()
        conn.close()
        self.send_json_response({"message": "تم إبلاغ الإدارة، سيتم معالجة طلبك قريباً."})

    def handle_update_permissions(self, data):
        if not self._is_admin(data.get('requester_id')): return self.send_error_response(403, "صلاحية مقيدة: للمدير فقط")
        uid, perms = data.get('id'), data.get('permissions')
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("UPDATE users SET permissions=? WHERE id=?", (json.dumps(perms), uid))
        conn.commit(); conn.close(); self.send_json_response({"message": "تم حفط الصلاحيات بنجاح."})

    def handle_get_notifications(self):
        parsed = urllib.parse.urlparse(self.path)
        role = urllib.parse.parse_qs(parsed.query).get('role', ['admin'])[0]
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        try:
            if role == 'admin':
                # Admin sees EVERYTHING from all roles
                cur.execute("SELECT id, target_role, message, created_at FROM notifications ORDER BY id DESC LIMIT 50")
            else:
                # Each role sees ONLY their own notifications
                cur.execute("SELECT id, target_role, message, created_at FROM notifications WHERE target_role=? ORDER BY id DESC LIMIT 30", (role,))
            result = [dict(zip(['id', 'target_role', 'message', 'created_at'], row)) for row in cur.fetchall()]
        except:
            result = []
        conn.close(); self.send_json_response(result)

    def handle_clear_notifications(self, data):
        role = data.get('role', 'admin')
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        try:
            # ALWAYS delete only the requester's own role — never touch other roles
            cur.execute("DELETE FROM notifications WHERE target_role=?", (role,))
            conn.commit()
        except: pass
        conn.close(); self.send_json_response({"message": "تم مسح إشعاراتك فقط."})

    def handle_get_pending_users(self):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT id, username, role, name, status FROM users WHERE status='pending'")
        result = [dict(zip([c[0] for c in cur.description], row)) for row in cur.fetchall()]
        conn.close(); self.send_json_response(result)

    def handle_search(self, q):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT * FROM beneficiaries WHERE name LIKE ? OR national_id LIKE ? OR phone LIKE ?", (f'%{q}%', f'%{q}%', f'%{q}%'))
        result = [dict(zip([c[0] for c in cur.description], row)) for row in cur.fetchall()]; conn.close()
        self.send_json_response(result)

    def send_json_response(self, data):
        self.send_response(200); self.send_header('Content-type', 'application/json; charset=utf-8'); self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def send_error_response(self, code, message):
        self.send_response(code); self.send_header('Content-type', 'application/json; charset=utf-8'); self.end_headers()
        self.wfile.write(json.dumps({"error": message}, ensure_ascii=False).encode('utf-8'))

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), EhsanHandler) as httpd:
        print(f"Ehsan Platform v2.2.2 - Security & Governance Mode - Port {PORT}")
        httpd.serve_forever()
