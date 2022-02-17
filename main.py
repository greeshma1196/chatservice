from socket import socket
from flask import Flask, render_template, request
from flask_socketio import SocketIO
import sqlite3 as sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app)

conn = sqlite3.connect("chatservice.db", check_same_thread=False)

cursor = conn.cursor()

sql_statement = """
CREATE TABLE IF NOT EXISTS [Chatmessages] (
    [ID] INTEGER PRIMARY KEY AUTOINCREMENT,
    [Name] VARCHAR(20),
    [Message] VARCHAR(100)
);
"""
cursor.execute(sql_statement)

@app.route('/')
def sessions():
    return render_template('index.html')


def messageReceived(methods=['GET', 'POST']):
    app.logger.debug('message received.')


@socketio.on('check previous messages')
def handle_check_previous_messages():
    app.logger.debug('session id:' + str(request.sid))
    with sqlite3.connect("chatservice.db") as conn:
        cursor = conn.cursor()
        sql_statement = "select * from Chatmessages;"
        cursor.execute(sql_statement)
        messageData = cursor.fetchall()
        if len(messageData) > 0:
            socketio.emit('receive chat history',data = messageData, to = [request.sid])

@socketio.on('send message')
def handle_send_message(json):
    with sqlite3.connect("chatservice.db") as conn:
        cursor = conn.cursor()
        sql_statement = "INSERT INTO Chatmessages (Name, Message) VALUES ('{}', '{}')".format(json['user_name'], json['message'])  
        cursor.execute(sql_statement)
        conn.commit()
    socketio.emit('new message', json, callback=messageReceived)

if __name__ == '__main__':
    socketio.run(app, debug=True, host="0.0.0.0")