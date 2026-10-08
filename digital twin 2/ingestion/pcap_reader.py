import os
from typing import List, Dict, Any, Iterator
try:
    from scapy.all import rdpcap, IP, TCP, UDP
    HAS_SCAPY = True
except ImportError:
    HAS_SCAPY = False

class PCAPFlowReader:
    """Reads raw PCAP packet captures and aggregates packets into window flows."""
    def __init__(self, pcap_path: str):
        self.pcap_path = pcap_path
        if not HAS_SCAPY:
            raise ImportError("Scapy package is required for PCAP parsing. Install via `pip install scapy`.")
        if not os.path.exists(pcap_path):
            raise FileNotFoundError(f"PCAP file not found: {pcap_path}")

    def read_all(self) -> List[Dict[str, Any]]:
        packets = rdpcap(self.pcap_path)
        records = []
        for pkt in packets:
            if IP in pkt:
                t = float(pkt.time)
                src_ip = pkt[IP].src
                dst_ip = pkt[IP].dst
                proto_num = pkt[IP].proto
                proto = "TCP" if proto_num == 6 else ("UDP" if proto_num == 17 else "IP")
                
                src_port = 0
                dst_port = 0
                syn_flag = 0
                rst_flag = 0

                if TCP in pkt:
                    src_port = pkt[TCP].sport
                    dst_port = pkt[TCP].dport
                    flags = str(pkt[TCP].flags)
                    if "S" in flags:
                        syn_flag = 1
                    if "R" in flags:
                        rst_flag = 1
                elif UDP in pkt:
                    src_port = pkt[UDP].sport
                    dst_port = pkt[UDP].dport

                length = len(pkt)

                records.append({
                    "timestamp": t,
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "src_port": src_port,
                    "dst_port": dst_port,
                    "protocol": proto,
                    "duration": 0.01,
                    "tot_pkts": 1,
                    "tot_bytes": length,
                    "syn_flag_cnt": syn_flag,
                    "rst_flag_cnt": rst_flag,
                    "label": "BENIGN"
                })
        return records

    def stream_records(self) -> Iterator[Dict[str, Any]]:
        for record in self.read_all():
            yield record
