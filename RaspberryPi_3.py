import socket
import threading
import time
import struct
import os
import RPi.GPIO as GPIO
from gpiozero import Button, LED
from picamera import PiCamera
from datetime import datetime

# Setup GPIO
GPIO.setmode(GPIO.BCM)
LED_PIN = 18
GPIO.setup(LED_PIN, GPIO.OUT)
camera = PiCamera()
doorbell = Button(23)

# Network configuration
send_port = 12345
receive_port = 54321
server_ip = "94.16.32.22"
BUFFER = 1024
FORMAT = "utf-8"

# Fan state
fan_state = False

def handle_cmd(conn, addr):
    """
    Handle incoming commands from the server to control devices.

    Args:
        conn (socket.socket): The connection socket.
        addr (tuple): The address of the connected client.
    """
    global fan_state
    print(f"Connection accepted from {addr}")

    try:
        data = conn.recv(BUFFER).decode(FORMAT)
        if not data:
            print(f"No initial data received from {addr}. Closing connection.")
            conn.close()
        else:
            print(f"Initial data received from {addr}: {data}")

        message = data.lower()
        print(f"Message from {addr}: {message}")
        if message == "fan_on":
            fan_state = True
            print("Fan state set to ON")
        elif message == "fan_off":
            fan_state = False
            print("Fan state set to OFF")
        elif message == "light_on":
            GPIO.output(LED_PIN, GPIO.HIGH)
            print("LED on")
        elif message == "light_off":
            GPIO.output(LED_PIN, GPIO.LOW)
            print("LED off")

    except socket.error as e:
        print(f"Socket error while receiving initial data from {addr}: {e}")
    except Exception as e:
        print(f"General error while receiving initial data from {addr}: {e}")

    finally:
        try:
            conn.close()
            print(f"Connection with {addr} closed.")
        except Exception as e:
            print(f"Error closing connection with {addr}: {e}")

    print(f"Finished handling connection with {addr}.")

def fan():
    """
    Control the fan based on the current fan state.
    """
    global fan_state
    ControlPin = [12, 16, 20, 21]
    GPIO.setmode(GPIO.BCM)
    for pin in ControlPin:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, 0)

    seq = [
        [1, 0, 0, 0],
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1],
        [1, 0, 0, 1]
    ]

    try:
        while True:
            if fan_state:
                for halfstep in range(8):
                    for pin in range(4):
                        GPIO.output(ControlPin[pin], seq[halfstep][pin])
                    time.sleep(0.001)
            else:
                time.sleep(1)

    except KeyboardInterrupt:
        print("Exiting program")

    finally:
        print("Cleaning up GPIO")
        GPIO.cleanup()

def take_picture():
    """
    Capture a picture using the PiCamera and send it to the server.
    """
    filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.jpg')
    camera.capture(filename)
    print(f'Picture taken and saved as {filename}')

    try:
        with open(filename, "rb") as file:
            data = file.read()

        send_socket.send(f"camera: {filename}".encode())
        print("[CLIENT]: Filename sent successfully")
        msg = send_socket.recv(BUFFER).decode()
        print(f"[SERVER]: {msg}")

        file_size = os.path.getsize(filename)
        send_socket.send(struct.pack('!I', file_size))
        print(f"[CLIENT] File size sent: {file_size} bytes")

        send_socket.sendall(data)
        print("[CLIENT]: File sent successfully")
    except Exception as e:
        print(f"An error occurred: {e}")

def handle_send(send_sock):
    """
    Handle sending data to the server when the doorbell button is pressed.

    Args:
        send_sock (socket.socket): The sending socket.
    """
    doorbell.when_pressed = take_picture
# Initialize the sockets
send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

send_socket.connect((server_ip, send_port))
receive_socket.bind(('', receive_port))
receive_socket.listen(1)

# Thread for controlling the fan state
fan_thread = threading.Thread(target=fan)
fan_thread.start()

# Thread for handling sending messages
send_thread = threading.Thread(target=handle_send, args=(send_socket,))
send_thread.start()

try:
    while True:
        conn, addr = receive_socket.accept()
        receive_thread = threading.Thread(target=handle_cmd, args=(conn, addr))
        receive_thread.start()
except Exception as e:
    print(f"Error: {e}")

finally:
    send_socket.close()
    GPIO.cleanup()

print("Client connection closed.")