from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from routes.message_routes import message_routes
from routes.auth_routes import auth_routes

app = Flask(__name__)
CORS(app)
app.register_blueprint(message_routes)
app.register_blueprint(auth_routes)

socketio = SocketIO(cors_allowed_origins='*')
socketio.init_app(app, cors_allowed_origins='*')

# In-memory message history
messages = []

@socketio.on('send_message')
def handle_send(data):
    messages.append(data)
    emit('receive_message', data, broadcast=True)

@socketio.on('join')
def handle_join():
    # Send all previous messages to the new user (only to sender)
    for msg in messages:
        emit('receive_message', msg)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5002)
