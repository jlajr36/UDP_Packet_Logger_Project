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
    sock.bind(("0.0.0.0", port))

    print_queue.put(f"[+] Data Listener: Listening on UDP port {port}")

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            sender_ip = addr[0]
            slot_name = IP_TO_SLOT.get(sender_ip, "Unknown Slot")
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            msg = f"[{current_time}] [{slot_name}] Port {port} <- Received {len(data)} bytes from {sender_ip}"
            print_queue.put(msg)        
        except Exception as e:
            print_queue.put(f"[PORT {port}] Error: {e}")

def listen_commands(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))

    print_queue.put(f"[+] Command Listener: Listening on UDP port {port}")

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            sender_ip = addr[0]
            slot_name = IP_TO_SLOT.get(sender_ip, "Unknown Slot")
            
            # Decode the command payload
            try:
                command = data.decode('utf-8').strip()
            except UnicodeDecodeError:
                command = f"<Non-text data: {data.hex()}>"

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            print_queue.put(f"[{current_time}] [COMMAND] From {slot_name} ({sender_ip}): {command}")
            
            # --- Handle your commands here ---
            # Example:
            # if command == "REBOOT":
            #     trigger_reboot_logic(sender_ip)
            # ---------------------------------

        except Exception as e:
            print_queue.put(f"[COMMAND PORT {port}] Error: {e}")

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

    print_queue.put("[*] UDP listeners running. Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")

if __name__ == "__main__":
    main()