import RPi.GPIO as GPIO
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

hostname = "0.0.0.0" # indiv ip? got from app.py
host_port = 5001

def setupGPIO():
    GPIO.setmore(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(18, GPIO.OUT) # setup the GPIO pins

def printTemperature(): # print out the temperature for the raspberry pi
    temp = os.popen("/opt/vc/bin/vcgencmd_measure_temp").read()
    return temp

class myServer(BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
    
    def _redirect(self, push):
        self.send_response(303)