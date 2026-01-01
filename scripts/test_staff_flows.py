import uuid
import json
from app import app


def pretty(resp):
    try:
        return json.dumps(resp.get_json(), indent=2)
    except Exception:
        return resp.data.decode()


with app.app_context():
    client = app.test_client()

    # create unique staff user
    email = f"staff_test_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPass123!"
    print('Registering staff user:', email)
    r = client.post('/auth/register', json={'name': 'Test Staff', 'email': email, 'password': password, 'role': 'staff'})
    print('register ->', r.status_code)
    print(pretty(r))

    # login
    r = client.post('/auth/login', json={'email': email, 'password': password})
    print('login ->', r.status_code)
    print(pretty(r))
    if r.status_code != 200:
        raise SystemExit('Login failed')
    token = r.get_json().get('token')
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    # create staff profile via POST /api/staff/me
    r = client.post('/api/staff/me', json={'phone': '9999999999'}, headers=headers)
    print('/api/staff/me POST ->', r.status_code)
    print(pretty(r))

    # get staff profile
    r = client.get('/api/staff/me', headers=headers)
    print('/api/staff/me GET ->', r.status_code)
    print(pretty(r))

    # update staff profile
    r = client.put('/api/staff/me', json={'phone': '8888888888', 'is_available': False}, headers=headers)
    print('/api/staff/me PUT ->', r.status_code)
    print(pretty(r))

    # get assignments
    r = client.get('/api/staff/me/assignments', headers=headers)
    print('/api/staff/me/assignments ->', r.status_code)
    print(pretty(r))

    # get deliveries for staff
    r = client.get('/deliveries/my', headers=headers)
    print('/deliveries/my ->', r.status_code)
    print(pretty(r))

    print('\nTest script completed')
