from socket import socket
from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app)

messageDict = []

@app.route('/')
def sessions():
    return render_template('index.html')


def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')


@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    if len(messageDict) > 0:
        socketio.emit('send previous messages',messageDict)
    socketio.emit('my response', json, callback=messageReceived)

@socketio.on('my chat')
def handle_my_chat_event(json, methods=['GET', 'POST']):
    print('received my chat: ' + str(json))
    messageDict.append((json['user_name'], json['message']))
    print(messageDict)
    socketio.emit('my response', json, callback=messageReceived)


if __name__ == '__main__':
    socketio.run(app, debug=True)