import datetime
import pydantic 
from typing import List, Optional


class UserBase(pydantic.BaseModel):
    name: str
    email: str
    api_key : Optional[str] = None 
    organisation: Optional[str] = None  # Mark organisation as optional
    class Config:
       from_attributes=True

class UserCreate(UserBase):
    password: str
    class Config:
       from_attributes=True

class User(UserBase):
    id: int
    date_created: datetime.datetime
    class Config:
       from_attributes=True


class GenerateUserToken(pydantic.BaseModel):
    username: str
    password: str
    class Config:
        from_attributes=True

class GenerateOtp(pydantic.BaseModel):
    email: str
    
class VerifyOtp(pydantic.BaseModel):
    email: str
    otp: int


class Watchlist(pydantic.BaseModel):
    stock_symbol: str
    stock_name: str


class profileUpdate(pydantic.BaseModel):
    name: str
    api_key : Optional[str] = None 
    organisation: Optional[str] = None  # Mark organisation as optional
    class Config:
       from_attributes=True