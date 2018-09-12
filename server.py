#! python
import socket

def Main():
    # Auto grab host name
    ip = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip.connect(("8.8.8.8", 80))
    host = ip.getsockname()[0]
    port = 6969

    #Listing properties
    print("Server IP: %s"%(host))
    print("Server PORT: %d"%(port))

    s = socket.socket()
    s.bind((host, port))

    s.listen(1)
    c, addr = s.accept()
    print("Connection from: " + str(addr))
    while True:
        data = c.recv(1024).decode('utf-8')
        if not data:
            break
        print("From connected user: " + data)
        data = data.upper()
        print("Sending: " + data)
        c.send(data.encode('utf-8'))
    c.close()

if __name__ == '__main__':
    Main()