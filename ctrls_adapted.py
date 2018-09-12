import pygame
import socket
import time
import subprocess
import os
import signal

#Inital Connection set up
host = '192.168.0.103'

port = 6969
heartbeat = 0
s = socket.socket()
s.connect((host, port))
print("Connected to Drone...")
s.settimeout(5)
pygame.init()

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
devnull = open('/dev/null', 'w')
cannyon = subprocess.Popen(["/Users/austingreisman/Documents/University/Internship/Drone/udp-image-streaming/./server", "8080", "0"], stdout=devnull, shell=False)


def StartYourEngines(heartbeat):
    if heartbeat:
        print("Sending start sequence to drone...")
        message = "%d,%d,%d,%d " % (239, 251, 245, 400) #Change!
        print(message)
        s.send(message.encode('utf-8'))
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
            #Prevent the wobble
            #if abs(axis) < 0.02:
            #    axis = 0

            #  Minimum jump value implemented to remove wobble
            min_jump = 0.05

            if i == 0 and abs(axis-yaw) > min_jump:
                yaw = axis - 0.051
            if i == 1 and abs(axis-throttle) > min_jump:
                throttle = (axis +0.004)*-1
            if i == 2 and abs(axis-roll) > min_jump:
                roll = axis + 0.027
            if i == 3 and abs(axis-pitch) > min_jump:
                pitch = (axis + 0.020) * -1

        buttons = joystick.get_numbuttons()

        #button = joystick.get_button(3)

        selectBut = joystick.get_button(0)


        # Hat switch. All or nothing for direction, not like joysticks.
        # Value comes back in an array.
        hats = joystick.get_numhats()

        for i in range( hats ):
            hat = joystick.get_hat( i )
    
    ####Prepare to send, currently hardcoded to call settings -  Custom
    send_pitch = int(mid_cal + 90*pitch) - 3
    send_yaw = int(mid_cal + 90*yaw) - 2
    send_roll =int(mid_cal + 90*roll) - 3
    send_throttle = int(mid_cal +90*throttle)


    #####Send commands out
    try:
        heartbeat = s.recv(5)
    except:
        print("Lost connection...")
        cannypid = cannyon.pid
        os.kill(cannypid, signal.SIGINT)
        break
    # ------ NEED TO FIND HOW TO GET START BUTTON ------
    '''if button:
        StartYourEngines(heartbeat)
        heartbeat = 0
        heartbeat = s.recv(5)'''
    if selectBut:
        print("Switching feeds...")
        cannypid = cannyon.pid
        os.kill(cannypid, signal.SIGINT)
        if Canny == 1:
            cannyon = subprocess.Popen(
                ["/Users/austingreisman/Documents/University/Internship/Drone/udp-image-streaming/./server", "8080",
                 "1"], stdout=devnull, shell=False)
            Canny = 0
        else:
            cannyon = subprocess.Popen(
                ["/Users/austingreisman/Documents/University/Internship/Drone/udp-image-streaming/./server", "8080",
                 "0"], stdout=devnull, shell=False)
            Canny = 1
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
