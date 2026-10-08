import os
import random
import time
import pandas as pd
import numpy as np

def generate_datasets(output_dir="data/raw"):
    os.makedirs(output_dir, exist_ok=True)
    base_time = 1700000000.0  # Reference timestamp

    # 1. Scenario A: Recon -> Brute Force -> Exfiltration
    scenario_a_rows = []
    curr_t = base_time

    # Phase A1: Benign baseline (0 - 30s)
    for _ in range(50):
        curr_t += random.uniform(0.1, 0.6)
        scenario_a_rows.append({
            "timestamp": curr_t,
            "src_ip": random.choice(["192.168.1.10", "192.168.1.11", "192.168.1.12"]),
            "dst_ip": "192.168.1.100",
            "src_port": random.randint(49152, 65535),
            "dst_port": random.choice([80, 443, 22]),
            "protocol": "TCP",
            "duration": random.uniform(0.01, 1.5),
            "tot_pkts": random.randint(5, 30),
            "tot_bytes": random.randint(500, 15000),
            "syn_flag_cnt": 1,
            "rst_flag_cnt": 0,
            "label": "BENIGN"
        })

    # Phase A2: Reconnaissance / PortScan (30s - 60s)
    scanner_ip = "192.168.1.50"
    for port in range(20, 120):
        curr_t += random.uniform(0.1, 0.3)
        scenario_a_rows.append({
            "timestamp": curr_t,
            "src_ip": scanner_ip,
            "dst_ip": "192.168.1.100",
            "src_port": random.randint(49152, 65535),
            "dst_port": port,
            "protocol": "TCP",
            "duration": random.uniform(0.001, 0.05),
            "tot_pkts": random.randint(1, 3),
            "tot_bytes": random.randint(64, 180),
            "syn_flag_cnt": 1,
            "rst_flag_cnt": random.choice([0, 1]),
            "label": "PortScan"
        })

    # Phase A3: Brute Force SSH (60s - 90s)
    for _ in range(80):
        curr_t += random.uniform(0.1, 0.4)
        scenario_a_rows.append({
            "timestamp": curr_t,
            "src_ip": scanner_ip,
            "dst_ip": "192.168.1.100",
            "src_port": random.randint(49152, 65535),
            "dst_port": 22,
            "protocol": "TCP",
            "duration": random.uniform(0.05, 0.3),
            "tot_pkts": random.randint(8, 16),
            "tot_bytes": random.randint(800, 2400),
            "syn_flag_cnt": 1,
            "rst_flag_cnt": random.choice([0, 1]),
            "label": "BruteForce"
        })

    # Phase A4: Data Exfiltration (90s - 120s)
    for _ in range(40):
        curr_t += random.uniform(0.3, 0.8)
        scenario_a_rows.append({
            "timestamp": curr_t,
            "src_ip": "192.168.1.100",
            "dst_ip": "203.0.113.55",  # External C2 / Exfil IP
            "src_port": random.randint(49152, 65535),
            "dst_port": 443,
            "protocol": "TCP",
            "duration": random.uniform(0.5, 4.0),
            "tot_pkts": random.randint(200, 1000),
            "tot_bytes": random.randint(200000, 1500000),
            "syn_flag_cnt": 1,
            "rst_flag_cnt": 0,
            "label": "DataExfiltration"
        })

    df_a = pd.DataFrame(scenario_a_rows)
    df_a.to_csv(os.path.join(output_dir, "scenario_a_recon_bruteforce_exfil.csv"), index=False)
    print(f"Generated Scenario A: {len(df_a)} rows")

    # 2. Scenario B: PortScan -> DoS -> Command Execution
    scenario_b_rows = []
    curr_t = base_time

    # Phase B1: Benign traffic (0 - 30s)
    for _ in range(50):
        curr_t += random.uniform(0.1, 0.6)
        scenario_b_rows.append({
            "timestamp": curr_t,
            "src_ip": "192.168.1.15",
            "dst_ip": "192.168.1.200",
            "src_port": random.randint(49152, 65535),
            "dst_port": 80,
            "protocol": "TCP",
            "duration": random.uniform(0.01, 1.0),
            "tot_pkts": random.randint(5, 20),
            "tot_bytes": random.randint(400, 8000),
            "syn_flag_cnt": 1,
            "rst_flag_cnt": 0,
            "label": "BENIGN"
        })

    # Phase B2: Intensive DoS Flood (30s - 60s)
    attacker_ip = "192.168.1.99"
    for _ in range(250):
        curr_t += random.uniform(0.01, 0.1)
        scenario_b_rows.append({
            "timestamp": curr_t,
            "src_ip": attacker_ip,
            "dst_ip": "192.168.1.200",
            "src_port": random.randint(1024, 65535),
            "dst_port": 80,
            "protocol": "TCP",
            "duration": random.uniform(0.001, 0.01),
            "tot_pkts": random.randint(50, 200),
            "tot_bytes": random.randint(30000, 150000),
            "syn_flag_cnt": 1,
            "rst_flag_cnt": 0,
            "label": "DoS"
        })

    # Phase B3: Command Execution / Exploitation (60s - 90s)
    for _ in range(40):
        curr_t += random.uniform(0.4, 1.0)
        scenario_b_rows.append({
            "timestamp": curr_t,
            "src_ip": attacker_ip,
            "dst_ip": "192.168.1.200",
            "src_port": random.randint(49152, 65535),
            "dst_port": 4444, # Reverse shell port
            "protocol": "TCP",
            "duration": random.uniform(0.2, 2.0),
            "tot_pkts": random.randint(15, 50),
            "tot_bytes": random.randint(1200, 6000),
            "syn_flag_cnt": 1,
            "rst_flag_cnt": 0,
            "label": "CommandExecution"
        })

    df_b = pd.DataFrame(scenario_b_rows)
    df_b.to_csv(os.path.join(output_dir, "scenario_b_dos_command_exec.csv"), index=False)
    print(f"Generated Scenario B: {len(df_b)} rows")

    # 3. Scenario C: Purely Benign Baseline Traffic
    scenario_c_rows = []
    curr_t = base_time
    for _ in range(200):
        curr_t += random.uniform(0.1, 0.5)
        scenario_c_rows.append({
            "timestamp": curr_t,
            "src_ip": random.choice(["192.168.1.10", "192.168.1.11", "192.168.1.12", "192.168.1.13"]),
            "dst_ip": random.choice(["192.168.1.100", "192.168.1.200", "8.8.8.8"]),
            "src_port": random.randint(49152, 65535),
            "dst_port": random.choice([80, 443, 53]),
            "protocol": random.choice(["TCP", "UDP"]),
            "duration": random.uniform(0.01, 2.0),
            "tot_pkts": random.randint(2, 30),
            "tot_bytes": random.randint(120, 20000),
            "syn_flag_cnt": random.choice([0, 1]),
            "rst_flag_cnt": 0,
            "label": "BENIGN"
        })

    df_c = pd.DataFrame(scenario_c_rows)
    df_c.to_csv(os.path.join(output_dir, "scenario_c_benign.csv"), index=False)
    print(f"Generated Scenario C (Benign): {len(df_c)} rows")

if __name__ == "__main__":
    generate_datasets()
