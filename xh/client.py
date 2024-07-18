import socket, threading
import os

server_port = 12345
server_ip = socket.gethostbyname(socket.gethostname())
print(f"server_ip: {server_ip}, port: {server_port}")
# server_ip = "127.0.0.1"
buffer_size = 1024 # make sure this is same as server buffer size
file_format = "utf-8"

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
        nfc_id = "123456789"
        status = "success"
        # usermsg = input("Enter a message to send to server: ") # can delete this line
        # message = "door: userid, success" + "hellooo" # TODO: UPDATE OWN DATA
        message = f"door: {nfc_id}, {status}"
        client_socket.sendto(message.encode(), (server_ip, server_port))

        # if usermsg == "end":
        #     print("Ending connection...")
        #     client_socket.close()
        #     break

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

def send_pic():
    filename = "picture.jpg"

     # Ensure the file exists and is not empty
    if not os.path.exists(f"xh/{filename}"):
        print(f"[CLIENT] File {filename} does not exist.")
        return
    if os.path.getsize(f"xh/{filename}") == 0:
        print(f"[CLIENT] File {filename} is empty.")
        return

    with open(f"xh/{filename}", "rb") as file: # TODO: update location of the file 
        data = file.read()
        print(f"we are sending data: {data}")

    client_socket.send(f"camera: {filename}".encode(file_format))
    print("[CLIENT]: Filename sent successfully")
    msg = client_socket.recv(buffer_size).decode(file_format) # send the filename
    print(f"[SERVER]: {msg}")

    client_socket.sendall(data) # send file over to server
    print("[CLIENT]: File sent successfully")


# Create threads for sending and receiving messages
send_thread = threading.Thread(target=send_messages)
receive_thread = threading.Thread(target=receive_messages)
send_pic()

# Start the threads
send_thread.start()
receive_thread.start()

# Wait for the threads to complete
send_thread.join()
receive_thread.join()

print("Client connection closed.")
# remember to close the soccket when finish
client_socket.close()
