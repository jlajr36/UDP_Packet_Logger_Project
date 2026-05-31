import socket
import time

HOST = "127.0.0.1"
PORTS = [9995, 9996, 9997, 9998, 9999]

i = 0

print("Starting UDP client loop. Press Ctrl+C to stop.")

try:

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        while True: # Runs continuously 
            message = f"Hello from client message {i}"
            data = message.encode("utf-8")

            for port in PORTS:
                sock.sendto(data, (HOST, port))
                print(f"Sent to {port}: {message}")

            i += 1
            time.sleep(0.01)

except KeyboardInterrupt:
    print("\nStopping client. Goodbye!")