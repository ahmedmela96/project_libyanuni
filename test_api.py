import urllib.request, json

base = 'http://localhost:8000'

def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method='POST', headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

# 1. Test approve with admin ID = 1
print('Test 1: Approve user with admin ID=1')
code, resp = post(f'{base}/api/users/approve', {'id': 2, 'decision': 'approve', 'requester_id': 1})
print(f'  Status {code}: {resp}')

# 2. Test update user  
print('Test 2: Update user info + password')
code, resp = post(f'{base}/api/users/update', {'id': 2, 'name': 'Test User', 'role': 'researcher', 'status': 'active', 'password': 'test123', 'requester_id': 1})
print(f'  Status {code}: {resp}')

# 3. Test permissions update
print('Test 3: Update permissions')
code, resp = post(f'{base}/api/users/update_permissions', {'id': 2, 'permissions': ['entry-view', 'research-view'], 'requester_id': 1})
print(f'  Status {code}: {resp}')

# 4. Test forgot password notification
print('Test 4: Forgot password -> notification')
code, resp = post(f'{base}/api/forgot_password', {'identifier': 'sharia'})
print(f'  Status {code}: {resp}')

# Verify notification was created
with urllib.request.urlopen(f'{base}/api/notifications', timeout=3) as r:
    notifs = json.loads(r.read())
    print(f'  Total notifications: {len(notifs)}')
    if notifs:
        print(f'  Latest: {notifs[0]["message"]}')

print('\n=== ALL TESTS DONE ===')
