import socket
import threading
import time
import env

UDP_PORTS = env.UDP_PORTS
BUFFER_SIZE = 4096

def listen_udp(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))

    print(f"[+] Listening on UDP port {port}")

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            print(f"[PORT {port}] From {addr}: {data.decode(errors='replace')}")
        except Exception as e:
            print(f"[PORT {port}] Error: {e}")
            break

def main():
    threads = []

    for port in UDP_PORTS:
        t = threading.Thread(target=listen_udp, args=(port,), daemon=True)
        t.start()
        threads.append(t)

    print("[*] UDP listeners running. Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")

if __name__ == "__main__":
    main()