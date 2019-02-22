import flask
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
from time import time
import requests

app = Flask(__name__)

socketio = SocketIO(app)

names = open("students.txt", "r").read().split("\n")
students = {name: {'name': name, 'status': None, 'online': False} for name in filter(None, names)}
sessions = {}
task = dict(started=False, at=time())
chat = []

def logout():
    if flask.request.sid in sessions:
        sessions[flask.request.sid].update(dict(online=False, status=None))

def get_student_list():
    return sorted(students.values(), key=lambda x: x['name'])

@socketio.on('trigger_task')
def trigger_task(started):
    status = 'thinking' if started else None

    for student in students.values():
        if student['online']:
            student['status'] = status

    task.update(dict(started=started, at=time()))

    socketio.emit('task_triggered', dict(
            started=task['started'],
            running_time=int(time() - task['at'])
        ), broadcast=True)

    socketio.emit('student_list', get_student_list(), broadcast=True)

@socketio.on('change_status')
def change_status(status):
    if flask.request.sid in sessions:
        sessions[flask.request.sid]['status'] = status
        socketio.emit('student_list', get_student_list(), broadcast=True)

@socketio.on('student_list_request')
def student_list_request():
    socketio.emit('student_list', get_student_list())

@socketio.on('chat_message_send')
def chat_message_send(text):
    name = sessions[flask.request.sid]['name'] if flask.request.sid in sessions else 'Anonymous'
    chat.append(dict(name=name, text=text))

    socketio.emit(
        'chat_message_receive',
        dict(name=name, text=text),
        broadcast=True
    )

@socketio.on('reset_statuses')
def reset_statuses(status):
    for student in students.values():
        if student['online']:
            student['status'] = status

    socketio.emit('student_list', get_student_list(), broadcast=True)

@socketio.on('connect')
def connect():
    socketio.emit('task_triggered', dict(
        started=task['started'],
        running_time=int(time() - task['at'])
    ))

    socketio.emit('student_list', get_student_list())
    socketio.emit('chat_history', chat)

@socketio.on('disconnect')
def disconnect():
    if flask.request.sid in sessions:
        logout()
        del sessions[flask.request.sid]
        socketio.emit('student_list', get_student_list(), broadcast=True)

@socketio.on('login')
def login(name):
    if not name in students:
        return

    prev_status = sessions[flask.request.sid]['status'] if flask.request.sid in sessions \
        else 'thinking' if task['started'] else None

    logout()

    students[name].update(dict(online=True, status=prev_status))
    sessions[flask.request.sid] = students[name]

    socketio.emit('student_list', get_student_list(), broadcast=True)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if app.debug:
        return requests.get('http://localhost:8080/{}'.format(path)).text
    else:
        if path != "":
            return send_from_directory('dist', path)

        return send_from_directory('dist', 'index.html')

if __name__ == '__main__':
    socketio.run(app, debug=app.debug)
