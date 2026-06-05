import socket
import time
import random

HOST = "192.168.1.222"
PORTS = [9995, 9996, 9997, 9998, 9999]

print("Starting UDP client loop with dynamic IoT metrics. Press Ctrl+C to stop.")

try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        while True: # Runs continuously 
            epoch_ts = round(time.time(), 2) 
            now = time.localtime()
            julian_day = now.tm_yday + round((now.tm_hour / 24.0) + (now.tm_min / 1440.0) + (now.tm_sec / 86400.0), 5)

            temp = round(22.0 + random.uniform(-1.5, 1.5), 1)
            voltage = round(120.0 + random.uniform(-2.0, 2.0), 1)
            cpu = round(10.0 + random.uniform(0.0, 45.0), 1)
            motion = random.choice([0, 0, 0, 0, 1]) # 20% chance of motion
            messages = [
                f"ID=ENV_01|TS={epoch_ts}|JUL={julian_day}|TEMP={temp}C|HUMIDITY=45%|STATUS=OK",
                f"ID=PWR_02|TS={epoch_ts}|JUL={julian_day}|VOLTAGE={voltage}V|LOAD=4.2A|STATUS=NORMAL",
                f"ID=SEC_03|TS={epoch_ts}|JUL={julian_day}|MOTION={motion}|DOOR=CLOSED|STATUS=ARMED",
                f"ID=FLOW_04|TS={epoch_ts}|JUL={julian_day}|RATE=12.5LPM|PRESSURE=45PSI|STATUS=OK",
                f"ID=SYS_05|TS={epoch_ts}|JUL={julian_day}|CPU_UTIL={cpu}%|RAM_FREE=2048MB|STATUS=OK"
            ]
            for port, message in zip(PORTS, messages):
                data = message.encode("utf-8")  
                sock.sendto(data, (HOST, port))
                print(f"Sent to {port}: {message}")

            time.sleep(0.5)

except KeyboardInterrupt:
    print("\nStopping client. Goodbye!")