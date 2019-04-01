#! python
#Created for Mission Critial Drone Project for Ericsson
#Code to be run on Pi on Drone
#Austin Greisman

import socket
import board
import busio
import adafruit_pca9685
import time
import re
import sys
import select
from simple_pid import PID

import ultrasonic #call distance() returns cm
import gps        #returns dic of parameters
from threading import Thread
import AppIot_Drone_Send

import AngleMeterAlpha #kalman filter with MPU6050
mpu = AngleMeterAlpha.AngleMeterAlpha()
mpu.MPU_Init()
mpu.measure()
# Begin calling measurements
#mpu.get_kalman_roll()
#mpu.get_kalman_pitch()

#For integrating Accelerometer and Gyroscope: https://github.com/Tijndagamer/mpu6050
#from mpu6050 import mpu6050

#sensor = mpu6050(0x68) #0x68 is memory address on i2C
#Functions available
#.get_temp() -> temp in *C
#.get_gyro_data() -> Gyro data in param format. Access with sensor['x'] to get x value.
#.get_accel_data() -> Same as Gyro m/s^2

# If gyro
i2c = busio.I2C(board.SCL, board.SDA)
pwm = adafruit_pca9685.PCA9685(i2c)
#pwm = Adafruit_PCA9685.PCA9685()
#Values were deteremind to be the ZERO and MIN points for the proper PWM widths sent to onboard flight controller
#These have now been tested in the lab and are infact correct! Creates pulse widths beteen 1-2ms. Zero value = 1.5ms at 50hz
MIN_VALUE  = 3807
ZERO_VALUE = 5246
MAX_VALUE  = 6685

#Frequency determind from someone who hacked the NAZAM-V2. Possible this could be changed. But it does work.
#Link here for reference: https://github.com/minla-rc/Minla-LTE-Receiver/raw/master/documentation/minla_pinout_and_naza_connection_v0.35_EN.pdf
pwm.frequency = 50
# Output file for logging
current_output_name = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())

output_file = open("/home/pi/Adafruit_Python_PCA9685/examples/logs/%s.log" % (current_output_name), 'w')

def printboth(line):
    sys.stdout.write("%s\n" % (line))
    output_file.write("%s\n" % (line))
    
def AutoLand():
    #ultrasonic.distance() returns distance in cm. 11cm is height from ground. 12 should be good then to drop
    LandPID = PID(-0.5, 0.1, 0.05, setpoint=12)
    LandPID.sample_time = 0.01
    pid.output_limits = (300, 325)    # output value will be between 0 and 10
    #Current distance away
    distance = ultrasonic.distance()
    while distance > 12:
        control = LandPID(distance)
        #Change throttle - control needs to be between 240-420
        talktopi(ZERO_VALUE, ZERO_VALUE, control, ZERO_VALUE)
        #update distance
        distance = ultrasonic.distance()
    #Turn off motors
    talktopi(ZERO_VALUE, ZERO_VALUE, MIN_VALUE, ZERO_VALUE)
    time.sleep(1)

def IoT_send():#(OperatingStatus_Value, Longitude_Value, Latitude_Value, Altitude_Value, Speed_Value, CameraOnOff_Value, RemainingBattery_Value, RemainingFlight_Value, CommandString_Value):
    #Run daily regression
    gpsData = gps.get_data()
    if gpsData != 'Waiting for Fix':
        printboth("Sending data to IoT Accelerator...")
        AppIot_Drone_Send.run("1", gpsData['Longitude'], gpsData['Latitude'], gpsData['Altitude'], gpsData['Speed'], "1", "90", "80", "SNAFU")
        printboth("Sent...")
    else:
        printboth("Wating for fix")
    
# If system disconnects, this function is run to automatically land the Drone safely. Need to add in Ultrasonic sense
def disconnected(c, s):
    printboth("Cannot Send... Must be disconnected from Controller... Resetting Speeds...")
    talktopi(ZERO_VALUE, ZERO_VALUE, ZERO_VALUE, ZERO_VALUE)
    time.sleep(1)
    talktopi(ZERO_VALUE, ZERO_VALUE, MIN_VALUE, ZERO_VALUE)
    c.close()
    s.close()

#A = Roll, E = Pitch, T = Throttle, R = Yaw
#Sends the proper PWM widths over the PWM board to the drone
def talktopi(aileron, elevator, throttle, rudder):
    printboth("Roll: %s, Pitch: %s, Yaw: %s, Throttle: %s, "%(aileron, elevator, rudder, throttle))
    
    pwm.channels[0].duty_cycle = int(aileron) #A
    pwm.channels[3].duty_cycle = int(elevator)  # E
    pwm.channels[4].duty_cycle = int(throttle)  # T
    pwm.channels[7].duty_cycle = int(rudder)  # R
    time.sleep(0.01)

def Main():
    #Local variable def
    printboth("\n\n\n New Execution @%s....\n\n\n"%(time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())))
    values = []
    # Auto grab host name (Drone IP and Port that it's listening on)
    ip = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip.connect(("8.8.8.8", 80))
    host = ip.getsockname()[0]
    port = 6970

    #Listing properties -> Changed for VPN 0.0.0.0 (Allows all connections)
    printboth("Server IP: 0.0.0.0")
    printboth("Server PORT: %d"%(port))

    s = socket.socket()
    s.bind(('0.0.0.0', port))

    #Waiting for connection from computer
    s.listen(1)
    c, addr = s.accept()
    c.settimeout(3)
    printboth("Connection from: " + str(addr))
    threadcounter = 0
    while True:
        #Trys to send data to Controller to maintain sync
        try:
            c.send('1'.encode('utf-8'))
        except:
            disconnected(c, s)
            break
        #Recieves data from Controller to grab current values
        #Format ####,####,####,#### = 8 bits * 4 numbers * 4 pairs + 4 commas = 132 bits. Did 160 bits just to be safe
        #Newer Format ####,####,####,####,####,####,####,####
        try:
            data = c.recv(160).decode('utf-8')
        except socket.error as e:
            err = e.args[0]
            if err == 'timed out':
                disconnected(c, s)
                break
            elif err == 104:
                printboth("Disconnected by controller")
                disconnected(c, s)
                break
            else:
                printboth(e)
                break
        # A = Roll, E = Pitch, T = Throttle, R = Yaw
        values = re.split(",+", data)
        try:
            talktopi(values[0], values[1], values[2], values[3])
            #Do some more stuff here
            #gpsData = gps.get_data()
            thread = Thread(target = IoT_send)
            thread.daemon = True
            if not thread.isAlive() and threadcounter > 100:
                thread.start()
                threadcounter = 0
                print("Thread Reset")
            #print(gpsData)
            #IoT_send("1", gpsData['Longitude'], gpsData['Latitude'], gpsData['Altitude'], gpsData['Speed'], "1", "90", "80", "SNAFU")
            threadcounter += 1
            #Finish doing more stuff here
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
        except socket.error as e:
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
 
