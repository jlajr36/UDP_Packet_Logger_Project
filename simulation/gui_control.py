import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from datetime import datetime
import env

# Fetch target connection info from your environment configuration
# Assuming env.py contains COMMAND_PORT. We target localhost for testing, 
# but change "127.0.0.1" to your server's actual IP if running remotely.
SERVER_IP = "127.0.0.1"
SERVER_PORT = env.COMMAND_PORT
BUFFER_SIZE = 4096


class UDPControllerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("UDP Server Controller")
        self.root.geometry("500x400")
        self.root.minsize(450, 350)

        # Build UI layout
        self.create_widgets()

    def create_widgets(self):
        # Top Section: Connection Info
        info_frame = tk.LabelFrame(self.root, text=" Target Server Config ", padx=10, pady=5)
        info_frame.pack(fill="x", padx=15, pady=10)

        tk.Label(info_frame, text=f"IP Target: {SERVER_IP}").pack(side="left", padx=5)
        tk.Label(info_frame, text=f"Port: {SERVER_PORT}").pack(side="left", padx=20)

        # Middle Section: Command Buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=15, pady=5)

        # Style configurations
        btn_config = {"font": ("Arial", 10, "bold"), "width": 10, "pady": 5}

        self.btn_start = tk.Button(btn_frame, text="START", bg="#d4edda", fg="#155724", 
                                   command=lambda: self.trigger_send("START"), **btn_config)
        self.btn_start.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_stop = tk.Button(btn_frame, text="STOP", bg="#fff3cd", fg="#856404", 
                                  command=lambda: self.trigger_send("STOP"), **btn_config)
        self.btn_stop.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_alive = tk.Button(btn_frame, text="ALIVE", bg="#cce5ff", fg="#004085", 
                                   command=lambda: self.trigger_send("ALIVE"), **btn_config)
        self.btn_alive.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_quit = tk.Button(btn_frame, text="QUIT", bg="#f8d7da", fg="#721c24", 
                                  command=self.confirm_quit, **btn_config)
        self.btn_quit.pack(side="left", padx=5, expand=True, fill="x")

        # Bottom Section: Console Log output
        log_frame = tk.LabelFrame(self.root, text=" Response Console ", padx=10, pady=5)
        log_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.console = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, font=("Courier New", 9))
        self.console.pack(fill="both", expand=True)
        self.console.config(state="disabled") # Read-only console

    def append_log(self, text):
        """Safely updates the text console log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.config(state="normal")
        self.console.insert(tk.END, f"[{timestamp}] {text}\n")
        self.console.see(tk.END)
        self.console.config(state="disabled")

    def confirm_quit(self):
        """Asks for confirmation before shutting down the remote system."""
        if messagebox.askyesno("Confirm Remote Termination", 
                               "Are you sure you want to send the QUIT command?\nThis shuts down the remote server script completely."):
            self.trigger_send("QUIT")

    def trigger_send(self, command_str):
        """Spins off networking actions to a background thread to prevent UI lockup."""
        threading.Thread(target=self.send_udp_command, args=(command_str,), daemon=True).start()

    def send_udp_command(self, command):
        """Handles the socket lifecycle and blocks for responses in the background."""
        self.append_log(f"Sending command: '{command}'...")
        
        # Open an ephemeral socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(2.5)  # Don't hang indefinitely if server is offline
            
            try:
                # Send command payload
                sock.sendto(command.encode('utf-8'), (SERVER_IP, SERVER_PORT))
                
                # Await matching server acknowledgment echo
                data, addr = sock.recvfrom(BUFFER_SIZE)
                response = data.decode('utf-8')
                self.append_log(f"Response <- {response}")
                
            except socket.timeout:
                self.append_log("[-] Error: Request timed out. Is the server running?")
            except Exception as e:
                self.append_log(f"[-] Network Error: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = UDPControllerApp(root)
    root.mainloop()