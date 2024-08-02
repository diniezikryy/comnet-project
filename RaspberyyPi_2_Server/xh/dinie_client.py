import socket

# TCP Client Config
SERVER_IP = '127.0.0.1'
SERVER_PORT = 12345
BUFFER_SIZE = 1024
FORMAT = 'utf-8'

# EXAMPLE MSG TO BE SENT TO SERVER
DOOR_MESSAGE = f"door: 12345, open"

def test_door():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # connecting socket to the server's addr and port
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}.")

        # send message to the server
        client_socket.send(DOOR_MESSAGE.encode(FORMAT))
        print(f"Sent Message: {DOOR_MESSAGE}")

        # Recv response from server
        response = client_socket.recv(BUFFER_SIZE).decode(FORMAT)
        print(f"Received Response: {response}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client_socket.close()
        print(f"Disconnected from server at {SERVER_IP}:{SERVER_PORT}.")

if __name__ == '__main__':
    test_door()
