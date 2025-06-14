import sqlite3, hashlib
from database import get_connection

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?,?)",
                  (username, hash_password(password)))
        conn.commit(); return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    res = c.fetchone(); conn.close()
    return res[0] if res else None

def update_username(user_id, new_username):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("UPDATE users SET username=? WHERE id=?", (new_username, user_id))
        conn.commit(); return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_password(user_id, new_password):
    conn = get_connection(); c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE id=?",
              (hash_password(new_password), user_id))
    conn.commit(); conn.close()
    return True
