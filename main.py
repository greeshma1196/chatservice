from flask import Flask, render_template, request
from flask_socketio import SocketIO
import sqlite3 as sqlite3
import os
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'abcde12345!'
socketio = SocketIO(app, message_queue='redis://message-queue:6379')

port = int(os.getenv('PORT'))
is_leader = os.getenv('IS_LEADER')
followers = os.getenv('FOLLOWERS')
if followers != None:
    followers = followers.split(',')

conn = sqlite3.connect("/data/chatservice.db", check_same_thread=False)

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

@app.route('/append-entries', methods=['POST'])
def append_entries():
    user_name = request.form['user_name']
    message = request.form['message']
    with sqlite3.connect("/data/chatservice.db") as conn:
        cursor = conn.cursor()
        sql_statement = "INSERT INTO Chatmessages (Name, Message) VALUES ('{}', '{}')".format(user_name, message)  
        cursor.execute(sql_statement)
        conn.commit()
    return {'success':True}

@socketio.on('check previous messages')
def handle_check_previous_messages():
    app.logger.debug('session id:' + str(request.sid))
    with sqlite3.connect("/data/chatservice.db") as conn:
        cursor = conn.cursor()
        sql_statement = "select * from Chatmessages;"
        cursor.execute(sql_statement)
        messageData = cursor.fetchall()
        if len(messageData) > 0:
            socketio.emit('receive chat history', data = messageData, to = [request.sid])

@socketio.on('send message')
def handle_send_message(json):
    if is_leader == 'true':
        acknowledgement_follower = True
        for follower in followers:
            app.logger.debug("Follower name: " + follower)
            acknowledgement_follower = acknowledgement_follower and send_append_entries(follower, json)
            
        if acknowledgement_follower:
            with sqlite3.connect("/data/chatservice.db") as conn:
                cursor = conn.cursor()
                sql_statement = "INSERT INTO Chatmessages (Name, Message) VALUES ('{}', '{}')".format(json['user_name'], json['message'])  
                cursor.execute(sql_statement)
                conn.commit()
            socketio.emit('new message', json)

def send_append_entries(follower, entry):
    url = "http://{follower}:{port}/append-entries".format(follower = follower, port = port)
    response_follower = requests.post(url, data=entry)
    response_follower = response_follower.json()
    return response_follower['success']

if __name__ == '__main__':
    socketio.run(app, debug=True, host="0.0.0.0", port=port)