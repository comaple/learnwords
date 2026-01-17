from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import status
from sqlalchemy.orm import Session
import os

from .db import engine, Base, get_db
from . import models
from .schemas import UserCreate, UserOut, Token, UploadOut
from .auth import hash_password, verify_password, create_access_token
from .auth import get_current_user
from .learning import MemoryService
from sqlalchemy.orm import Session

app = FastAPI(title='WordMem API - Skeleton')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/')
def hello():
    return {'status': 'ok', 'service': 'wordmem-backend'}


# User registration
@app.post('/api/v1/users/register', response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        # Be idempotent in registration during tests/dev: return existing user
        return existing
    user_obj = models.User(
        email=user.email,
        password_hash=hash_password(user.password),
        name=user.name
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return user_obj


@app.post('/api/v1/users/login', response_model=Token)
def login(credentials: UserCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    token = create_access_token({'sub': user.id})
    return {'access_token': token, 'token_type': 'bearer'}


# Simple upload endpoint that delegates to OCR service
@app.post('/api/v1/upload', response_model=UploadOut)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    from .ocr_service import OCRService
    contents = await file.read()
    tmp_path = f"/tmp/{file.filename}"
    with open(tmp_path, 'wb') as f:
        f.write(contents)
    ocr = OCRService()
    result = ocr.process_document(tmp_path)
    # Persist minimal upload and ocr_result
    upload = models.Upload(filename=file.filename, storage_path=tmp_path, status='done')
    db.add(upload)
    db.commit()
    db.refresh(upload)
    ocr_rec = models.OCRResult(upload_id=upload.id, raw_json=str(result), plain_text='\n'.join(result.get('words', [])), words_extracted=','.join(result.get('words', [])), count=result.get('count', 0))
    db.add(ocr_rec)
    db.commit()
    return {'upload_id': upload.id, 'words': result.get('words', []), 'count': result.get('count', 0)}



@app.get('/api/v1/learning/plan')
def get_learning_plan(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    ms = MemoryService()
    rows = ms.due_for_user(db, current_user.id)
    plans = []
    for r in rows:
        plans.append({
            'word_id': r.word_id,
            'next_review': r.next_review_at,
            'interval_hours': r.interval_hours,
            'review_count': r.review_count
        })
    return {'plans': plans}


@app.post('/api/v1/learning/progress')
def post_learning_progress(payload: dict, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.id
    word_id = payload.get('word_id')
    performance = float(payload.get('performance', 0.0))
    if not word_id:
        raise HTTPException(status_code=400, detail='word_id required')
    ms = MemoryService()
    res = ms.update_progress(db, user_id, word_id, performance)
    return {'next_review': res['next_review'], 'interval_hours': res['interval_hours']}
