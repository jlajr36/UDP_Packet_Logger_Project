from scapy.all import rdpcap, IP, UDP, Raw, Ether, sendp, conf
import time
import os
import env

os.chdir(os.path.dirname(os.path.abspath(__file__)))

packets = rdpcap(env.f_pcapng)

iface = conf.iface

# ===== BUILD GLOBAL TIMELINE =====
all_pkts = []

for p in packets:
    if IP in p and UDP in p:
        if p[IP].src in env.selected_ips:
            all_pkts.append(p)

# sort by original capture time
all_pkts.sort(key=lambda p: float(p.time))

print(f"Replaying {len(all_pkts)} packets globally...")

# ===== REPLAY =====
start_time = float(all_pkts[0].time)

for i, p in enumerate(all_pkts):
    if i == 0:
        prev_time = start_time
    else:
        prev_time = float(all_pkts[i - 1].time)

    current_time = float(p.time)
    delta = current_time - prev_time

    time.sleep(max(0, delta))

    payload = bytes(p[UDP].payload)

    pkt = Ether() / IP(src=p[IP].src, dst=p[IP].dst) / UDP(
        sport=p[UDP].sport,
        dport=p[UDP].dport
    ) / Raw(payload)

    sendp(pkt, iface=iface, verbose=False)