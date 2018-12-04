#! python
#Created for Mission Critial Drone Project for Ericsson
#Code to be run on Pi on Drone
#Austin Greisman

import socket
import Adafruit_PCA9685
import time
import re
import sys
import select


pwm = Adafruit_PCA9685.PCA9685()
#Values were deteremind to be the ZERO and MIN points for the proper PWM widths sent to onboard flight controller
MIN_VALUE = 230
ZERO_VALUE = 325

#Frequency determind from someone who hacked the NAZAM-V2. Possible this could be changed. But it does work.
#Link here for reference: https://github.com/minla-rc/Minla-LTE-Receiver/raw/master/documentation/minla_pinout_and_naza_connection_v0.35_EN.pdf
pwm.set_pwm_freq(50)
# Output file for logging
current_output_name = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())

output_file = open("/home/pi/Adafruit_Python_PCA9685/examples/logs/%s.log" % (current_output_name), 'w')

# If system disconnects, this function is run to automatically land the Drone safely.
def disconnected(c, s):
    printboth("Cannot Send... Must be disconnected from Controller... Resetting Speeds...")
    talktopi(ZERO_VALUE, ZERO_VALUE, ZERO_VALUE, ZERO_VALUE)
    time.sleep(1)
    talktopi(ZERO_VALUE, ZERO_VALUE, MIN_VALUE, ZERO_VALUE)
    c.close()
    s.close()

def printboth(line):
    sys.stdout.write("%s\n" % (line))
    output_file.write("%s\n" % (line))

#A = Roll, E = Pitch, T = Throttle, R = Yaw
#Sends the proper PWM widths over the PWM board to the drone
def talktopi(aileron, elevator, throttle, rudder):
    printboth("Roll: %s, Pitch: %s, Yaw: %s, Throttle: %s, "%(aileron, elevator, rudder, throttle))
    
    pwm.set_pwm(0, 0, int(aileron)) #A
    pwm.set_pwm(3, 0, int(elevator))  # E
    pwm.set_pwm(4, 0, int(throttle))  # T
    pwm.set_pwm(7, 0, int(rudder))  # R
    time.sleep(0.01)

def Main():

    printboth("\n\n\n New Execution @%s....\n\n\n"%(time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())))
    values = []
    # Auto grab host name (Drone IP and Port that it's listening on)
    ip = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip.connect(("8.8.8.8", 80))
    host = ip.getsockname()[0]
    port = 6970

    #Listing properties
    printboth("Server IP: %s"%(host))
    printboth("Server PORT: %d"%(port))

    s = socket.socket()
    s.bind((host, port))

    #Waiting for connection from computer
    s.listen(1)
    c, addr = s.accept()
    c.settimeout(3)
    printboth("Connection from: " + str(addr))
    while True:
        #Trys to send data to Controller to maintain sync
        try:
            c.send('1')
        except:
            disconnected()
            break

        #Recieves data from Controller to grab current values
        #Format ####,####,####,#### = 8 bits * 4 numbers * 4 pairs + 4 commas = 132 bits. Did 160 bits just to be safe
        try:
            data = c.recv(160).decode('utf-8')
        except socket.error, e:
            err = e.args[0]
            if err == 'timed out':
                disconnected(c, s)
                break
            else:
                printboth(e)
                break
        # A = Roll, E = Pitch, T = Throttle, R = Ya
        values = re.split(",+", data)
        try:
            talktopi(values[0], values[1], values[2], values[3])
        except IndexError:
            printboth("Index Error... Most likely connection down..")
            disconnected(c, s)
            break
    c.close()
    s.close()

    #Go again
    #Main()

if __name__ == '__main__':
	# Ensures the program does not crash on the PI!
    while True:
        try:
            Main()
            time.sleep(5)
        except socket.error, e:
            try:
                err = e.args[0]
            except:
	        output_file.close()
                print("KeyboardInterrupt... Output file closed...")
                break

            if err == 101:
                printboth("Network is unreachable.. Connecting..")
                time.sleep(10)
            elif err == 98:
                printboth("Socket is unavailable... Waiting")
                time.sleep(10)
            else:
                printboth(">%s< &%s "%(err, e))
                output_file.close()
                print("Output file closed...")
                break
 

