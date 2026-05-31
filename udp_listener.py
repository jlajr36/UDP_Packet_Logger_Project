import socket
import threading
import tkinter as tk
from tkinter import ttk
import time

HOST = "0.0.0.0"
PORTS = [9995, 9996, 9997, 9998, 9999]

class UDPListener:
    def __init__(self, root):
        self.root = root
        self.root.title("UDP Telemetry Dashboard")

        self.clients = {}

        self.tree = ttk.Treeview(
            root,
            columns=("ip", "device", "seq", "value", "age"),
            show="headings",
            height=15
        )

        self.tree.heading("ip", text="IP")
        self.tree.heading("device", text="DEVICE")
        self.tree.heading("seq", text="SEQ")
        self.tree.heading("value", text="VALUE")
        self.tree.heading("age", text="AGE")

        self.tree.column("ip", width=140)
        self.tree.column("device", width=100)
        self.tree.column("seq", width=80)
        self.tree.column("value", width=200)
        self.tree.column("age", width=100)

        self.tree.pack(padx=10, pady=10)

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

    def parse_message(self, message):
        data = {}
        for part in message.split("|"):
            if "=" in part:
                k, v = part.split("=", 1)
                data[k] = v
        return data

    def listen_udp(self, sock, port):
        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                message = data.decode("utf-8", errors="replace")

                ip = addr[0]
                parsed = self.parse_message(message)

                device = parsed.get("ID", "UNKNOWN")
                seq = parsed.get("SEQ", "-")

                value = next(
                    (f"{k}={v}" for k, v in parsed.items()
                     if k not in ["ID", "SEQ", "TS", "JUL"]),
                    "-"
                )

                key = (ip, device)

                self.clients[key] = {
                    "ip": ip,
                    "device": device,
                    "seq": seq,
                    "value": value,
                    "last_seen": time.time()
                }

                self.root.after(0, self.refresh_table)

            except socket.timeout:
                # normal loop check
                continue

            except OSError:
                # socket closed
                break

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())

        now = time.time()

        for (ip, device), c in self.clients.items():
            age = round(now - c["last_seen"], 2)

            self.tree.insert(
                "",
                "end",
                values=(
                    ip,
                    device,
                    c["seq"],
                    c["value"],
                    f"{age}s"
                )
            )

root = tk.Tk()
app = UDPListener(root)
root.mainloop()