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
            elif self.path.startswith('/api/search?'):
                query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q', [''])[0]
                self.handle_search(query)
            else:
                self.send_error_response(404, "Endpoint not found")
        else:
            super().do_GET()

    # --- API Handlers ---

    def handle_login(self, data):
        username = data.get('username')
        password = data.get('password')
        hashed = hash_password(password)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, name FROM users WHERE username=? AND password=?", (username, hashed))
        user = cursor.fetchone()
        conn.close()

        if user:
            self.send_json_response({
                "id": user[0],
                "username": user[1],
                "role": user[2],
                "name": user[3]
            })
        else:
            self.send_error_response(401, "اسم المستخدم أو كلمة المرور غير صحيحة")

    def handle_get_users(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, name, created_at FROM users")
        rows = cursor.fetchall()
        result = [dict(zip([c[0] for c in cursor.description], row)) for row in rows]
        conn.close()
        self.send_json_response(result)

    def handle_add_user(self, data):
        # Admin-only check logic would go here in a production system
        u = data.get('username')
        p = data.get('password')
        r = data.get('role')
        n = data.get('name')
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)", (u, hash_password(p), r, n))
            conn.commit()
            conn.close()
            self.send_json_response({"message": "تمت إضافة المستخدم بنجاح"})
        except sqlite3.IntegrityError:
            self.send_error_response(400, "اسم المستخدم مسجل مسبقاً")

    def handle_add_beneficiary(self, data):
        national_id = data.get('nationalId')
        name = data.get('name')
        family_size = int(data.get('size'))
        case_type = data.get('caseType') 
        income = float(data.get('income'))
        phone = data.get('phone')

        # Need Score Logic
        fs_score = 1 if family_size <= 2 else (2 if family_size <= 5 else 3)
        inc_score = 3 if income < 500 else (2 if income <= 1000 else 1)
        ct_score = {"orphan": 3, "patient": 2, "widow": 2, "needy": 1}.get(case_type, 1)
        need_score = (0.4 * fs_score) + (0.4 * inc_score) + (0.2 * ct_score)

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO beneficiaries (national_id, name, family_size, case_type, income, need_score, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (national_id, name, family_size, case_type, income, need_score, phone))
            conn.commit()
            conn.close()
            self.send_json_response({"needScore": round(need_score, 2)})
        except sqlite3.IntegrityError:
            self.send_error_response(400, "الرقم الوطني مسجل مسبقاً")

    def handle_distribute(self, data):
        b_id = data.get('beneficiaryId')
        aid_id = data.get('aidId')
        user_id = data.get('userId')
        limit_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM distributions WHERE beneficiary_id=? AND aid_id=? AND distribution_date > ?", (b_id, aid_id, limit_date))
        if cursor.fetchone():
            conn.close()
            self.send_error_response(400, "⚠️ المستفيد استلم هذه المساعدة مسبقاً خلال الـ 30 يوماً الماضية.")
            return

        cursor.execute("INSERT INTO distributions (beneficiary_id, aid_id, user_id, distribution_date) VALUES (?, ?, ?, ?)", 
                       (b_id, aid_id, user_id, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()
        self.send_json_response({"message": "تم توثيق التوزيع بنجاح"})

    def handle_get_beneficiaries(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM beneficiaries ORDER BY need_score DESC")
        result = [dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()]
        conn.close()
        self.send_json_response(result)

    def handle_get_aid_types(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM aid_types")
        result = [dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()]
        conn.close()
        self.send_json_response(result)

    def handle_get_stats(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        b = cursor.execute("SELECT COUNT(*) FROM beneficiaries").fetchone()[0]
        d = cursor.execute("SELECT COUNT(*) FROM distributions").fetchone()[0]
        u = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        conn.close()
        self.send_json_response({"totalBeneficiaries": b, "totalDistributions": d, "totalStaff": u})

    def handle_search(self, query):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM beneficiaries WHERE name LIKE ? OR national_id LIKE ?", (f'%{query}%', f'%{query}%'))
        result = [dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()]
        conn.close()
        self.send_json_response(result)

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
        print(f"Ehsan Secure Server started at http://localhost:{PORT}")
        httpd.serve_forever()
