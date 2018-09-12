import socket
import os
import time

def Main():
    # Auto grab host name
    ip = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip.connect(("8.8.8.8", 80))
    host = ip.getsockname()[0]
    port = 6969

    print("Successfully connected to network... Starting thermal")
    os.system("/home/pi/Drone/libseek-thermal/examples/./seek_viewerUDP --colormap=11")
    print("Thermal UDP stream started")

if __name__ == '__main__':
    while True:
        try:
            Main()
            time.sleep(5)
        except socket.error, e:
            err = e.args[0]
            if err == 101:
                print("Network is unreachable.. Connecting..")
                time.sleep(10)
            elif err == 98:
                print("Socket is unavailable... Waiting")
                time.sleep(10)
            else:
                print(">%s< &%s "%(err, e))
                break

