import sqlite3
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def connect(path):
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA secure_delete=ON')
    try:
        with db:
            yield db
    finally:
        db.close()


def init_db(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                version TEXT NOT NULL CHECK(version IN ('v1','v2','v3','v4','v5')),
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
                UNIQUE(username, version)
            );
            CREATE TABLE IF NOT EXISTS captures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                fictional_password TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
            );
        ''')


def list_users(path, version=None):
    with connect(path) as db:
        if version:
            return db.execute('SELECT * FROM users WHERE version=? ORDER BY id', (version,)).fetchall()
        return db.execute('SELECT * FROM users ORDER BY version, id').fetchall()


def reset_db(path):
    with connect(path) as db:
        db.execute('DELETE FROM users')
        db.execute('DELETE FROM captures')
        # Preserve monotonically increasing IDs: an old cookie must never inherit
        # a new account after a CLI reset while the server is still running.
    # Reclaim free pages; this is not a secure erase of backups or SSD snapshots.
    with connect(path) as db:
        db.execute('VACUUM')
