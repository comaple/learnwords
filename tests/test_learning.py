import os
import time
from backend.app import models
from backend.app.db import SessionLocal

os.environ.setdefault('DATABASE_URL', 'sqlite:///./test.db')

from fastapi.testclient import TestClient

from backend.app.main import app


def setup_module(module):
    try:
        os.remove('test.db')
    except FileNotFoundError:
        pass


def teardown_module(module):
    try:
        os.remove('test.db')
    except FileNotFoundError:
        pass


def get_client_and_headers():
    client = TestClient(app)
    # registration is idempotent in the app; safe to call repeatedly
    r = client.post('/api/v1/users/register', json={'email': 't@example.com', 'password': 'pass', 'name': 'T'})
    assert r.status_code == 200
    r = client.post('/api/v1/users/login', json={'email': 't@example.com', 'password': 'pass', 'name': 'T'})
    assert r.status_code == 200
    token = r.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    return client, headers


def ensure_word(lemma='apple'):
    db = SessionLocal()
    existing = db.query(models.Word).filter(models.Word.lemma == lemma).first()
    if existing:
        w = existing
    else:
        w = models.Word(lemma=lemma)
        db.add(w)
        db.commit()
        db.refresh(w)
    db.close()
    return w


def test_register_user():
    client = TestClient(app)
    r = client.post('/api/v1/users/register', json={'email': 'u1@example.com', 'password': 'pw', 'name': 'U1'})
    assert r.status_code == 200
    data = r.json()
    assert data.get('email') == 'u1@example.com'


def test_login_user():
    client = TestClient(app)
    # ensure account exists
    client.post('/api/v1/users/register', json={'email': 'u2@example.com', 'password': 'pw', 'name': 'U2'})
    r = client.post('/api/v1/users/login', json={'email': 'u2@example.com', 'password': 'pw', 'name': 'U2'})
    assert r.status_code == 200
    data = r.json()
    assert 'access_token' in data


def test_upload_triggers_background_and_records_ocr(monkeypatch):
    client, headers = get_client_and_headers()

    import backend.app.ocr_service as ocr_mod

    def fake_process(self, path):
        return {'words': ['apple', 'banana'], 'count': 2, 'raw_result': {}}

    monkeypatch.setattr(ocr_mod.OCRService, 'process_document', fake_process)

    files = {'file': ('f.txt', b'hello', 'text/plain')}
    r = client.post('/api/v1/upload', files=files)
    assert r.status_code == 200
    payload = r.json()
    assert 'upload_id' in payload
    upload_id = payload['upload_id']

    # poll status until background task completes (small timeout)
    final = None
    for _ in range(20):
        r2 = client.get(f'/api/v1/upload/{upload_id}')
        assert r2.status_code == 200
        body = r2.json()
        if body.get('status') == 'done':
            final = body
            break
        time.sleep(0.05)

    assert final is not None, 'background OCR did not complete in time'
    assert final.get('count') == 2
    assert 'apple' in final.get('words', [])


def test_learning_progress_and_plan():
    client, headers = get_client_and_headers()
    w = ensure_word('apple')

    # post progress
    payload = {'word_id': w.id, 'performance': 0.9}
    r = client.post('/api/v1/learning/progress', json=payload, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert 'next_review' in data

    # get learning plan and ensure word appears
    r = client.get('/api/v1/learning/plan', headers=headers)
    assert r.status_code == 200
    plans = r.json().get('plans', [])
    assert any(p['word_id'] == w.id for p in plans)


def test_integration_full_flow(monkeypatch):
    # Full flow: register/login -> upload (OCR) -> create word -> progress -> plan
    client = TestClient(app)
    client.post('/api/v1/users/register', json={'email': 'integ@example.com', 'password': 'pw', 'name': 'I'})
    r = client.post('/api/v1/users/login', json={'email': 'integ@example.com', 'password': 'pw', 'name': 'I'})
    token = r.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    import backend.app.ocr_service as ocr_mod

    def fake_process(self, path):
        return {'words': ['orange'], 'count': 1, 'raw_result': {}}

    monkeypatch.setattr(ocr_mod.OCRService, 'process_document', fake_process)

    files = {'file': ('f2.txt', b'hello', 'text/plain')}
    r = client.post('/api/v1/upload', files=files)
    assert r.status_code == 200
    upload_id = r.json()['upload_id']

    # wait for OCR
    for _ in range(20):
        r2 = client.get(f'/api/v1/upload/{upload_id}')
        if r2.json().get('status') == 'done':
            break
        time.sleep(0.05)

    # ensure word created and progress can be posted
    w = ensure_word('orange')
    r = client.post('/api/v1/learning/progress', json={'word_id': w.id, 'performance': 0.8}, headers=headers)
    assert r.status_code == 200
    r = client.get('/api/v1/learning/plan', headers=headers)
    assert r.status_code == 200

