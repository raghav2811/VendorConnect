import os
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional
from models import User, UserCreate
from database import Database

class AuthService:
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-this")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60 * 24  # 24 hours
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.db = Database()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return self.pwd_context.hash(password)

    def create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = await self.db.get_user_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    async def create_user(self, user_create: UserCreate) -> User:
        """Create a new user with hashed password"""
        hashed_password = self.get_password_hash(user_create.password)
        return await self.db.create_user(user_create, hashed_password)

    def decode_token(self, token: str) -> Optional[dict]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None 