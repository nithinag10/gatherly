from flask import Flask, jsonify
from flask_cors import CORS
from google.cloud.sql.connector import Connector, IPTypes
import sqlalchemy
import os
from controllers.ChatController import chat_controller
from controllers.UserController import user_controller

# Load environment variables
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")

# Initialize connector
connector = Connector()

# Define the connection function
def getconn():
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pymysql",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
        ip_type=IPTypes.PUBLIC
    )
    return conn

# Create connection pool
pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

# Create Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    "*": {
        "origins": ["http://localhost:3000", "https://getherly-frontend.vercel.app"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Register the chat controller with the /api prefix
app.register_blueprint(chat_controller, url_prefix='/api/chats')
app.register_blueprint(user_controller, url_prefix='/api/auth')

@app.route('/')
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}, 200


@app.teardown_appcontext
def close_connector(exception=None):
    """Clean up the connector on application teardown."""
    connector.close()
