from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi import status
from sqlalchemy.orm import Session
import os

from .db import engine, Base, get_db, SessionLocal
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
async def upload_file(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks(), db: Session = Depends(get_db)):
    from .ocr_service import OCRService
    contents = await file.read()
    tmp_path = f"/tmp/{file.filename}"
    with open(tmp_path, 'wb') as f:
        f.write(contents)
    # Persist minimal upload with pending status and schedule background OCR
    upload = models.Upload(filename=file.filename, storage_path=tmp_path, status='pending')
    db.add(upload)
    db.commit()
    db.refresh(upload)

    def _process_background(u_id: str, path: str):
        db2 = SessionLocal()
        try:
            ocr = OCRService()
            result = ocr.process_document(path)
            ocr_rec = models.OCRResult(upload_id=u_id, raw_json=str(result), plain_text='\n'.join(result.get('words', [])), words_extracted=','.join(result.get('words', [])), count=result.get('count', 0))
            db2.add(ocr_rec)
            up = db2.query(models.Upload).filter(models.Upload.id == u_id).first()
            if up:
                up.status = 'done'
            db2.commit()
        except Exception:
            up = db2.query(models.Upload).filter(models.Upload.id == u_id).first()
            if up:
                up.status = 'error'
            db2.commit()
        finally:
            db2.close()

    # schedule background processing
    background_tasks.add_task(_process_background, upload.id, tmp_path)
    return {'upload_id': upload.id, 'words': [], 'count': 0}


@app.get('/api/v1/upload/{upload_id}')
def get_upload(upload_id: str, db: Session = Depends(get_db)):
    up = db.query(models.Upload).filter(models.Upload.id == upload_id).first()
    if not up:
        raise HTTPException(status_code=404, detail='Upload not found')
    ocr_rec = db.query(models.OCRResult).filter(models.OCRResult.upload_id == up.id).first()
    words = []
    count = 0
    if ocr_rec:
        words = ocr_rec.words_extracted.split(',') if ocr_rec.words_extracted else []
        count = ocr_rec.count or 0
    return {'upload_id': up.id, 'status': up.status, 'words': words, 'count': count}



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
