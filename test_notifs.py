import urllib.request, json

base = 'http://localhost:8000'

def get(path):
    with urllib.request.urlopen(f'{base}{path}', timeout=5) as r:
        return json.loads(r.read())

def post(path, body):
    req = urllib.request.Request(f'{base}{path}', data=json.dumps(body).encode(),
                                  method='POST', headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

print('=== اختبار نظام الإشعارات المحسّن ===\n')

# Admin sees all
admin_notifs = get('/api/notifications?role=admin')
print(f'المدير يرى: {len(admin_notifs)} إشعار')

# Researcher sees only researcher+admin
res_notifs = get('/api/notifications?role=researcher')
print(f'الباحث يرى: {len(res_notifs)} إشعار')

# Sharia sees only sharia+admin
sharia_notifs = get('/api/notifications?role=sharia_committee')
print(f'الشرعية ترى: {len(sharia_notifs)} إشعار')

# Finance
fin_notifs = get('/api/notifications?role=finance')
print(f'المالية ترى: {len(fin_notifs)} إشعار')

# Add test notifications for each role
print('\n--- إضافة إشعارات تجريبية ---')
import sqlite3
conn = sqlite3.connect('ehsan.db')
cur = conn.cursor()
cur.execute("INSERT INTO notifications (target_role, message) VALUES ('researcher', '🏚️ مستفيد جديد: أحمد الميلادي - يحتاج زيارة')")
cur.execute("INSERT INTO notifications (target_role, message) VALUES ('sharia_committee', '⚖️ ملف ينتظر الفتوى: طه التاجوري')")
cur.execute("INSERT INTO notifications (target_role, message) VALUES ('finance', '💰 ملف جاهز للصرف: محمد علي - تم اعتماده شرعياً')")
cur.execute("INSERT INTO notifications (target_role, message) VALUES ('admin', '🔔 طلب انضمام جديد من: يوسف الفلاح')")
conn.commit(); conn.close()
print('تم إضافة 4 إشعارات تجريبية')

# Re-check
print('\n--- التحقق النهائي ---')
print(f'المدير يرى: {len(get("/api/notifications?role=admin"))} إشعار (كل شيء)')
print(f'الباحث يرى: {len(get("/api/notifications?role=researcher"))} إشعار')
print(f'الشرعية ترى: {len(get("/api/notifications?role=sharia_committee"))} إشعار')
print(f'المالية ترى: {len(get("/api/notifications?role=finance"))} إشعار')

# Test clear
code, resp = post('/api/notifications/clear', {'role': 'researcher'})
print(f'\nمسح إشعارات الباحث: {code} - {resp}')
print(f'الباحث بعد المسح يرى: {len(get("/api/notifications?role=researcher"))} إشعار')

print('\n=== اكتمل الاختبار بنجاح ===')
