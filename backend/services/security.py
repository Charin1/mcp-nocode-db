import os
import sqlite3
import yaml
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from models.auth import User, UserInDB, TokenData

# --- Configuration ---
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

# --- User Database Functions ---


def get_db_path():
    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)
    return config["metadata_db"]["path"]


def _create_users_table_if_not_exists():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        hashed_password TEXT NOT NULL,
        role TEXT NOT NULL,
        disabled BOOLEAN NOT NULL
    )
    """
    )
    conn.commit()
    conn.close()


def get_user(username: str) -> Optional[UserInDB]:
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user_row = cursor.fetchone()
    conn.close()
    if user_row:
        return UserInDB(**user_row)
    return None


def add_user(user: UserInDB):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, hashed_password, role, disabled) VALUES (?, ?, ?, ?)",
            (user.username, user.hashed_password, user.role, user.disabled),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return None  # User already exists
    conn.close()
    return user


def get_total_users() -> int:
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(username) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count


# --- Password and Auth Logic ---


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str) -> Optional[User]:
    user = get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return User(username=user.username, role=user.role, disabled=user.disabled)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- Dependency for getting current user ---


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    access_token: Optional[str] = Cookie(None),
) -> User:
    """
    Validates the user. Checks the 'Authorization' header first (via oauth2_scheme),
    then falls back to the 'access_token' cookie.
    """
    if token is None:
        token = access_token

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role", "viewer")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = get_user(token_data.username)
    if user is None or user.disabled:
        raise credentials_exception

    return User(username=user.username, role=user.role, disabled=user.disabled)


# --- Dependency for Role-Based Access Control ---


def has_role(required_role: str):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Requires '{required_role}' role.",
            )
        return current_user

    return role_checker


# --- User Registration ---


def register_new_user(email: str, password: str) -> Optional[UserInDB]:
    _create_users_table_if_not_exists()

    if get_user(email):
        return None  # User already exists

    hashed_password = get_password_hash(password)

    # First user becomes admin
    role = "admin" if get_total_users() == 0 else "viewer"

    new_user = UserInDB(
        username=email, hashed_password=hashed_password, role=role, disabled=False
    )

    return add_user(new_user)


def create_initial_admin_user():
    """Creates a default admin user if no users exist."""
    _create_users_table_if_not_exists()
    if get_total_users() == 0:
        email = "admin@example.com"
        password = "password"
        user = register_new_user(email, password)
        if user:
            print(
                f"--- First user '{email}' created with role 'admin'. Password is '{password}'. ---"
            )
        else:
            print(f"--- Admin user '{email}' already exists. ---")
