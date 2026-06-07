import socket
import threading
import time
import queue
import signal  # Used to intercept and suppress Ctrl+C
from datetime import datetime
import env

# Environment Configuration
UDP_PORTS = env.UDP_PORTS
SELECTED_IPS = env.SELECTED_IPS
COMMAND_PORT = env.COMMAND_PORT
BUFFER_SIZE = 4096

# Thread-safe Print Queue
print_queue = queue.Queue()

# Global State Control
is_logging = False
is_logging_lock = threading.Lock()
shutdown_event = threading.Event()


def build_slot_map(ips_list):
    """Maps individual IPs to their respective human-readable Slot identifiers."""
    slot_map = {}
    for index, ip_pair in enumerate(ips_list):
        slot_name = f"Slot {index + 1}"
        for ip in ip_pair:
            slot_map[ip] = slot_name
    return slot_map


IP_TO_SLOT = build_slot_map(SELECTED_IPS)


def ignore_ctrl_c(signum, frame):
    """Callback to log and bypass Ctrl+C keystrokes."""
    print_queue.put("[!] Warning: KeyboardInterrupt ignored. Use the UDP 'QUIT' command to exit.")


def print_worker():
    """Consumes and prints messages from the print queue."""
    while True:
        try:
            msg = print_queue.get(timeout=0.5)
            print(msg)
            print_queue.task_done()
        except queue.Empty:
            if shutdown_event.is_set():
                break


def listen_udp(port):
    """Listens for data payloads on a specific UDP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.bind(("0.0.0.0", port))
            print_queue.put(f"[+] Data Listener: Listening on UDP port {port}")
        except Exception as e:
            print_queue.put(f"[-] Data Listener Failed to bind on port {port}: {e}")
            return

        sock.settimeout(1.0)

        while not shutdown_event.is_set():
            try:
                try:
                    data, addr = sock.recvfrom(BUFFER_SIZE)
                except socket.timeout:
                    continue

                # Quick state verification
                with is_logging_lock:
                    logging_active = is_logging

                if not logging_active:
                    continue

                sender_ip = addr[0]
                slot_name = IP_TO_SLOT.get(sender_ip, "Unknown Slot")
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                
                msg = f"[{current_time}] [{slot_name}] Port {port} <- Received {len(data)} bytes from {sender_ip}"
                print_queue.put(msg)
            except Exception as e:
                print_queue.put(f"[PORT {port}] Error: {e}")
                time.sleep(1)
        
        print_queue.put(f"[-] Data Listener on port {port} shut down.")


def listen_commands(port):
    """Listens for inbound operational commands on the designated command port."""
    global is_logging
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.bind(("0.0.0.0", port))
            print_queue.put(f"[+] Command Listener: Listening on UDP port {port}")
        except Exception as e:
            print_queue.put(f"[-] Command Listener Failed to bind on port {port}: {e}")
            return

        sock.settimeout(1.0)

        while not shutdown_event.is_set():
            try:
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
        
        print_queue.put("[-] Command Listener shut down.")


def main():
    # Override standard Ctrl+C handling globally
    signal.signal(signal.SIGINT, ignore_ctrl_c)

    # Start up the printing sub-thread
    t_print = threading.Thread(target=print_worker, daemon=True)
    t_print.start()

    threads = []

    # Initialize data pipeline streams
    for port in UDP_PORTS:
        t = threading.Thread(target=listen_udp, args=(port,), daemon=True)
        t.start()
        threads.append(t)

    # Initialize command control stream
    t_cmd = threading.Thread(target=listen_commands, args=(COMMAND_PORT,), daemon=True)
    t_cmd.start()
    threads.append(t_cmd)

    print_queue.put("[*] UDP listeners running. System is LOCKED. Send UDP 'QUIT' command to exit.")

    # Primary execution loop - can now only be broken by shutdown_event
    while not shutdown_event.is_set():
        time.sleep(0.5)

    # Wait for networking threads to finish up active cycles cleanly
    for t in threads:
        t.join(timeout=2.0)

    # Process outstanding items remaining in print queue
    print_queue.join()
    print("[*] System completely shutdown.")


if __name__ == "__main__":
    main()