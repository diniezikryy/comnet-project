import socket, threading
import time

send_port = 12345
receive_port = 54321
server_ip = "127.0.0.1"
BUFFER = 1024
FORMAT = "utf-8"

# for fan control
fan_state = False

def handle_cmd(conn, addr):
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
        # TODO: add codes for lights

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
    global fan_state  # Declare that we are using the global variable fan_state
    while True:
        if fan_state:
            fan_on()
        else:
            fan_off()

def fan_on():
    print("fan is ON")
    time.sleep(3)
def fan_off():
    print("fan is OFF")
    time.sleep(3)

def handle_send(send_sock):
    send_sock.send("camera: HELLOOO IM FROM CLIENT".encode(FORMAT))
    return

# = = = = =

# initialise the sockets
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

while True:
    try:
        conn, addr = receive_socket.accept()
        receive_thread = threading.Thread(target=handle_cmd, args=(conn, addr))
        receive_thread.start()
    except Exception as e:
        print(f"Error: {e}")

print("Client connection closed.")
# remember to close the soccket when finish
send_socket.close()