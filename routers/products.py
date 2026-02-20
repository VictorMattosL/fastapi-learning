import sys
import os

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, field_validator, EmailStr

from typing import List, Optional
from enum import Enum

from sqlalchemy.orm import Session
from data.database import get_db
from data import models

from datetime import timedelta, datetime
from jose import JWTError, jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import secrets

router = APIRouter()

SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

ph = PasswordHasher()

def verify_password(plain_password, hashed_password):
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False

def get_password_hash(password):
    return ph.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
        
    return user

class ProdutoBase(BaseModel):
    name: str
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    
    @field_validator('name')
    @classmethod
    def check_name(cls, v: str):
        if "teste" in v.lower():
            raise ValueError("name can't contain 'teste'")
        return v

class ProdutoCreate(ProdutoBase):
    pass

class Produto(ProdutoBase):
    id: int
    class Config:
        from_attributes = True

class ProdutoPublic(BaseModel):
    id: int
    name: str
    price: float
    stock: int

class Sort_by(str, Enum):
    op_1 = "id"
    op_2 = "name"
    op_3 = "price"
    op_4 = "stock"

class Order(str, Enum):
    op_1 = "asc"
    op_2 = "desc"

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    
    class Config:
        from_attributes = True

class UserPublic(UserBase):
    id: int
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/products", status_code=201, response_model=Produto)
def add_product(
    produto: ProdutoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_product = models.Product(
        name=produto.name, 
        price=produto.price, 
        stock=produto.stock,
        description="Descrição padrão"
    )
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    return db_product

@router.get("/products", status_code=200, response_model=List[ProdutoPublic])
def all_products(
    db: Session = Depends(get_db),
    choice: Sort_by = Sort_by.op_1, 
    order: Order = Order.op_1, 
    min_price: Optional[float] = None, 
    max_price: Optional[float] = None, 
    search: Optional[str] = None, 
    skip: int = 0, 
    limit: int = 10
):
    query = db.query(models.Product)

    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)
    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)
    if search is not None:
        query = query.filter(models.Product.name.ilike(f"%{search}%"))

    if order == Order.op_2:
        if choice == Sort_by.op_2: query = query.order_by(models.Product.name.desc())
        elif choice == Sort_by.op_3: query = query.order_by(models.Product.price.desc())
        elif choice == Sort_by.op_4: query = query.order_by(models.Product.stock.desc())
        else: query = query.order_by(models.Product.id.desc())
    else:
        if choice == Sort_by.op_2: query = query.order_by(models.Product.name.asc())
        elif choice == Sort_by.op_3: query = query.order_by(models.Product.price.asc())
        elif choice == Sort_by.op_4: query = query.order_by(models.Product.stock.asc())
        else: query = query.order_by(models.Product.id.asc())

    return query.offset(skip).limit(limit).all()

@router.get("/products/{product_id}", status_code=200, response_model=ProdutoPublic)
def search_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/products/{product_id}", status_code=200, response_model=ProdutoPublic)
def update_product(product_id: int, updated_product: ProdutoCreate, db: Session = Depends(get_db)):
    product_query = db.query(models.Product).filter(models.Product.id == product_id)
    product = product_query.first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product_query.update(updated_product.dict(), synchronize_session=False)
    db.commit()
    db.refresh(product)
    return product

@router.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return

@router.post("/users/", response_model=UserPublic)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        is_admin=False
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "is_admin": user.is_admin},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}