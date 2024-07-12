from flask import Flask, render_template, redirect, url_for, flash, request
from extensions import db, login_manager
from flask_login import login_user, login_required, logout_user, current_user
from forms import RegistrationForm, LoginForm
from models import User, Log
from flask_socketio import SocketIO, emit
import socket, threading, signal, sys, os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = '695bf18ae30e380398715ff072e684c0d1437958c7e9147a'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
# app.config['DEBUG'] = True  # Enable debug mode

db.init_app(app)
login_manager.init_app(app)

client_db = [
    {
        "ip": "127.0.0.1",
        "name": "door",
        "socket": None
    },
    {
        "ip": "94.16.32.21",
        "name": "door",
        "socket": None
    },
    {
        "ip": "94.16.32.23",
        "name": "light&fan",
        "socket": None
    },
    {
        "ip": "94.16.32.23",
        "name": "camera",
        "socket": None
    }
]

# = = = socket tcp = = =
socketio = SocketIO(app)
TCP_IP = socket.gethostbyname(socket.gethostname())
TCP_PORT = 12345
BUFFER = 1024

# Function to handle incoming socket data
def handle_tcp_client(client_socket, client_address):
    while True:
        try:
            data = client_socket.recv(BUFFER)
            if not data:
                break

            # Emit data to WebSocket clients
            print(f"this is client address {client_address}")
            [client_ip, session_id] = client_address
            client_name, message = data.decode('utf-8').split(": ", 1)
            print(f"Received data from {client_name}: {message}")
            
            for client in client_db:
                if client["ip"] == client_ip and client_name.lower() == client["name"]:
                    action = client["name"]
                    client["socket"] = client_socket

            if action:

                if action == "door":
                    emit_data = {"data": f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}, {message}"}
                    print(f"Emitting {action} event with data: {emit_data}")
                    socketio.emit(action, emit_data)

                    # send back
                    client_socket.send("door request received".encode())
                    print(f"sending back the formatted packet")

                elif action == "camera":
                    # TODO: update to camera data
                    emit_data = {"data": message}
                    print(f"Emitting {action} event with data: {emit_data}")
                    socketio.emit(action, emit_data)

                    # send back
                    client_socket.send("light&fan request received".encode())
                    print(f"sending back the formatted packet")
            else:
                print(f"Received data from unknown client {client_ip}: {data.decode('utf-8')}")

        except ConnectionResetError:
            break
    client_socket.close()

def handle_disconnect():
    print('Client disconnected')

def tcp_server():
    print("Starting TCP server...")
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server_socket.bind((TCP_IP, TCP_PORT))
    tcp_server_socket.listen(5)
    print(f"\nTCP server listening on {TCP_IP}:{TCP_PORT}")

    while True:
        client_socket, addr = tcp_server_socket.accept()
        print(f"Connection from {addr}")
        client_handler = threading.Thread(target=handle_tcp_client, args=(client_socket, addr))
        client_handler.start()

@app.route("/send_data")
def send_data():
    sendto_client = request.args.get('client')
    message = request.args.get('message')

    for client in client_db:
        if client["name"] == sendto_client:
            try:
                if client["socket"]:
                    print(f"Send packet to {client['name']}:{client['ip']} --> {message}")
                    client["socket"].send(message.encode())
                else:
                    print(f"No socket connection available for {client['name']}:{client['ip']}")
            except Exception as e:
                print(f"Failed to send message to {client['name']}: {e}")
    return redirect("/")

# = = = others = = =
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/test')
def test():
    return render_template('test.html')


@app.route('/logs')
@login_required
def logs():
    # Hardcoded logs
    logs = [
        {'datetime': '1/1/24 5:00:00', 'status': 'Successful', 'id': '123456789009'},
        {'datetime': '1/1/24 5:05:00', 'status': 'Fail', 'id': '123456789010'},
        {'datetime': '1/1/24 5:10:00', 'status': 'Successful', 'id': '123456789011'},
        {'datetime': '1/1/24 5:15:00', 'status': 'Fail', 'id': '123456789012'},
        {'datetime': '1/1/24 5:20:00', 'status': 'Successful', 'id': '123456789013'},
        {'datetime': '1/1/24 5:25:00', 'status': 'Fail', 'id': '123456789014'},
        # Add more logs as needed
    ]
    return render_template('test_logs.html', logs=logs)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, nfc_tag=form.nfc_tag.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# DB & Running Flask Web App
def create_app():
    with app.app_context():
        db.create_all()


@app.context_processor
def inject_user():
    return dict(current_user=current_user)


if __name__ == '__main__':
    create_app()
    thread = threading.Thread(target=tcp_server)
    thread.daemon = True
    thread.start()

    socketio.run(app, host='0.0.0.0', port=5001)
