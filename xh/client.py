import socket, threading

server_port = 12345
server_ip = socket.gethostbyname(socket.gethostname())
buffer_size = 1024 # make sure this is same as server buffer size

# setup client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# initiate connection to the server
client_socket.connect((server_ip, server_port))


### 
# DOOR DATA TO SEND:
# " door: <nfc id>, <attempt status (success/fail)> "
# 
# CAMERA DATA TO SEND:
# " camera: <filename> "
# ###
def send_messages():
    while True:
        usermsg = input("Enter a message to send to server: ") # can delete this line
        message = "door: userid, success" + usermsg # TODO: UPDATE OWN DATA
        client_socket.sendto(message.encode(), (server_ip, server_port))

        if usermsg == "end":
            print("Ending connection...")
            client_socket.close()
            break

def receive_messages():
    while True:
        try:
            modified_message = client_socket.recv(buffer_size)
            if not modified_message:
                print("Server closed the connection.")
                break
            print(f"Message from {server_ip}:{server_port} -> {modified_message.decode()}")
        except OSError:
            break  # Break the loop if the socket is closed

# Create threads for sending and receiving messages
send_thread = threading.Thread(target=send_messages)
receive_thread = threading.Thread(target=receive_messages)

# Start the threads
send_thread.start()
receive_thread.start()

# Wait for the threads to complete
send_thread.join()
receive_thread.join()

print("Client connection closed.")
# remember to close the soccket when finish
client_socket.close()