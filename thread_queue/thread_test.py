import math
import queue
import time
import threading
import tkinter as tk


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Queue")

        # Thread-safe communication channel between worker thread and GUI thread
        self.q = queue.Queue()

        # Used to signal the worker thread to stop gracefully
        self.stop_event = threading.Event()

        # Will hold reference to the worker thread
        self.worker = None

        # --- UI SETUP ---
        self.start_btn = tk.Button(root, text="Start", command=self.start)
        self.start_btn.pack(pady=5)

        self.stop_btn = tk.Button(root, text="Stop", command=self.stop)
        self.stop_btn.pack(pady=5)

        self.text = tk.Text(root, width=60, height=20)
        self.text.pack()

        # IMPORTANT IDEA:
        # Tkinter is single-threaded → we poll the queue periodically
        self.root.after(100, self.check_queue)

    def producer(self):
        """
        Background worker thread.

        IMPORTANT IDEA:
        - This runs outside the GUI thread
        - It must NOT touch Tkinter widgets directly
        - It communicates ONLY through the queue
        """

        n = 1

        while not self.stop_event.is_set():
            # Heavy CPU-bound work (simulating load)
            # NOTE: Python threads won't parallelize CPU due to the GIL
            result = sum(math.sin(i * n) for i in range(10000))

            # Send result to GUI thread safely
            self.q.put(f"n={n} result={result:.4f}")

            n += 1

            # Small sleep just to slow down output (not required for correctness)
            time.sleep(0.2)

    def start(self):
        """
        Start worker thread if not already running.
        """

        # Prevent starting multiple worker threads accidentally
        if self.worker and self.worker.is_alive():
            return

        # Clear stop flag so thread can run again
        self.stop_event.clear()

        # Create and launch background thread
        self.worker = threading.Thread(
            target=self.producer,
            daemon=True  # thread exits automatically when program closes
        )
        self.worker.start()

        self.text.insert(tk.END, "Started\n")

    def stop(self):
        """
        Signal worker thread to stop.
        """

        # This does NOT kill the thread immediately.
        # Instead, the thread checks this flag periodically.
        self.stop_event.set()

        self.text.insert(tk.END, "Stopped\n")

    def check_queue(self):
        """
        Runs in the GUI thread.

        IMPORTANT IDEA:
        - This is the "bridge" between worker thread and UI
        - Tkinter cannot be updated from background threads safely
        """

        # Drain all available messages from queue
        while not self.q.empty():
            msg = self.q.get()

            # Safe: we are in the main thread
            self.text.insert(tk.END, msg + "\n")
            self.text.see(tk.END)

        # Re-schedule this function (event loop pattern)
        self.root.after(100, self.check_queue)


# --- PROGRAM ENTRY POINT ---

root = tk.Tk()
app = App(root)
root.mainloop()