"""
auth_service.py - Authentication, Session Security & User Database Engine for WeatherGPT
Provides persistent SQLite storage for user profiles, credentials, logins, and audit trails.
"""

import sqlite3
import hashlib
import hmac
import secrets
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Database persistence location
DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "weathergpt.db"


def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection configured for WAL mode and row factory."""
    conn = sqlite3.connect(str(DB_PATH), timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    """Initializes tables for users, sessions, and activity logs."""
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT DEFAULT 'Farmer',
            phone TEXT,
            state TEXT DEFAULT 'Uttar Pradesh',
            district TEXT DEFAULT 'Lucknow',
            village TEXT,
            primary_crop TEXT DEFAULT 'Wheat',
            preferred_language TEXT DEFAULT 'en',
            created_at TEXT NOT NULL,
            updated_at TEXT,
            last_login_at TEXT,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS user_sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            user_email TEXT,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(token);
        CREATE INDEX IF NOT EXISTS idx_activity_logs_time ON activity_logs(timestamp);
        """)
    print(f"[AUTH] SQLite Database initialized at: {DB_PATH}")


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Hashes password with PBKDF2-HMAC-SHA256 and salt."""
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations=100000
    )
    return key.hex(), salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Timing-safe password verification."""
    computed_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, expected_hash)


def log_activity(conn: sqlite3.Connection, user_id: Optional[int], email: str, action: str, details: str = ""):
    """Records an activity event into the database with exact timestamp."""
    now_utc = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO activity_logs (user_id, user_email, action, details, timestamp) VALUES (?, ?, ?, ?, ?)",
        (user_id, email, action, details, now_utc)
    )


def register_user(
    name: str,
    email: str,
    password: str,
    role: str = "Farmer",
    phone: Optional[str] = None,
    state: Optional[str] = "Uttar Pradesh",
    district: Optional[str] = "Lucknow",
    village: Optional[str] = None,
    primary_crop: Optional[str] = "Wheat",
    preferred_language: Optional[str] = "en"
) -> Tuple[Dict[str, Any], str]:
    """
    Registers a new user into SQLite, logs the record time, and creates an active session.
    Returns (user_dict, token).
    """
    clean_email = email.strip().lower()
    now_utc = datetime.now(timezone.utc).isoformat()
    pwd_hash, salt = hash_password(password)

    with get_connection() as conn:
        # Check if email already exists
        cur = conn.execute("SELECT id FROM users WHERE email = ?", (clean_email,))
        if cur.fetchone():
            raise ValueError(f"An account with email '{clean_email}' already exists. Please switch to 'Sign In' or use 'Reset Password'.")

        cur = conn.execute("""
            INSERT INTO users (
                name, email, password_hash, salt, role, phone,
                state, district, village, primary_crop, preferred_language,
                created_at, updated_at, last_login_at, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            name.strip(), clean_email, pwd_hash, salt, role, phone,
            state, district, village, primary_crop, preferred_language,
            now_utc, now_utc, now_utc
        ))
        user_id = cur.lastrowid

        # Generate session token (30 days)
        token = secrets.token_urlsafe(36)
        expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        conn.execute(
            "INSERT INTO user_sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, user_id, now_utc, expires_at)
        )

        # Audit log creation
        log_activity(
            conn, user_id, clean_email, "REGISTER",
            f"Account created for {name} ({role}) in {district}, {state}. Crop: {primary_crop}"
        )

        user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        sync_readable_export()
        return dict(user_row), token


def authenticate_user(email: str, password: str) -> Tuple[Dict[str, Any], str]:
    """
    Validates user credentials, records login timestamp, and issues new session token.
    Returns (user_dict, token).
    """
    clean_email = email.strip().lower()
    now_utc = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (clean_email,)).fetchone()
        if not row:
            log_activity(conn, None, clean_email, "LOGIN_FAILED", "User not found or inactive")
            raise ValueError("No account found with this email. Please switch to 'Create Account' to register.")

        if not verify_password(password, row["salt"], row["password_hash"]):
            log_activity(conn, row["id"], clean_email, "LOGIN_FAILED", "Incorrect password")
            raise ValueError("Incorrect password. Please re-enter your password or click 'Forgot / Reset Password'.")

        # Update last_login_at
        conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (now_utc, row["id"]))

        # Create session token
        token = secrets.token_urlsafe(36)
        expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        conn.execute(
            "INSERT INTO user_sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, row["id"], now_utc, expires_at)
        )

        log_activity(conn, row["id"], clean_email, "LOGIN", f"Successful login at {now_utc}")
        updated_row = conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()
        sync_readable_export()
        return dict(updated_row), token


def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    """Retrieves user profile associated with an active, unexpired session token."""
    now_utc = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        query = """
            SELECT u.* FROM users u
            JOIN user_sessions s ON u.id = s.user_id
            WHERE s.token = ? AND s.expires_at > ? AND u.is_active = 1
        """
        row = conn.execute(query, (token, now_utc)).fetchone()
        return dict(row) if row else None


def update_profile(user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Updates user profile attributes, records updated_at timestamp, and logs activity."""
    allowed_fields = [
        "name", "phone", "role", "state", "district", "village",
        "primary_crop", "preferred_language"
    ]
    set_clauses = []
    values = []

    for field in allowed_fields:
        if field in updates and updates[field] is not None:
            set_clauses.append(f"{field} = ?")
            values.append(updates[field])

    if not set_clauses:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(row) if row else {}

    now_utc = datetime.now(timezone.utc).isoformat()
    set_clauses.append("updated_at = ?")
    values.append(now_utc)
    values.append(user_id)

    with get_connection() as conn:
        conn.execute(f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?", values)
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row:
            log_activity(conn, user_id, row["email"], "UPDATE_PROFILE", f"Updated fields: {list(updates.keys())}")
            sync_readable_export()
            return dict(row)
        raise ValueError("User not found.")


def logout_user(token: str):
    """Terminates session by deleting token from database."""
    with get_connection() as conn:
        session = conn.execute("SELECT user_id FROM user_sessions WHERE token = ?", (token,)).fetchone()
        if session:
            conn.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
            user = conn.execute("SELECT email FROM users WHERE id = ?", (session["user_id"],)).fetchone()
            email = user["email"] if user else "unknown"
            log_activity(conn, session["user_id"], email, "LOGOUT", "Session revoked successfully")


def get_all_users_for_admin() -> List[Dict[str, Any]]:
    """Returns list of registered users with record timestamps (excluding sensitive hash/salt)."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, name, email, role, phone, state, district, village,
                   primary_crop, preferred_language, created_at, last_login_at, updated_at
            FROM users
            ORDER BY id DESC
        """).fetchall()
        return [dict(r) for r in rows]


def get_activity_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """Returns chronological audit logs of user actions with timestamps."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, user_id, user_email, action, details, timestamp
            FROM activity_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


def reset_password(email: str, new_password: str) -> Dict[str, Any]:
    """Updates password hash and salt for given user email."""
    clean_email = email.strip().lower()
    if len(new_password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    
    pwd_hash, salt = hash_password(new_password)
    now_utc = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        row = conn.execute("SELECT id, name FROM users WHERE email = ? AND is_active = 1", (clean_email,)).fetchone()
        if not row:
            raise ValueError(f"No account found with email '{clean_email}'. Please register first.")
        
        conn.execute(
            "UPDATE users SET password_hash = ?, salt = ?, updated_at = ? WHERE id = ?",
            (pwd_hash, salt, now_utc, row["id"])
        )
        # Invalidate old sessions
        conn.execute("DELETE FROM user_sessions WHERE user_id = ?", (row["id"],))
        log_activity(conn, row["id"], clean_email, "RESET_PASSWORD", f"Password reset successfully at {now_utc}")
        updated = conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()
        sync_readable_export()
        return dict(updated)


def sync_readable_export():
    """Maintains a human-readable JSON mirror at backend/data/registered_users_log.json."""
    try:
        users = get_all_users_for_admin()
        logs = get_activity_logs(50)
        export_file = DB_DIR / "registered_users_log.json"
        with open(export_file, "w", encoding="utf-8") as f:
            json.dump({
                "description": "Human-Readable Live Mirror of Registered WeatherGPT Users & Telemetry Timestamps",
                "database_file": str(DB_PATH),
                "total_users": len(users),
                "last_synced_utc": datetime.now(timezone.utc).isoformat(),
                "users": users,
                "recent_activity_logs": logs
            }, f, indent=2)
    except Exception as e:
        print(f"[AUTH] Readable export notice: {e}")


