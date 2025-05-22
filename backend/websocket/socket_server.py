from flask_socketio import SocketIO, emit

socketio = SocketIO(cors_allowed_origins='*')

@socketio.on('send_message')
def handle_send(data):
    # data should be {'username': 'nessa', 'message': 'hello'}
    emit('receive_message', data, broadcast=True)
