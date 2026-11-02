"""
TradeLens AI - Authentication & Token Security Engine
NIST-compliant PBKDF2-HMAC-SHA256 password hashing and HMAC signed tokens.
Zero external crypto dependency; safe and portable across all platforms.
"""
import os
import hashlib
import hmac
import base64
import json
import time
import uuid
from typing import Optional, Dict, Any, Tuple
from app.database import db

JWT_SECRET = os.getenv("JWT_SECRET", "tradelens-ai-super-secret-production-key-2026")
TOKEN_EXPIRY_SECONDS = 7 * 24 * 3600  # 7 days

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """
    PBKDF2-HMAC-SHA256 password hash with 100,000 iterations.
    """
    if not salt:
        salt = os.urandom(16).hex()
    pwd_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
    return f"{salt}${key.hex()}"

def verify_password(plain_password: str, hashed_str: str) -> bool:
    try:
        parts = hashed_str.split('$')
        if len(parts) != 2:
            return False
        salt, _ = parts
        computed = hash_password(plain_password, salt)
        return hmac.compare_digest(computed, hashed_str)
    except Exception:
        return False

def create_access_token(user_id: str, email: str, full_name: str) -> str:
    """
    Creates an HMAC-SHA256 signed bearer token.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "name": full_name,
        "exp": int(time.time()) + TOKEN_EXPIRY_SECONDS,
        "iat": int(time.time())
    }

    b64_header = base64.urlsafe_b64encode(json.dumps(header).encode('utf-8')).decode('utf-8').rstrip('=')
    b64_payload = base64.urlsafe_b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8').rstrip('=')
    signature_data = f"{b64_header}.{b64_payload}".encode('utf-8')
    signature = hmac.new(JWT_SECRET.encode('utf-8'), signature_data, hashlib.sha256).digest()
    b64_sig = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')

    return f"{b64_header}.{b64_payload}.{b64_sig}"

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies token signature and checks expiration.
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        b64_header, b64_payload, b64_sig = parts
        signature_data = f"{b64_header}.{b64_payload}".encode('utf-8')
        expected_sig = hmac.new(JWT_SECRET.encode('utf-8'), signature_data, hashlib.sha256).digest()
        
        # Add padding back if necessary
        pad_len = 4 - (len(b64_sig) % 4)
        if pad_len and pad_len < 4:
            b64_sig_padded = b64_sig + ('=' * pad_len)
        else:
            b64_sig_padded = b64_sig

        actual_sig = base64.urlsafe_b64decode(b64_sig_padded.encode('utf-8'))
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        # Decode payload
        payload_pad = 4 - (len(b64_payload) % 4)
        if payload_pad and payload_pad < 4:
            b64_payload += '=' * payload_pad
        payload_data = json.loads(base64.urlsafe_b64decode(b64_payload.encode('utf-8')).decode('utf-8'))

        if payload_data.get('exp', 0) < time.time():
            return None # Expired

        return payload_data
    except Exception:
        return None

def register_user(email: str, password: str, full_name: str, is_demo: bool = False) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    email_clean = email.strip().lower()
    if not email_clean or '@' not in email_clean:
        return False, "Invalid email address.", None
    if len(password) < 6:
        return False, "Password must be at least 6 characters.", None

    hashed = hash_password(password)
    user_id = f"USR-{uuid.uuid4().hex[:8]}"

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email_clean,))
        if cursor.fetchone():
            return False, "An account with this email already exists.", None

        cursor.execute(
            "INSERT INTO users (id, email, hashed_password, full_name, is_demo) VALUES (?, ?, ?, ?, ?)",
            (user_id, email_clean, hashed, full_name.strip(), 1 if is_demo else 0)
        )

        # Create default portfolio
        port_id = f"PORT-{uuid.uuid4().hex[:8]}"
        cursor.execute(
            "INSERT INTO portfolios (id, user_id, name, broker_name, description) VALUES (?, ?, ?, ?, ?)",
            (port_id, user_id, "Main Indian F&O & Equity Portfolio", "Zerodha", "Primary trading ledger")
        )

        conn.commit()

    token = create_access_token(user_id, email_clean, full_name.strip())
    return True, "Registration successful.", {
        "user_id": user_id,
        "email": email_clean,
        "full_name": full_name.strip(),
        "token": token,
        "portfolio_id": port_id
    }

def authenticate_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    email_clean = email.strip().lower()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, hashed_password, full_name, is_demo FROM users WHERE email = ?", (email_clean,))
        row = cursor.fetchone()
        if not row:
            return False, "Invalid email or password.", None

        if not verify_password(password, row['hashed_password']):
            return False, "Invalid email or password.", None

        # Fetch primary portfolio
        cursor.execute("SELECT id FROM portfolios WHERE user_id = ? LIMIT 1", (row['id'],))
        port = cursor.fetchone()
        port_id = port['id'] if port else None

        token = create_access_token(row['id'], row['email'], row['full_name'])
        return True, "Login successful.", {
            "user_id": row['id'],
            "email": row['email'],
            "full_name": row['full_name'],
            "token": token,
            "portfolio_id": port_id,
            "is_demo": bool(row['is_demo'])
        }
