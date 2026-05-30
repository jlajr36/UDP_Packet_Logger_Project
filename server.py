import socket
import threading
import tkinter as tk

HOST = "0.0.0.0"
PORT = 9999

class UDPListener:
    def __init__(self, root):
        self.root = root
        self.root.title("UDP Listener")

        self.message_label = tk.Label(
            root,
            text="Waiting for data...",
            font=("Arial", 14),
            width=50,
            height=5,
            wraplength=500
        )
        self.message_label.pack(padx=20, pady=20)

        self.toggle_udp_button = tk.Button(
            root,
            text="Start Listening",
            command=self.toggle_udp
        )
        self.toggle_udp_button.pack(pady=10)

        self.running = False
        self.sock = None
        self.thread = None

    def toggle_udp(self):
        if not self.running:
            #START
            self.running = True
            self.toggle_udp_button.config(text="Stop Listening")

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((HOST, PORT))
            
            # IMPORTANT: prevents blocking forever
            self.sock.settimeout(1.0)

            # IMPORTANT: prevents blocking forever
            self.thread = threading.Thread(target=self.listen_udp, daemon=True)
            self.thread.start()
        
        else:
            # STOP
            self.running = False
            self.toggle_udp_button.config(text="Start Listening")

            if self.sock:
                self.sock.close()
                self.sock = None

    def listen_udp(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = data.decode("utf-8")

                # Safely update Tkinter UI from thread
                self.root.after(
                    0,
                    self.update_label,
                    f"{addr[0]}:{addr[1]} → {message}"
                )

            except socket.timeout:
                # normal loop check
                continue

            except OSError:
                # socket closed
                break
        
    def update_label(self, message):
        self.message_label.config(text=message)

root = tk.Tk()
app = UDPListener(root)
root.mainloop()