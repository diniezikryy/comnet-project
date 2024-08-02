# imports
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from time import sleep
import datetime
import multiprocessing
import socket

# Server Pi's IP address and port (Pi 2's IP)
server_ip = '94.16.32.22'  # Server Pi's IP address
server_port = 12345        # Server Pi's Port Number

listener_port = 54321      # Current Pi's Port Number to receive Server's messages

# Servo initialization (for Door)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT)

# Reader initialization (for RFID Reader)
reader = SimpleMFRC522()

# Keypad layout (for keypad)
KEYPAD = [
    [1, 2, 3, 'A'],
    [4, 5, 6, 'B'],
    [7, 8, 9, 'C'],
    ['*', 0, '#', 'D']
]

# Define GPIO pins for rows and columns (for keypad)
ROW_PINS = [29, 31, 33, 35]  # Physical pins for rows
COL_PINS = [37, 36, 38, 40]  # Physical pins for columns

# Password to unlock door with keypad
PASSWORD = [1, 2, 3, 4]

# Keypad init
# Set up row pins as outputs
for row_pin in ROW_PINS:
    GPIO.setup(row_pin, GPIO.OUT)
    GPIO.output(row_pin, GPIO.LOW)

# Set up column pins as inputs with pull-down resistors
for col_pin in COL_PINS:
    GPIO.setup(col_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

door = multiprocessing.Value('b', False)

# Function to move servo (open door for 5s, close door)
def unlock():
    p = GPIO.PWM(11, 50)
    p.start(0)
    p.ChangeDutyCycle(3) # Open door
    sleep(5)             # Door stays open for 5s
    p.ChangeDutyCycle(9) # Close door
    sleep(1)
    p.stop()
    return False

# Function to send RFID entry attempt to server
def send_entry_attempt(entry_attempt):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, server_port))
            s.sendall(entry_attempt.encode())
            print(f"Sent entry_attempt: {entry_attempt}")
    except Exception as e:
        print(f"Error sending data: {str(e)}")

# Function when entry attempt is successful
def approve(id):
    print("Valid entry attempt at " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    entry_attempt = "door: " + str(id) + ",success"
    process = multiprocessing.Process(target=send_entry_attempt, args=(entry_attempt,))
    process.start()

# Function when entry attempt in unsuccessful
def decline(id):
    print("Invalid entry attempt at " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    entry_attempt = "door: " + str(id) + ",fail"
    process = multiprocessing.Process(target=send_entry_attempt, args=(entry_attempt,))
    process.start()

# Function to check if RFID card is correct
def check_card(door):
    while True:
        id, text = reader.read()
        print(id)
        if id == 646419520150:
            approve(id)
            door.value = True
        else:
            decline(id)
        sleep(1)

# Function to read the pressed key from the keypad
def get_key():
    key = None
    for row_num, row_pin in enumerate(ROW_PINS):
        GPIO.output(row_pin, GPIO.HIGH)
        for col_num, col_pin in enumerate(COL_PINS):
            if GPIO.input(col_pin) == GPIO.HIGH:
                key = KEYPAD[row_num][col_num]
                while GPIO.input(col_pin) == GPIO.HIGH:
                    sleep(0.05)
        GPIO.output(row_pin, GPIO.LOW)
    return key

# Function to check if password is correct
def check_password(input_password):
    return input_password == PASSWORD

# Function to send keypad entry attempt to server
def send_password_attempt(x):
    if (x == 1):
        entry_attempt = "door: keypad was used,success"
        process = multiprocessing.Process(target=send_entry_attempt, args=(entry_attempt,))
        process.start()
    else:
        entry_attempt = "door: keypad was used,fail"
        process = multiprocessing.Process(target=send_entry_attempt, args=(entry_attempt,))
        process.start()

# Function to listen to keypad
def keypad_listener(door):
    entered_keys = []
    while True:
        pressed_key = get_key()
        if pressed_key is not None:
            print(f"Pressed: {pressed_key}")
            if pressed_key == '*':
                entered_keys = []  # Reset the input password
            elif pressed_key == '#':
                if check_password(entered_keys):
                    print("Password correct!")
                    door.value = True
                    send_password_attempt(1)  # Send correct password attempt
                else:
                    print("Incorrect password. Try again.")
                    send_password_attempt(0)
                    entered_keys = []  # Reset the input password
            else:
                entered_keys.append(pressed_key)
        sleep(0.1)
        
# Function to listen to server's message
def door_listener(door):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', listener_port))
        s.listen()
        while True:
            conn, addr = s.accept()
            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    print(f"Received message: {data.decode()}")
                    door.value = True

def main():

    # Multiprocessing to handle multiple listeners
    card_reader_process = multiprocessing.Process(target=check_card, args=(door,))
    keypad_process = multiprocessing.Process(target=keypad_listener, args=(door,))
    receiver_process = multiprocessing.Process(target=door_listener, args=(door,))
    
    # Start processes
    card_reader_process.start()
    keypad_process.start()
    receiver_process.start()
    
    # Try with exception handling
    try:
        while True:
            if door.value:
                door.value = unlock()
            sleep(0.1)

    except KeyboardInterrupt:
        card_reader_process.terminate()
        keypad_process.terminate()
        receiver_process.terminate()
        GPIO.cleanup()

if __name__ == '__main__':
    main()