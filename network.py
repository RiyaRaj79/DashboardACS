import pandas as pd
import numpy as np
import random
import time
import hashlib

def generate_network_status(df: pd.DataFrame, ip_col: str) -> pd.DataFrame:
    """
    Simulates ICMP Ping and SNMP polling for assets that have an IP address.
    Returns a dataframe with added network metrics.
    """
    if df.empty or ip_col not in df.columns:
        return pd.DataFrame()

    # Filter to assets that have an IP
    net_df = df[df[ip_col].notna()].copy()
    if net_df.empty:
        return net_df

    status_list = []
    latency_list = []
    cpu_list = []
    uptime_list = []
    bandwidth_list = []

    for idx, row in net_df.iterrows():
        ip = row[ip_col]
        # Use hashlib to make it deterministic but pseudorandom, 
        # add a small time component so it fluctuates slightly every minute
        t = int(time.time() / 60)
        seed = int(hashlib.md5(f"{ip}{t}".encode()).hexdigest(), 16)
        
        # 92% chance of being UP
        is_up = (seed % 100) < 92
        
        if is_up:
            status_list.append("🟢 UP")
            latency_list.append(random.randint(2, 45))
            cpu_list.append(random.randint(5, 85))
            uptime_list.append(f"{random.randint(10, 300)} days")
            bandwidth_list.append(f"{random.randint(10, 800)} Mbps")
        else:
            status_list.append("🔴 DOWN")
            latency_list.append(None)
            cpu_list.append(None)
            uptime_list.append("Offline")
            bandwidth_list.append(None)

    net_df["Status (ICMP)"] = status_list
    net_df["Latency (ms)"] = latency_list
    net_df["CPU Load (%)"] = cpu_list
    net_df["Uptime (SNMP)"] = uptime_list
    net_df["Bandwidth (SNMP)"] = bandwidth_list

    return net_df
