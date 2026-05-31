import socket
import threading
import tkinter as tk

HOST = "0.0.0.0"
PORTS = [9995, 9996, 9997, 9998, 9999]

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
        self.socks = []
        self.threads = []

    def toggle_udp(self):
        if not self.running:
            # START
            self.running = True
            self.toggle_udp_button.config(text="Stop Listening")

            for port in PORTS:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((HOST, port))

                # IMPORTANT: prevents blocking forever
                sock.settimeout(1.0)

                # IMPORTANT: prevents blocking forever
                thread = threading.Thread(
                    target=self.listen_udp,
                    args=(sock, port),
                    daemon=True
                )
                self.socks.append(sock)
                self.threads.append(thread)
                thread.start()
        
        else:
            # STOP
            self.running = False
            self.toggle_udp_button.config(text="Start Listening")

            for sock in self.socks:
                try:
                    sock.close()
                except:
                    pass

            for thread in self.threads:
                thread.join(timeout=1.1) 

            self.socks.clear()
            self.threads.clear()

    def listen_udp(self, sock, port):
        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                message = data.decode("utf-8", errors="replace")

                # Safely update Tkinter UI from thread
                self.root.after(
                    0,
                    self.update_label,
                    f"[PORT {port}] {addr[0]}:{addr[1]} → {message}"
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