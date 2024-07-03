# !/usr/bin/env python3

import RPi.GPIO as GPIO
import os

def setupGPIO():
    GPIO.setmore(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(18, GPIO.OUT) # setup the GPIO pins

def printTemperature(): # print out the temperature for the raspberry pi
    temp = os.popen("/opt/vc/bin/vcgencmd_measure_temp").read()
    print()

def controlLED():
    try:
        while True:
            input("Turn LELD On or Off with 1 or 0 (Ctrl-C to exit): ")
        if user_input is "1":
            GPIO.output(18, GPIO.HIGH)
            print("LED is on")
        elif user_input is "0":
            GPIO.output(18, GPIO.LOW)
            print("LED is off")
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("cleaned and closed")

setupGPIO()
printTemperature()

controlLED()