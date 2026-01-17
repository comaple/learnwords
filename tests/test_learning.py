import os
import json
import shutil
from backend.app import models
from backend.app.db import SessionLocal

os.environ.setdefault('DATABASE_URL', 'sqlite:///./test.db')

from fastapi.testclient import TestClient

from backend.app.main import app


def setup_module(module):
    # remove test.db
    try:
        os.remove('test.db')
    except FileNotFoundError:
        pass


def teardown_module(module):
    try:
        os.remove('test.db')
    except FileNotFoundError:
        pass


def test_learning_flow(monkeypatch):
    client = TestClient(app)

    # register
    r = client.post('/api/v1/users/register', json={'email': 't@example.com', 'password': 'pass', 'name': 'T'})
    assert r.status_code == 200
    user = r.json()

    # login
    r = client.post('/api/v1/users/login', json={'email': 't@example.com', 'password': 'pass', 'name': 'T'})
    assert r.status_code == 200
    token = r.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # Monkeypatch OCR to avoid external calls
    import backend.app.ocr_service as ocr_mod

    def fake_process(self, path):
        return {'words': ['apple', 'banana'], 'count': 2, 'raw_result': {}}

    monkeypatch.setattr(ocr_mod.OCRService, 'process_document', fake_process)

    # upload a fake file
    files = {'file': ('f.txt', b'hello', 'text/plain')}
    r = client.post('/api/v1/upload', files=files)
    assert r.status_code == 200

    # create a Word in DB
    db = SessionLocal()
    w = models.Word(lemma='apple')
    db.add(w)
    db.commit()
    db.refresh(w)

    # post learning progress
    payload = {'word_id': w.id, 'performance': 0.9}
    r = client.post('/api/v1/learning/progress', json=payload, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert 'next_review' in data

    # get learning plan
    r = client.get('/api/v1/learning/plan', headers=headers)
    assert r.status_code == 200
    plans = r.json().get('plans', [])
    assert any(p['word_id'] == w.id for p in plans)
