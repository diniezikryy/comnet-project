import socket

server_port = 54321
server_ip = "127.0.0.1"

# setup client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# initiate connection to the server
client_socket.connect((server_ip, server_port))
# set buffer size
buffer_size = 1024 # make sure this is same as server buffer size

while True: 
    # send message to server
    # message = input("Enter a message to send to server: ")
    message = "pi1: userid, success"
    client_socket.sendto(message.encode(), (server_ip, server_port))

    # receive message from server
    modified_message = client_socket.recv(buffer_size)
    print(f"Message from {server_ip}:{server_port} -> {modified_message.decode()}")

# remember to close the soccket when finish
client_socket.close()