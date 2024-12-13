import pytest
from app import create_app
import json

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_create_chat(client):
    """Test chat creation"""
    response = client.post('/api/chats', 
        json={
            'creator_id': 'user1',
            'chat_id': 'test_chat'
        }
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'chat' in data
    assert data['chat']['id'] == 'test_chat'

def test_join_chat(client):
    """Test joining a chat"""
    # First create a chat
    client.post('/api/chats', 
        json={
            'creator_id': 'user1',
            'chat_id': 'test_chat'
        }
    )
    
    # Then try to join it
    response = client.post('/api/chats/test_chat/join',
        json={'user_id': 'user2'}
    )
    assert response.status_code == 200

def test_send_message(client):
    """Test sending a message"""
    # Create chat and join
    client.post('/api/chats', 
        json={
            'creator_id': 'user1',
            'chat_id': 'test_chat'
        }
    )
    
    # Send message
    response = client.post('/api/chats/test_chat/messages',
        json={
            'user_id': 'user1',
            'content': 'Hello, World!'
        }
    )
    assert response.status_code == 201

def test_get_chat(client):
    """Test getting chat details"""
    # Create chat
    client.post('/api/chats', 
        json={
            'creator_id': 'user1',
            'chat_id': 'test_chat'
        }
    )
    
    # Get chat details
    response = client.get('/api/chats/test_chat')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == 'test_chat' 