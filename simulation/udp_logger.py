import socket
import threading
import time
import queue
import env
from datetime import datetime

UDP_PORTS = env.UDP_PORTS
SELECTED_IPS = env.SELECTED_IPS
COMMAND_PORT = env.COMMAND_PORT

BUFFER_SIZE = 4096

print_queue = queue.Queue()

# Global state control - Initialized to False so logging is OFF at startup
is_logging = False
is_logging_lock = threading.Lock()
shutdown_event = threading.Event()

def build_slot_map(ips_list):
    slot_map = {}
    for index, ip_pair in enumerate(ips_list):
        slot_name = f"Slot {index + 1}"
        for ip in ip_pair:
            slot_map[ip] = slot_name
    return slot_map

IP_TO_SLOT = build_slot_map(SELECTED_IPS)

def print_worker():
    while True:
        msg = print_queue.get()
        print(msg)
        print_queue.task_done()

def listen_udp(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("0.0.0.0", port))
        print_queue.put(f"[+] Data Listener: Listening on UDP port {port}")
    except Exception as e:
        print_queue.put(f"[-] Data Listener Failed to bind on port {port}: {e}")
        return

    while not shutdown_event.is_set():
        try:
            sock.settimeout(1.0)
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                continue

            with is_logging_lock:
                if not is_logging:
                    continue

            sender_ip = addr[0]
            slot_name = IP_TO_SLOT.get(sender_ip, "Unknown Slot")
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            msg = f"[{current_time}] [{slot_name}] Port {port} <- Received {len(data)} bytes from {sender_ip}"
            print_queue.put(msg)        
        except Exception as e:
            print_queue.put(f"[PORT {port}] Error: {e}")
            time.sleep(1)

def listen_commands(port):
    global is_logging
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("0.0.0.0", port))
        print_queue.put(f"[+] Command Listener: Listening on UDP port {port}")
    except Exception as e:
        print_queue.put(f"[-] Command Listener Failed to bind on port {port}: {e}")
        return

    while not shutdown_event.is_set():
        try:
            sock.settimeout(1.0)
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                continue

            sender_ip = addr[0]
            slot_name = IP_TO_SLOT.get(sender_ip, "Unknown Slot")
            
            try:
                command = data.decode('utf-8').strip()
            except UnicodeDecodeError:
                command = f"<Non-text data: {data.hex()}>"

            cmd_upper = command.upper()
            if cmd_upper != "QUIT":
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                print_queue.put(f"[{current_time}] [COMMAND] From {slot_name} ({sender_ip}): {command}")
            
            response = ""

            if cmd_upper == "START":
                with is_logging_lock:
                    is_logging = True
                response = "ACK: Logging started"
                print_queue.put("[*] System State: Logging ENABLED")

            elif cmd_upper == "STOP":
                with is_logging_lock:
                    is_logging = False
                response = "ACK: Logging stopped"
                print_queue.put("[*] System State: Logging DISABLED")

            elif cmd_upper == "ALIVE":
                with is_logging_lock:
                    status = "running (logging active)" if is_logging else "running (logging stopped)"
                response = f"ACK: Application is {status}"

            elif cmd_upper == "QUIT":
                response = "ACK: Application quitting"
                shutdown_event.set()

            else:
                response = f"ERR: Unknown command '{command}'"

            try:
                sock.sendto(response.encode('utf-8'), addr)
            except Exception as send_err:
                print_queue.put(f"[-] Failed to send echo response to {addr}: {send_err}")

        except Exception as e:
            print_queue.put(f"[COMMAND PORT {port}] Error: {e}")
            time.sleep(1)

def main():
    t_print = threading.Thread(target=print_worker, daemon=True)
    t_print.start()

    threads = []

    for port in UDP_PORTS:
        t = threading.Thread(target=listen_udp, args=(port,), daemon=True)
        t.start()
        threads.append(t)

    t_cmd = threading.Thread(target=listen_commands, args=(COMMAND_PORT,), daemon=True)
    t_cmd.start()
    threads.append(t_cmd)

    print_queue.put("[*] UDP listeners running. Use UDP command 'quit' to exit.")

    while not shutdown_event.is_set():
        try:
            time.sleep(0.5)
        except KeyboardInterrupt:
            pass

    print_queue.join() 

if __name__ == "__main__":
    main()