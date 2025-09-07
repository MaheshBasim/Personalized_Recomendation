import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect('database/auth.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Insert admin user
    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ('admin', generate_password_hash('admin123'))
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully")