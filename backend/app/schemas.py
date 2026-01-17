from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str]

class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str]
    created_at: Optional[datetime]

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'

class UploadOut(BaseModel):
    upload_id: str
    words: List[str]
    count: int
