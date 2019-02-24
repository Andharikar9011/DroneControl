#Python3 
#Created for Mission Critial Drone Project for Ericsson
#Code to be run on Computer to connect to Drone
#Need to connect pygame compatiable controller. May need to change axis layout if new controller is used
#Use "ControllerFile.py" to test

#Austin Greisman

import pygame
import socket
import time
import subprocess
import os
import signal

#Inital Connection set up -> Drone static IP over Hai's PIC VPN
host = '10.8.0.2'

#Static port
port = 6970

#Variable used to remain in sync with the drone during data transimission
heartbeat = 0
s = socket.socket()
s.connect((host, port))
print("Connected to Drone...")

#If connection is lost for more than 5 seconds, connection dropped
s.settimeout(5)
pygame.init()
print("yes")
#Loop until the user clicks the close button.
done = False
# Used to manage how fast the screen updates
clock = pygame.time.Clock()

# Initialize the joysticks
pygame.joystick.init()

#Variables
pitch = 0
roll = 0
yaw = 0
throttle = 0

#Calibration Settings
low_cal = 240
mid_cal = 330
max_cal = 420
Canny = 1

#Activated by pressing start button. However, needs to be calibrated again
def StartYourEngines(heartbeat, s):
    if heartbeat:
        print("Sending start sequence to drone...")
        message = "%d,%d,%d,%d " % (237, 237, 248, 238) #Change!
        print(message)
        for i in range(10):
            s.send(message.encode('utf-8'))
            heartbeat = 0
            s.recv(5)
        print("Start sequence sent...")


# -------- Main Program Loop -----------
while done==False:
    # EVENT PROCESSING STEP
    for event in pygame.event.get(): # User did something
        if event.type == pygame.QUIT: # If user clicked close
            done=True # Flag that we are done so we exit this loop

    #Count Joystick
    joystick_count = pygame.joystick.get_count()
    # For each joystick:
    for i in range(joystick_count):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()
        
        # Usually axis run in pairs, up/down for one, and left/right for
        # the other.
        axes = joystick.get_numaxes()
        
        for i in range( axes ):
            axis = joystick.get_axis( i )

            #  Minimum jump value implemented to remove wobble
            min_jump = 0.05

            #CUSTOM FOR UBUNTU CONTROL
            if i == 2 and abs(axis-yaw) > min_jump:
                yaw = axis
            if i == 3 and abs(axis-throttle) > min_jump:
                throttle = (axis)*-1
            if i == 0 and abs(axis-roll) > min_jump:
                roll = axis
            if i == 1 and abs(axis-pitch) > min_jump:
                pitch = (axis) * -1

        # Grabs value for start button on Logitech controller (For StartYourEngines())
        engine_button = joystick.get_button(0)
        hover_button = joystick.get_button(1)
        
        # Hat switch. All or nothing for direction, not like joysticks.
        # Value comes back in an array.
        #hats = joystick.get_numhats()

        #for i in range( hats ):
        #    hat = joystick.get_hat( i )
    
    ####Prepare to send, currently hardcoded to call settings -  Custom
    send_pitch = int(mid_cal + 90*pitch) - 3
    send_yaw = int(mid_cal + 90*yaw) - 2
    send_roll =int(mid_cal + 90*roll) - 3
    send_throttle = int(mid_cal +90*throttle)

    #####Send commands out
    # To remain in sync with drone
    try:
        heartbeat = s.recv(5)
    except:
        print("Lost connection...")
        break
    # If start button(s) pressed
    if engine_button:
        StartYourEngines(heartbeat, s)
    if hover_button:
        print("AutoHover Engagged")
    if heartbeat:
        #print("Sending Commands...")
        message = "%d,%d,%d,%d "%(send_roll, send_pitch, send_throttle, send_yaw)
        #print(message)
        s.send(message.encode('utf-8'))
        #print("Message sent...")
        time.sleep(0.01) #was 0.1
    heartbeat = 0
    
# Close the window and quit.
# If you forget this line, the program will 'hang'
# on exit if running from IDLE.
pygame.quit ()
