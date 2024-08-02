import socket
import os

# Configuration for the TCP client
SERVER_IP = "127.0.0.1"  # Replace with your server's IP address if different
SERVER_PORT = 12345
BUFFER_SIZE = 1024
FORMAT = "utf-8"

# Simulated message from the "camera" client
IMAGE_FILE = "picture.jpg"

def send_image(filename):
    try:
        # Create a TCP/IP socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the server's address and port
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}")

        # Send the filename to the server with the "camera" action
        client_socket.send(f"camera: {filename}".encode(FORMAT))
        print(f"Sent filename: {filename}")

        # Receive acknowledgment from the server
        response = client_socket.recv(BUFFER_SIZE).decode(FORMAT)
        print(f"Received response: {response}")

        # Send the image data to the server
        with open(filename, "rb") as file:
            while chunk := file.read(BUFFER_SIZE):
                client_socket.send(chunk)
            print(f"Sent image data for {filename}")

        # Close the socket
        client_socket.close()
        print("Connection closed")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    send_image(IMAGE_FILE)
