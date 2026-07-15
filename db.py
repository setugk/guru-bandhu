import json
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = Path(__file__).parent / 'data' / 'guru-app.db'


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            teacher_name TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS kv (
            account_id INTEGER NOT NULL REFERENCES accounts(id),
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (account_id, key)
        )
    ''')
    conn.commit()
    conn.close()


def create_account(username, password, teacher_name):
    """Self-service signup: fails (returns None) if the username is already taken."""
    conn = get_db()
    password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    try:
        cur = conn.execute(
            'INSERT INTO accounts (username, password_hash, teacher_name) VALUES (?, ?, ?)',
            (username, password_hash, teacher_name)
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def create_or_update_account(username, password, teacher_name):
    conn = get_db()
    password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    conn.execute(
        "INSERT INTO accounts (username, password_hash, teacher_name) VALUES (?, ?, ?) "
        "ON CONFLICT(username) DO UPDATE SET password_hash = excluded.password_hash, teacher_name = excluded.teacher_name",
        (username, password_hash, teacher_name)
    )
    conn.commit()
    row = conn.execute('SELECT id FROM accounts WHERE username = ?', (username,)).fetchone()
    conn.close()
    return row['id']


def verify_login(username, password):
    conn = get_db()
    row = conn.execute('SELECT id, password_hash, teacher_name FROM accounts WHERE username = ?', (username,)).fetchone()
    conn.close()
    if row and check_password_hash(row['password_hash'], password):
        return {'id': row['id'], 'teacher_name': row['teacher_name']}
    return None


def get_account(account_id):
    conn = get_db()
    row = conn.execute('SELECT username, teacher_name FROM accounts WHERE id = ?', (account_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return {'username': row['username'], 'teacher_name': row['teacher_name']}


def get_state(account_id):
    conn = get_db()
    account = conn.execute('SELECT teacher_name FROM accounts WHERE id = ?', (account_id,)).fetchone()
    rows = conn.execute('SELECT key, value FROM kv WHERE account_id = ?', (account_id,)).fetchall()
    conn.close()
    state = {row['key']: json.loads(row['value']) for row in rows}
    state.setdefault('students', [])
    state.setdefault('settings', {})
    # Pre-fill the teacher name from signup until the guru explicitly saves their own Settings value.
    if not state['settings'].get('teacherName') and account and account['teacher_name']:
        state['settings']['teacherName'] = account['teacher_name']
    return state


def set_kv(account_id, key, value):
    conn = get_db()
    conn.execute(
        "INSERT INTO kv (account_id, key, value, updated_at) VALUES (?, ?, ?, datetime('now')) "
        "ON CONFLICT(account_id, key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
        (account_id, key, json.dumps(value))
    )
    conn.commit()
    conn.close()
