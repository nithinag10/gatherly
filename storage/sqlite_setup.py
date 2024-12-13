import sqlite3
from pathlib import Path

def init_db():
    """Initialize SQLite database with required tables"""
    db_path = Path("storage/chat_db.sqlite")
    db_path.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create tables
    cursor.executescript('''
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );

        -- Chats table
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            admin_id TEXT NOT NULL,
            FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- Chat participants (many-to-many relationship between chats and users)
        CREATE TABLE IF NOT EXISTS chat_participants (
            chat_id TEXT,
            user_id TEXT,
            PRIMARY KEY (chat_id, user_id),
            FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- Messages table
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            chat_id TEXT NOT NULL,
            sender_id TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE,
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- Create indexes for better query performance
        CREATE INDEX IF NOT EXISTS idx_chat_participants_chat_id 
        ON chat_participants(chat_id);
        
        CREATE INDEX IF NOT EXISTS idx_chat_participants_user_id 
        ON chat_participants(user_id);
        
        CREATE INDEX IF NOT EXISTS idx_messages_chat_id 
        ON messages(chat_id);
        
        CREATE INDEX IF NOT EXISTS idx_messages_sender_id 
        ON messages(sender_id);
        
        CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
        ON messages(timestamp);
    ''')

    conn.commit()
    conn.close()

def reset_db():
    """Reset the database by dropping all tables"""
    db_path = Path("storage/chat_db.sqlite")
    
    if not db_path.exists():
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.executescript('''
        DROP TABLE IF EXISTS messages;
        DROP TABLE IF EXISTS chat_participants;
        DROP TABLE IF EXISTS chats;
        DROP TABLE IF EXISTS users;
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Reset and initialize the database
    reset_db()
    init_db()
    print("Database initialized successfully!") 