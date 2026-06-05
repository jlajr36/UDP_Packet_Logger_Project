from scapy.all import Ether, sendp, conf
import time

iface = conf.iface

print("Sending packets... press CTRL+C to stop")

try:
    while True:
        pkt = Ether()/b"SCAPY_DETECT_TEST"
        sendp(pkt, iface=iface, verbose=False)
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Stopped.")