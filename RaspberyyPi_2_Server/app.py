from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_wtf import CSRFProtect
from sqlalchemy import desc
from extensions import db, login_manager
from flask_login import login_user, login_required, logout_user, current_user
from forms import RegistrationForm, LoginForm, LinkNfcTagForm, EditUserForm, RegisterNfcTagForm
from models import User, NfcTag, DoorLog, DoorbellLog
from flask_socketio import SocketIO, emit
from flask_migrate import Migrate
import socket, threading, signal, sys, os, struct
from datetime import datetime

# Initialize Flask application and configure settings
app = Flask(__name__)
app.config['SECRET_KEY'] = '695bf18ae30e380398715ff072e684c0d1437958c7e9147a'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
csrf = CSRFProtect(app)

# Initialize database, login manager, and migration
db.init_app(app)
login_manager.init_app(app)
migrate = Migrate(app, db)

# Define client database with devices and their IP addresses
client_db = [
    {"ip": "94.16.32.25", "name": "camera", "socket": None},
    {"ip": "94.16.32.21", "name": "door", "socket": None},
    {"ip": "94.16.32.23", "name": "light&fan", "socket": None},
    {"ip": "94.16.32.23", "name": "camera", "socket": None}
]

# Initialize SocketIO
socketio = SocketIO(app)
TCP_IP = "94.16.32.22"
TCP_PORT = 12345
BUFFER = 1024
FORMAT = "utf-8"

def save_image(image_data, filename):
    """
    Save image data from TCP client to a file and return the file path.

    Args:
        image_data (bytes): The image data received from the client.
        filename (str): The name of the file to save the image as.

    Returns:
        str: The path to the saved image file.
    """
    os.makedirs("static/uploads", exist_ok=True)
    image_path = os.path.join('static/uploads', filename)
    with open(image_path, 'wb') as file:
        file.write(image_data)
    return image_path

def handle_tcp_client(client_socket, client_address):
    """
    Handle incoming TCP client connections.

    Args:
        client_socket (socket.socket): The socket connected to the client.
        client_address (tuple): The address of the client.
    """
    with app.app_context():
        while True:
            try:
                action = None
                data = client_socket.recv(BUFFER)
                if not data:
                    break

                client_ip, session_id = client_address
                client_name, message = data.decode(FORMAT).split(": ", 1)

                for client in client_db:
                    if client["ip"] == client_ip and client_name.lower() == client["name"]:
                        action = client["name"]
                        client["socket"] = client_socket
                        break

                if action:
                    if action == "door":
                        message_parts = [part.strip() for part in message.split(",")]
                        door_log = DoorLog(nfc_id=message_parts[0], timestamp=datetime.now(), status=message_parts[1])
                        db.session.add(door_log)
                        db.session.commit()
                        emit_data = {"data": f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}, {message}"}
                        socketio.emit(action, emit_data)

                    elif action == "light&fan":
                        print(f"[LIGHT&FAN] Message from light&fan: {message}")

                    elif action == "camera":
                        filename = message
                        client_socket.send("Filename received".encode(FORMAT))
                        file_size_data = client_socket.recv(4)
                        file_size = struct.unpack('!I', file_size_data)[0]

                        image_data = b""
                        total_received = 0
                        while total_received < file_size:
                            chunk = client_socket.recv(BUFFER)
                            if not chunk:
                                break
                            image_data += chunk
                            total_received += len(chunk)

                        image_path = save_image(image_data, filename)
                        doorbell_log = DoorbellLog(timestamp=datetime.now(), image=image_path)
                        db.session.add(doorbell_log)
                        db.session.commit()

                else:
                    print(f"Received data from unknown client {client_ip}: {data.decode('utf-8')}")

            except ConnectionResetError:
                break
            
        client_socket.close()

def handle_disconnect():
    """
    Handle client disconnection.
    """
    print('Client disconnected')

def tcp_server():
    """
    Start TCP server and listen for incoming connections.
    """
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server_socket.bind((TCP_IP, TCP_PORT))
    tcp_server_socket.listen(5)

    while True:
        client_socket, addr = tcp_server_socket.accept()
        client_handler = threading.Thread(target=handle_tcp_client, args=(client_socket, addr))
        client_handler.start()

@app.route("/send_data")
def send_data():
    """
    Send data to a specified client.

    Returns:
        Response: Redirect to home page.
    """
    sendto_client = request.args.get('client')
    message = request.args.get('message')

    for client in client_db:
        if client["name"] == sendto_client:
            server_port = 54321
            server_ip = client["ip"]

            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((server_ip, server_port))

            try:
                client_socket.send(message.encode())
                client_socket.close()
            except socket.error as a:
                print(f"Socket error: {a}")
            except Exception as e:
                print(f"Failed to send message to {client['name']}: {e}")

    return redirect("/")

@login_manager.user_loader
def load_user(user_id):
    """
    Load user by ID for Flask-Login.

    Args:
        user_id (int): The ID of the user.

    Returns:
        User: The user object.
    """
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    """
    Render the index page.

    Returns:
        Response: The rendered template for the index page.
    """
    num_users = User.query.count()
    door_logs = DoorLog.query.order_by(DoorLog.timestamp.desc()).limit(5).all()
    latest_log = DoorbellLog.query.order_by(desc(DoorbellLog.timestamp)).first()
    if latest_log:
        latest_photo = {
            'image': latest_log.image,
            'timestamp': latest_log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
    else:
        latest_photo = None
    return render_template('index.html', num_users=num_users, door_logs=door_logs, latest_photo=latest_photo)

@app.route('/door_logs')
@login_required
def logs():
    """
    Render the door logs page.

    Returns:
        Response: The rendered template for the door logs page.
    """
    logs = DoorLog.query.order_by(DoorLog.timestamp.desc()).all()
    return render_template('door_logs.html', logs=logs)

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """
    Handle user registration.

    Returns:
        Response: The rendered template for the registration page or a redirect to manage users page.
    """
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('manage_users'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.

    Returns:
        Response: The rendered template for the login page or a redirect to the next page.
    """
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
    """
    Handle user logout.

    Returns:
        Response: Redirect to login page.
    """
    logout_user()
    return redirect(url_for('login'))

@app.route('/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    """
    Render the manage users page.

    Returns:
        Response: The rendered template for the manage users page.
    """
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """
    Handle editing user details.

    Args:
        user_id (int): The ID of the user to edit.

    Returns:
        Response: The rendered template for the edit user page or a redirect to manage users page.
    """
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    if form.validate_on_submit():
        user.name = form.name.data
        user.username = form.username.data
        db.session.commit()
        flash('User details updated successfully', 'success')
        return redirect(url_for('manage_users'))
    return render_template('edit_user.html', form=form, user=user)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """
    Handle deleting a user.

    Args:
        user_id (int): The ID of the user to delete.

    Returns:
        Response: Redirect to manage users page.
    """
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully', 'success')
    return redirect(url_for('manage_users'))

@app.route('/link_nfc/<int:user_id>', methods=['GET', 'POST'])
@login_required
def link_nfc(user_id):
    """
    Handle linking an NFC tag to a user.

    Args:
        user_id (int): The ID of the user to link the NFC tag to.

    Returns:
        Response: The rendered template for the link NFC page or a redirect to manage users page.
    """
    user = User.query.get_or_404(user_id)
    form = LinkNfcTagForm()
    if form.validate_on_submit():
        nfc_tag = NfcTag.query.filter_by(nfc_id=form.nfc_id.data).first()
        if nfc_tag:
            nfc_tag.user_id = user_id
            db.session.commit()
            flash('NFC tag linked successfully', 'success')
        else:
            flash('NFC tag not found', 'danger')
        return redirect(url_for('manage_users'))
    return render_template('link_nfc.html', form=form, user=user)

@app.route('/register_nfc_tag', methods=['GET', 'POST'])
@login_required
def register_nfc_tag():
    """
    Handle registering a new NFC tag.

    Returns:
        Response: The rendered template for the register NFC tag page or a redirect to manage users page.
    """
    form = RegisterNfcTagForm()
    if form.validate_on_submit():
        nfc_tag = NfcTag.query.filter_by(nfc_id=form.nfc_id.data).first()
        if nfc_tag:
            flash('NFC tag already exists', 'danger')
        else:
            new_nfc_tag = NfcTag(nfc_id=form.nfc_id.data)
            db.session.add(new_nfc_tag)
            db.session.commit()
            flash('NFC tag registered successfully', 'success')
        return redirect(url_for('manage_users'))
    return render_template('register_nfc_tag.html', form=form)

@app.route('/nfc_tags')
@login_required
def nfc_tags():
    """
    Render the NFC tags page.

    Returns:
        Response: The rendered template for the NFC tags page.
    """
    tags = NfcTag.query.all()
    return render_template('nfc_tags.html', tags=tags)

def create_app():
    """
    Create database tables.
    """
    with app.app_context():
        db.create_all()

@app.context_processor
def inject_user():
    """
    Inject current user into templates.

    Returns:
        dict: Dictionary containing the current user.
    """
    return dict(current_user=current_user)

if __name__ == '__main__':
    create_app()
    thread = threading.Thread(target=tcp_server)
    thread.daemon = True
    thread.start()
    socketio.run(app, host='0.0.0.0', port=5001)
