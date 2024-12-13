from flask import Flask
from controllers.ChatController import chat_controller
from storage.sqlite_setup import init_db

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Initialize database
    init_db()
    
    # Register blueprints
    app.register_blueprint(chat_controller, url_prefix='/api')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 