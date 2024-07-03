from flask import render_template, request, redirect, url_for, session, flash, jsonify
import RPi.GPIO as GPIO
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

GPIO_SETUP = False
host_name = '10.0.0.184'  # IP Address of Raspberry Pi
host_port = 8000

def setupGPIO():
    GPIO.setmore(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(18, GPIO.OUT) # setup the GPIO pins,, for now is LED pin
    GPIO_SETUP = True

def control_door():
    # if gpio is not set up, run setup, else run as usual
    if not GPIO_SETUP: setupGPIO()

    data = request.get_json()
    action = data.get('action')

    if action == 'lock':
        GPIO.output(18, GPIO.HIGH)
        message = 'Door locked'
    elif action == 'unlock':
        GPIO.output(18, GPIO.LOW)
        message = 'Door unlocked'
    else:
        message = 'Invalid action'

    return jsonify({message})

def control_fan():
    # if gpio is not set up, run setup, else run as usual
    if not GPIO_SETUP: setupGPIO()

    # TODO: setup for fan

if __name__ == '__main__':
    try:
        # Change '0.0.0.0' to your Raspberry Pi's IP address if you want to be more specific
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        GPIO.cleanup()  # Clean up GPIO settings on exit