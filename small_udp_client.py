import socket
import time

HOST = "127.0.0.1"
PORTS = [9995, 9996, 9997, 9998, 9999]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

for i in range(1000):
    message = f"Hello from client massage {i}"
    data = message.encode("utf-8")

    for port in PORTS:
        sock.sendto(data, (HOST, port))
        print(f"Sent to {port}:", message)

    time.sleep(0.01)

sock.close()