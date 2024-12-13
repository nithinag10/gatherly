from flask import Flask
from entities.Chat import Chat
from entities.Message import Message
from entities.User import User
from repositories.UserRepository import UserRepository
from repositories.ChatRepository import ChatRepository
from services.ChatService import ChatService
from storage.sqlite_setup import init_db, reset_db
import uuid
import sqlite3

app = Flask(__name__)

@app.route('/')
def home():
    return 'Welcome to the Flask Server!'

@app.route('/health')
def help():
    return '''
        Its healthy
    '''

def test_chat_system():
    """Test function to demonstrate chat system functionality"""
    
    # Initialize repositories and service
    user_repo = UserRepository()
    chat_repo = ChatRepository()
    chat_service = ChatService(chat_repo, user_repo)

    # Create test users
    users = [
        User(id="user1", name="Alice"),
        User(id="user2", name="Bob"),
        User(id="user3", name="Charlie")
    ]
    
    print("\n=== Creating Users ===")
    for user in users:
        user_repo.save_user(user)
        print(f"Created user: {user.name} (ID: {user.id})")

    # Test chat creation
    print("\n=== Creating Chat ===")
    chat, message = chat_service.create_chat("user1", "chat1")
    print(f"Create chat result: {message}")

    # Test joining chat
    print("\n=== Users Joining Chat ===")
    for user in ["user2", "user3"]:
        success, message = chat_service.join_chat(user, "chat1")
        print(f"{user} joining chat: {message}")

    # Test sending messages
    print("\n=== Sending Messages ===")
    messages = [
        ("user1", "Hello everyone!"),
        ("user2", "Hi Alice!"),
        ("user3", "Hey folks!"),
        ("user1", "How are you all doing?"),
    ]
    
    for user_id, content in messages:
        success, message = chat_service.send_message(user_id, "chat1", content)
        print(f"Message from {user_id}: {content} - {message}")

    # Test chat summary
    print("\n=== Chat Summary ===")
    summary, message = chat_service.get_chat_summary("chat1")
    if summary:
        print(f"Chat ID: {summary['id']}")
        print(f"Admin: {summary['admin_id']}")
        print(f"Participants: {summary['participant_count']}")
        print(f"Total messages: {summary['message_count']}")
        print("\nRecent messages:")
        for msg in summary['recent_messages']:
            print(f"{msg.sender_id}: {msg.content}")

def test_sqlite_chat():
    # Initialize database
    init_db()
    
    # Create repository
    chat_repo = ChatRepository()
    
    # Create a new chat
    chat_id = str(uuid.uuid4())
    chat = Chat(
        id=chat_id,
        admin_id="user1",
        participants=["user1", "user2"]
    )
    
    # Save chat
    chat_repo.save_chat(chat)
    
    # Add a message
    message = Message(
        id=str(uuid.uuid4()),
        sender_id="user1",
        content="Hello, SQLite!"
    )
    chat_repo.add_message(chat_id, message)
    
    # Get chat summary
    summary = chat_repo.get_chat_summary(chat_id)
    print("Chat Summary:", summary)

def test_db_setup():
    # Reset and initialize the database
    reset_db()
    init_db()
    
    # Connect and insert some test data
    conn = sqlite3.connect("storage/chat_db.sqlite")
    cursor = conn.cursor()
    
    try:
        # Insert test user
        cursor.execute(
            "INSERT INTO users (id, name) VALUES (?, ?)",
            ("user1", "John Doe")
        )
        
        # Insert test chat
        cursor.execute(
            "INSERT INTO chats (id, admin_id) VALUES (?, ?)",
            ("chat1", "user1")
        )
        
        # Add user as participant
        cursor.execute(
            "INSERT INTO chat_participants (chat_id, user_id) VALUES (?, ?)",
            ("chat1", "user1")
        )
        
        # Add test message
        cursor.execute("""
            INSERT INTO messages (id, chat_id, sender_id, content) 
            VALUES (?, ?, ?, ?)
        """, ("msg1", "chat1", "user1", "Hello, World!"))
        
        conn.commit()
        print("Test data inserted successfully!")
        
    except sqlite3.Error as e:
        print(f"Error: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def test_repositories():
    """Test all repository operations"""
    print("\n=== Starting Repository Tests ===")
    
    # Reset and initialize database
    print("\nResetting and initializing database...")
    reset_db()
    init_db()
    
    # Initialize repositories
    user_repo = UserRepository()
    chat_repo = ChatRepository()
    
    # Test User Repository Operations
    print("\n=== Testing User Repository ===")
    
    # Create users
    users = [
        User(id="user1", name="Alice"),
        User(id="user2", name="Bob"),
        User(id="user3", name="Charlie")
    ]
    
    print("\nCreating users...")
    for user in users:
        saved_user = user_repo.save_user(user)
        print(f"Created user: {saved_user.name} (ID: {saved_user.id})")
    
    # Retrieve users
    print("\nRetrieving users...")
    for user_id in ["user1", "user2", "user3"]:
        user = user_repo.get_user_by_id(user_id)
        print(f"Retrieved user: {user.name} (ID: {user.id})")
    
    # Test Chat Repository Operations
    print("\n=== Testing Chat Repository ===")
    
    # Create chat
    chat = Chat(
        id="chat1",
        admin_id="user1",
        participants=["user1"]
    )
    
    print("\nCreating chat...")
    saved_chat = chat_repo.save_chat(chat)
    print(f"Created chat: {saved_chat.id} (Admin: {saved_chat.admin_id})")
    
    # Add participants
    print("\nAdding participants...")
    for user_id in ["user2", "user3"]:
        success = chat_repo.add_participant("chat1", user_id)
        print(f"Added {user_id} to chat: {success}")
    
    # Add messages
    print("\nAdding messages...")
    messages = [
        ("Hello everyone!", "user1"),
        ("Hi Alice!", "user2"),
        ("Hey folks!", "user3")
    ]
    
    for content, sender_id in messages:
        message = Message(
            id=str(uuid.uuid4()),
            sender_id=sender_id,
            content=content
        )
        success = chat_repo.add_message("chat1", message)
        print(f"Message from {sender_id}: {content} - Success: {success}")
    
    # Get chat summary
    print("\nGetting chat summary...")
    summary = chat_repo.get_chat_summary("chat1")
    if summary:
        print(f"Chat ID: {summary['id']}")
        print(f"Admin: {summary['admin_id']}")
        print(f"Participants: {summary['participant_count']}")
        print(f"Total messages: {summary['message_count']}")
        print("\nRecent messages:")
        for msg in summary['recent_messages']:
            print(f"{msg.sender_id}: {msg.content}")
    
    # Get user's chats
    print("\nGetting user's chats...")
    user_chats = chat_repo.get_user_chats("user1")
    print(f"User1's chats: {len(user_chats)}")
    
    # Test deletion
    print("\n=== Testing Deletion ===")
    
    # Delete chat
    success = chat_repo.delete_chat("chat1")
    print(f"Deleted chat: {success}")
    
    # Delete user
    success = user_repo.delete_user("user3")
    print(f"Deleted user: {success}")
    
    print("\n=== Repository Tests Completed ===")

if __name__ == '__main__':
    # Initialize database tables
    init_db()

    # Run all tests
    test_repositories()  # Test basic repository operations
    test_chat_system()   # Test chat system with service layer
    test_sqlite_chat()   # Test SQLite-specific operations
    test_db_setup()      # Test database setup and raw SQL operations
    
    # Start Flask server
    app.run(debug=True)
