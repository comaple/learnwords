import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import SessionLocal
from backend.app import models

c = TestClient(app)
# register
r = c.post('/api/v1/users/register', json={'email':'t@example.com','password':'pass','name':'T'})
print('register', r.status_code, r.json())
# login
r = c.post('/api/v1/users/login', json={'email':'t@example.com','password':'pass','name':'T'})
print('login', r.status_code, r.json())
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}
# Monkeypatch OCRService.process_document by replacing attribute
import backend.app.ocr_service as ocr_mod
ocr_mod.OCRService.process_document = lambda self, path: {'words': ['apple', 'banana'], 'count': 2, 'raw_result': {}}
# upload
files = {'file': ('f.txt', b'hello', 'text/plain')}
r = c.post('/api/v1/upload', files=files)
print('upload', r.status_code, r.json())
# create/get word
db = SessionLocal()
existing = db.query(models.Word).filter(models.Word.lemma=='apple').first()
if not existing:
    w = models.Word(lemma='apple')
    db.add(w)
    db.commit()
    db.refresh(w)
else:
    w = existing
print('word id', w.id)
# post progress
r = c.post('/api/v1/learning/progress', json={'word_id': w.id, 'performance': 0.9}, headers=headers)
print('progress', r.status_code, r.json())
# inspect user_words
user = db.query(models.User).filter(models.User.email=='t@example.com').first()
print('user', user.id)
uws = db.query(models.UserWord).filter(models.UserWord.user_id==user.id).all()
print('user_words count', len(uws))
for uw in uws:
    print('uw', uw.id, uw.user_id, uw.word_id, uw.next_review_at)
# get plan
r = c.get('/api/v1/learning/plan', headers=headers)
print('plan', r.status_code, r.json())
