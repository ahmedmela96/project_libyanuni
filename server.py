import http.server
import socketserver
import json
import sqlite3
import urllib.parse
import hashlib
from datetime import datetime, timedelta

PORT = 8000
DB_PATH = 'ehsan.db'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class EhsanHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path.startswith('/api/'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            
            if self.path == '/api/login':
                self.handle_login(data)
            elif self.path == '/api/beneficiaries':
                self.handle_add_beneficiary(data)
            elif self.path == '/api/research/verify':
                self.handle_verify_research(data)
            elif self.path == '/api/sharia/approve':
                self.handle_sharia_decision(data)
            elif self.path == '/api/distributions':
                self.handle_distribute(data)
            elif self.path == '/api/users':
                self.handle_add_user(data)
            else:
                self.send_error_response(404, "Endpoint not found")
        else:
            super().do_POST()

    def do_GET(self):
        if self.path.startswith('/api/'):
            if self.path == '/api/beneficiaries':
                self.handle_get_beneficiaries()
            elif self.path == '/api/aid_types':
                self.handle_get_aid_types()
            elif self.path == '/api/stats':
                self.handle_get_stats()
            elif self.path == '/api/users':
                self.handle_get_users()
            elif self.path == '/api/distributions_full':
                self.handle_get_distributions_full()
            elif self.path.startswith('/api/search?'):
                query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q', [''])[0]
                self.handle_search(query)
            else:
                self.send_error_response(404, "Endpoint not found")
        else:
            super().do_GET()

    # --- Authentication & User Management ---

    def handle_login(self, data):
        u, p = data.get('username'), data.get('password')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, name FROM users WHERE username=? AND password=?", (u, hash_password(p)))
        user = cursor.fetchone()
        conn.close()
        if user:
            self.send_json_response({"id":user[0], "username":user[1], "role":user[2], "name":user[3]})
        else:
            self.send_error_response(401, "اسم المستخدم أو كلمة المرور غير صحيحة")

    def handle_add_user(self, data):
        u, p, r, n = data.get('username'), data.get('password'), data.get('role'), data.get('name')
        try:
            conn = sqlite3.connect(DB_PATH)
            curr = conn.cursor()
            curr.execute("INSERT INTO users (username, password, role, name) VALUES (?,?,?,?)", (u, hash_password(p), r, n))
            conn.commit()
            conn.close()
            self.send_json_response({"message": "تمت إضافة المستخدم بنجاح"})
        except Exception as e: self.send_error_response(400, f"خطأ: {str(e)}")

    def handle_get_users(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, name, created_at FROM users")
        result = [dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()]
        conn.close()
        self.send_json_response(result)

    # --- Workflow Logic Enhancements ---

    def handle_add_beneficiary(self, data):
        nid = data.get('nationalId')
        # Strict 12-digit validation
        if not nid or len(nid) != 12 or not nid.isdigit():
            return self.send_error_response(400, "يجب أن يتكون الرقم الوطني من 12 رقم بالضبط.")

        name, size, ctype, income, phone, address = data.get('name'), int(data.get('size')), data.get('caseType'), float(data.get('income')), data.get('phone'), data.get('address')
        
        # Scoring logic
        fs_score = 1 if size <= 2 else (2 if size <= 5 else 3)
        inc_score = 3 if income < 500 else (2 if income <= 1000 else 1)
        ct_score = {"orphan": 3, "patient": 2, "widow": 2, "needy": 1}.get(ctype, 1)
        need_score = (0.4 * fs_score) + (0.4 * inc_score) + (0.2 * ct_score)

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO beneficiaries (national_id, name, family_size, case_type, income, need_score, phone, address, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending_research')
            ''', (nid, name, size, ctype, income, need_score, phone, address))
            conn.commit()
            conn.close()
            self.send_json_response({"message": "تم تسجيل الطلب بنجاح وهو قيد المراجعة الميدانية."})
        except sqlite3.IntegrityError: self.send_error_response(400, "الرقم الوطني مسجل مسبقاً.")

    def handle_verify_research(self, data):
        bid, notes = data.get('beneficiaryId'), data.get('notes')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE beneficiaries SET researcher_notes=?, status='pending_sharia' WHERE id=?", (notes, bid))
        conn.commit()
        conn.close()
        self.send_json_response({"message": "تم توثيق الزيارة الميدانية وإحالة الطلب للجنة الشرعية."})

    def handle_sharia_decision(self, data):
        bid, decision, fatwa = data.get('beneficiaryId'), data.get('decision'), data.get('fatwa')
        status = 'approved' if decision == 'approve' else 'rejected'
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE beneficiaries SET sharia_fatwa=?, status=? WHERE id=?", (fatwa, status, bid))
        conn.commit()
        conn.close()
        self.send_json_response({"message": f"تم تسجيل قرار اللجنة الشرعية بنجاح ({status})."})

    def handle_distribute(self, data):
        bid, aid_id, uid = data.get('beneficiaryId'), data.get('aidId'), data.get('userId')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check Beneficiary status and Aid Type requirements
        cursor.execute("SELECT status FROM beneficiaries WHERE id=?", (bid,))
        b_status = cursor.fetchone()[0]
        cursor.execute("SELECT requires_approval FROM aid_types WHERE id=?", (aid_id,))
        a_req = cursor.fetchone()[0]

        if a_req == 1 and b_status != 'approved':
            conn.close()
            return self.send_error_response(403, "عفواً، هذه المساعدة تتطلب اعتماداً شرعياً مسبقاً للعائلة.")

        # Duplication Check (30 days)
        limit_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        cursor.execute("SELECT id FROM distributions WHERE beneficiary_id=? AND aid_id=? AND distribution_date > ?", (bid, aid_id, limit_date))
        if cursor.fetchone():
            conn.close()
            return self.send_error_response(400, "المستفيد استلم هذه المساعدة خلال الـ 30 يوماً الماضية.")

        cursor.execute("INSERT INTO distributions (beneficiary_id, aid_id, user_id, distribution_date) VALUES (?,?,?,?)", 
                       (bid, aid_id, uid, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()
        self.send_json_response({"message": "تم تأكيد عملية الصرف بنجاح."})

    # --- Data Retrieval ---

    def handle_get_beneficiaries(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM beneficiaries ORDER BY created_at DESC")
        result = [dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()]
        conn.close()
        self.send_json_response(result)

    def handle_get_stats(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        stats = {
            "total": cursor.execute("SELECT COUNT(*) FROM beneficiaries").fetchone()[0],
            "approved": cursor.execute("SELECT COUNT(*) FROM beneficiaries WHERE status='approved'").fetchone()[0],
            "pending": cursor.execute("SELECT COUNT(*) FROM beneficiaries WHERE status='pending_research'").fetchone()[0],
            "sharia": cursor.execute("SELECT COUNT(*) FROM beneficiaries WHERE status='pending_sharia'").fetchone()[0],
            "dist": cursor.execute("SELECT COUNT(*) FROM distributions").fetchone()[0]
        }
        conn.close()
        self.send_json_response(stats)

    def handle_get_distributions_full(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.id, b.name as b_name, a.name as a_name, d.distribution_date, u.name as u_name
            FROM distributions d
            JOIN beneficiaries b ON d.beneficiary_id = b.id
            JOIN aid_types a ON d.aid_id = a.id
            JOIN users u ON d.user_id = u.id
            ORDER BY d.id DESC
        ''')
        rows = cursor.fetchall()
        result = [dict(zip(['id','b_name','a_name','date','u_name'], row)) for row in rows]
        conn.close()
        self.send_json_response(result)

    def handle_get_aid_types(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM aid_types")
        result = [dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()]
        conn.close()
        self.send_json_response(result)

    def handle_search(self, q):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM beneficiaries WHERE name LIKE ? OR national_id LIKE ?", (f'%{q}%', f'%{q}%'))
        result = [dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()]
        conn.close()
        self.send_json_response(result)

    # --- HTTP Helpers ---

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}, ensure_ascii=False).encode('utf-8'))

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), EhsanHandler) as httpd:
        print(f"Institutional Server started at http://localhost:{PORT}")
        httpd.serve_forever()
