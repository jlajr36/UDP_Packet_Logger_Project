import socket
import threading
import time
import queue
import signal  # Intercepts and suppresses Ctrl+C
from datetime import datetime
import env

# Environment Configuration
UDP_PORTS = env.UDP_PORTS
SELECTED_IPS = env.SELECTED_IPS
COMMAND_PORT = env.COMMAND_PORT
BUFFER_SIZE = 4096

# Centralized safe execution queue (Holds logs to print and write)
logging_queue = queue.Queue()

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
    logging_queue.put(("CONSOLE", "[!] Warning: KeyboardInterrupt ignored. Use the UDP 'QUIT' command to exit."))


def logging_worker():
    """
    Consumes logging entries. Decides whether to print to terminal 
    or dynamically build and dump contents to specific Slot files.
    """
    # Track open file handles per slot. Created lazily when data arrives.
    slot_files = {}

    while True:
        try:
            # Short timeout allows checking the shutdown event periodically
            item = logging_queue.get(timeout=0.5)
            target, message = item
            
            # Print everything to terminal console
            print(message)
            
            # If target belongs to a specific slot, write cleanly to its file
            if target.startswith("Slot "):
                if target not in slot_files:
                    # File names use platform safe format: Slot_X_YYYY-MM-DD_HH-MM-SS.log
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    filename = f"{target.replace(' ', '_')}_{timestamp}.log"
                    slot_files[target] = open(filename, "a", encoding="utf-8", buffering=1) # Line buffered
                
                slot_files[target].write(message + "\n")

            logging_queue.task_done()
        except queue.Empty:
            if shutdown_event.is_set():
                break

    # Clean shutdown: Close all file streams that were dynamically opened
    for slot_name, file_handle in slot_files.items():
        try:
            file_handle.close()
        except Exception:
            pass


def listen_udp(port):
    """Listens for data payloads on a specific UDP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.bind(("0.0.0.0", port))
            logging_queue.put(("CONSOLE", f"[+] Data Listener: Listening on UDP port {port}"))
        except Exception as e:
            logging_queue.put(("CONSOLE", f"[-] Data Listener Failed to bind on port {port}: {e}"))
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
                
                # Send target string along to assign file routing automatically
                logging_queue.put((slot_name, msg))
            except Exception as e:
                logging_queue.put(("CONSOLE", f"[PORT {port}] Error: {e}"))
                time.sleep(1)
        
        logging_queue.put(("CONSOLE", f"[-] Data Listener on port {port} shut down."))


def listen_commands(port):
    """Listens for inbound operational commands on the designated command port."""
    global is_logging
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.bind(("0.0.0.0", port))
            logging_queue.put(("CONSOLE", f"[+] Command Listener: Listening on UDP port {port}"))
        except Exception as e:
            logging_queue.put(("CONSOLE", f"[-] Command Listener Failed to bind on port {port}: {e}"))
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
                    logging_queue.put(("CONSOLE", f"[{current_time}] [COMMAND] From {slot_name} ({sender_ip}): {command}"))
                
                response = ""

                if cmd_upper == "START":
                    with is_logging_lock:
                        is_logging = True
                    response = "ACK: Logging started"
                    logging_queue.put(("CONSOLE", "[*] System State: Logging ENABLED"))

                elif cmd_upper == "STOP":
                    with is_logging_lock:
                        is_logging = False
                    response = "ACK: Logging stopped"
                    logging_queue.put(("CONSOLE", "[*] System State: Logging DISABLED"))

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
                    logging_queue.put(("CONSOLE", f"[-] Failed to send echo response to {addr}: {send_err}"))

            except Exception as e:
                logging_queue.put(("CONSOLE", f"[COMMAND PORT {port}] Error: {e}"))
                time.sleep(1)
        
        logging_queue.put(("CONSOLE", "[-] Command Listener shut down."))


def main():
    # Override standard Ctrl+C handling globally
    signal.signal(signal.SIGINT, ignore_ctrl_c)

    # Start up the logging/printing sub-thread
    t_log = threading.Thread(target=logging_worker, daemon=True)
    t_log.start()

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

    logging_queue.put(("CONSOLE", "[*] UDP listeners running. System is LOCKED. Send UDP 'QUIT' command to exit."))

    # Primary execution loop - can now only be broken by shutdown_event
    while not shutdown_event.is_set():
        time.sleep(0.5)

    # Wait for networking threads to finish up active cycles cleanly
    for t in threads:
        t.join(timeout=2.0)

    # Process outstanding items remaining in logging queue
    logging_queue.join()
    print("[*] System completely shutdown.")


if __name__ == "__main__":
    main()