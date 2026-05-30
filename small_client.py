import socket
import time

HOST = "127.0.0.1"
PORT = 9999

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

for i in range(1000):
    message = f"Hello from client massage {i}"
    sock.sendto(message.encode("utf-8"), (HOST, PORT))
    print("Sent:", message)
    time.sleep(.001)

sock.close()