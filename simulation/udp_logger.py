import socket
import threading
import time
import queue
import env

UDP_PORTS = env.UDP_PORTS
BUFFER_SIZE = 4096

print_queue = queue.Queue()

def print_worker():
    while True:
        msg = print_queue.get()
        print(msg)
        print_queue.task_done()

def listen_udp(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))

    print_queue.put(f"[+] Listening on UDP port {port}")

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            msg = f"[PORT {port}] From {addr}: {data.decode(errors='replace')}"
            print_queue.put(msg)        
        except Exception as e:
            print_queue.put(f"[PORT {port}] Error: {e}")
            break

def main():
    t_print = threading.Thread(target=print_worker, daemon=True)
    t_print.start()

    threads = []

    for port in UDP_PORTS:
        t = threading.Thread(target=listen_udp, args=(port,), daemon=True)
        t.start()
        threads.append(t)

    print_queue.put("[*] UDP listeners running. Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")

if __name__ == "__main__":
    main()