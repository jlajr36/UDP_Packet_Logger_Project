import socket
import time
import random

HOST = "127.0.0.1"
PORTS = [9995, 9996, 9997, 9998, 9999]

i = 0

print("Starting UDP client loop with dynamic IoT metrics. Press Ctrl+C to stop.")

try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        while True: # Runs continuously 
            temp = round(22.0 + random.uniform(-1.5, 1.5), 1)
            voltage = round(120.0 + random.uniform(-2.0, 2.0), 1)
            cpu = round(10.0 + random.uniform(0.0, 45.0), 1)
            motion = random.choice([0, 0, 0, 0, 1]) # 20% chance of motion
            messages = [
                f"ID=ENV_01|SEQ={i}|TEMP={temp}C|HUMIDITY=45%|STATUS=OK",
                f"ID=PWR_02|SEQ={i}|VOLTAGE={voltage}V|LOAD=4.2A|STATUS=NORMAL",
                f"ID=SEC_03|SEQ={i}|MOTION={motion}|DOOR=CLOSED|STATUS=ARMED",
                f"ID=FLOW_04|SEQ={i}|RATE=12.5LPM|PRESSURE=45PSI|STATUS=OK",
                f"ID=SYS_05|SEQ={i}|CPU_UTIL={cpu}%|RAM_FREE=2048MB|STATUS=OK"
            ]
            for port in PORTS:
                message = messages[PORTS.index(port)]
                data = message.encode("utf-8")  
                sock.sendto(data, (HOST, port))
                print(f"Sent to {port}: {message}")

            i += 1
            time.sleep(0.01)

except KeyboardInterrupt:
    print("\nStopping client. Goodbye!")