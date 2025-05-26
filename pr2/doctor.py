import PcapReader, pyshark
import argparse
import matplotlib.pyplot as plt
from collections import deque
import pandas as pd
import numpy as np
import time, sys
import json

DBG_MODE = False

"""
Performance monitoring and analysis subroutine
"""
def get_text_from_metrics(performance_analysis_data: dict, visualization_data: dict, total_analysis_data: dict, start_time: float) -> str:
    text = []
    text.append(f"\nProcessed {performance_analysis_data['total_windows']} windows.")
    text.append(f"\n\n{'-'*60}")

    text.append(f"\n\nAverage throughput: {performance_analysis_data['throughput'] / performance_analysis_data['total_windows']:.2f} Mbps")
    text.append(f"\nAverage data rate: {performance_analysis_data['data_rate'] / performance_analysis_data['total_windows']:.2f} Mbps")
    text.append(f"\nAverage frame loss: {performance_analysis_data['frame_loss'] / performance_analysis_data['total_windows']:.2f}")
    text.append(f"\nAverage RSSI: {sum(visualization_data['rssi_values']) / len(visualization_data['rssi_values']):.2f} dBm")
    text.append(f"\nAverage PHY gap: {sum(visualization_data['phy_gap_values']) / len(visualization_data['phy_gap_values']):.2f} us")
    text.append(f"\nAverage channel utilization: {performance_analysis_data['channel_util'] / performance_analysis_data['total_windows']:.2f}")
    text.append(f"\n\n{'-'*60}")
    
    text.append(f"\nMax throughput: {visualization_data['max_throughput']:.2f} Mbps")
    text.append(f"\nMin throughput: {visualization_data['min_throughput']:.2f} Mbps")
    text.append(f"\nMean throughput: {visualization_data['mean_throughput']:.2f} Mbps")
    text.append(f"\nMedian throughput: {visualization_data['median_throughput']:.2f} Mbps")
    text.append(f"\n75th Percentile throughput: {visualization_data['75th_percentile_throughput']:.2f} Mbps")
    text.append(f"\n95th Percentile throughput: {visualization_data['95th_percentile_throughput']:.2f} Mbps")
    text.append(f"\n\n{'-'*60}")

    text.append(f"\n\nAggregate iPerf throughput (sum_received): {total_analysis_data['agg_iperf_throughput']:.2f} Mbps")
    
    overall_theoretical_throughput = total_analysis_data['total_improved_throughput'] / total_analysis_data['total_improved_throughput_time'] if total_analysis_data['total_improved_throughput_time'] > 0 else 0
    text.append(f"\nOverall theoretical throughput (Wi-Fi Doctor, 30s avg): {overall_theoretical_throughput:.2f} Mbps")

        
    text.append(f"\n\n{'-'*60}")

    text.append(f"\n\nProcessing runtime {(time.time() - start_time):.3f} seconds.")
    return ''.join(text)

## Project 2 -- function to take iperf json
def parse_iperf_json(iperf_json_path):
    with open(iperf_json_path, "r") as f:
        iperf_data = json.load(f)
    intervals = iperf_data["intervals"]
    timeseries = []
    for idx, interval in enumerate(intervals):
        # Use the 'sum' field for total throughput in this interval
        start_time = interval["sum"]["start"]
        throughput_mbps = interval["sum"]["bits_per_second"] / 1e6  # Convert to Mbps
        timeseries.append({"time": int(start_time), "throughput": throughput_mbps})
    # Also get the aggregate throughput from sum_received
    agg_throughput = iperf_data["end"]["sum_received"]["bits_per_second"] / 1e6  # Mbps
    return timeseries, agg_throughput

## end project 2

def process_packets(reader, i, start_time, src_address=None, dst_address=None, iperf_json_path="iperflogs", my_speedtest_path="speedtestlogs"):
    performance_analysis_data = {
        # Total values
        'total_windows': 0, 'data_rate': 0, 'throughput': 0, 'frame_loss': 0, 'channel_util': 0,
    }

    total_analysis_data = {
        'agg_iperf_throughput': 0, 'total_improved_throughput': 0, 'total_improved_throughput_time': 0,
    }

    visualization_data = {
        'improved_throughput_times': [],
        'improved_throughput_values': [],
        'data_rate_values': [],
        'frame_loss_values': [],
        'rssi_values': [],
        'phy_gap_values': [],
        'iperf_throughput_times': [],
        'iperf_throughput_values': [],
        'max_throughput': 0,
        'min_throughput': float('inf'),
        'mean_throughput': 0,
        'median_throughput': 0,
        '75th_percentile_throughput': 0,
        '95th_percentile_throughput': 0,
    }

    # Try to load iperf throughput from JSON file (every 2 seconds)
    iperf_json_data = []
    iperf_json_data, total_analysis_data['agg_iperf_throughput'] = parse_iperf_json("iperflogs")

    # --- Process all packets and bin into 2-second windows for 30 seconds ---
    window_size = 2
    total_duration = 30
    num_windows = total_duration // window_size
    # Prepare bins for each window
    window_bins = [[] for _ in range(num_windows)]
    window_start_time = None

    processed_packets = 0
    while True:
        packet = reader.read_next_packet()
        if packet is None:
            break
        info = reader.get_80211_info(packet)

        pkt_time = info.get('timestamp')
        if window_start_time is None and pkt_time is not None:
            window_start_time = pkt_time

        # Bin the packet into the correct window
        if pkt_time is not None and window_start_time is not None:
            rel_time = pkt_time - window_start_time
            window_idx = int(rel_time // window_size)
            if 0 <= window_idx < num_windows:
                if (src_address and info['ta'] != src_address) or (dst_address and info['ra'] != dst_address):
                    pass # Not the requested source/destination address
                else:
                    window_bins[window_idx].append(info)
                    processed_packets += 1
                    print(f"\rProcessed {processed_packets} packets...", end='\r', flush=True)
            # Ignore packets outside the 30s window

        if i > 0 and processed_packets >= i:
            break

    # --- Calculate improved throughput for each window ---
    for win_idx in range(num_windows):
        window = window_bins[win_idx]
        window_packets = len(window)
        window_data_rate_sum = 0
        window_retry_packets = 0
        window_phy_gap_sum = 0
        window_rssi_sum = 0
        busy_time = 0
        total_time = window_size
        for info in window:
            data_rate = float(info['data_rate']) if info['data_rate'] else 0
            pkt_len = info.get('length', 1500)
            window_data_rate_sum += data_rate
            window_rssi_sum += int(info['signal_dbm']) if info['signal_dbm'] else 0
            window_phy_gap_sum += info['phy_gap'] if info['phy_gap'] else 0
            window_retry_packets += int(info['fc_retry']) if info['fc_retry'] else 0
            # Busy time calculation
            busy_time += (pkt_len * 8) / (data_rate * 1e6) if data_rate > 0 else 0
        avg_data_rate_window = window_data_rate_sum / window_packets if window_packets > 0 else 0
        frame_loss_window = window_retry_packets / window_packets if window_packets > 0 else 0
        avg_rssi_window = window_rssi_sum / window_packets if window_packets > 0 else 0
        avg_phy_gap_window = window_phy_gap_sum / window_packets if window_packets > 0 else 0
        channel_utilization = (busy_time / total_time) if total_time > 0 else 0
        improved_throughput = avg_data_rate_window * (1 - frame_loss_window) * channel_utilization if window_packets > 0 else 0

        # Store the results for visualization
        visualization_data['improved_throughput_times'].append(win_idx * window_size)
        visualization_data['improved_throughput_values'].append(improved_throughput)
        visualization_data['data_rate_values'].append(avg_data_rate_window)
        visualization_data['frame_loss_values'].append(frame_loss_window)
        visualization_data['rssi_values'].append(avg_rssi_window)
        visualization_data['phy_gap_values'].append(avg_phy_gap_window)

        # Update min/max/mean/median/percentiles
        visualization_data['max_throughput'] = max(visualization_data['max_throughput'], improved_throughput)
        visualization_data['min_throughput'] = min(visualization_data['min_throughput'], improved_throughput)
        visualization_data['mean_throughput'] = np.mean(visualization_data['improved_throughput_values'])
        visualization_data['median_throughput'] = np.median(visualization_data['improved_throughput_values'])
        visualization_data['75th_percentile_throughput'] = np.percentile(visualization_data['improved_throughput_values'], 75)
        visualization_data['95th_percentile_throughput'] = np.percentile(visualization_data['improved_throughput_values'], 95)

        # Update total analysis data
        total_analysis_data['total_improved_throughput'] += improved_throughput*window_size
        total_analysis_data['total_improved_throughput_time'] += window_size

        performance_analysis_data['total_windows'] += 1
        performance_analysis_data['data_rate'] += avg_data_rate_window
        performance_analysis_data['throughput'] += improved_throughput
        performance_analysis_data['frame_loss'] += frame_loss_window
        performance_analysis_data['channel_util'] += channel_utilization
    
     # --- Prepare iperf throughput for plotting ---
    for win_idx in range(num_windows):
        if win_idx < len(iperf_json_data):
            entry = iperf_json_data[win_idx]
            visualization_data['iperf_throughput_times'].append(entry.get("time", win_idx * window_size))
            visualization_data['iperf_throughput_values'].append(entry.get("throughput", 0))
        else:
            visualization_data['iperf_throughput_times'].append(win_idx * window_size)
            visualization_data['iperf_throughput_values'].append(0)
       
    dbg_text = get_text_from_metrics(performance_analysis_data, visualization_data, total_analysis_data, start_time)
    if DBG_MODE:
        print(dbg_text)
    
    # --- Plot the results ---
    plt.figure(1, figsize=(12, 8))
    plt.subplot(1, 2, 1)
    plt.plot(visualization_data['improved_throughput_times'], visualization_data['improved_throughput_values'], marker='o', label="Improved (Wi-Fi Doctor)")
    plt.plot(visualization_data['improved_throughput_times'], visualization_data['data_rate_values'], label="Data Rate", linestyle='--')
    plt.plot(visualization_data['improved_throughput_times'], visualization_data['frame_loss_values'], label="Frame Loss", linestyle='--')
    plt.plot(visualization_data['improved_throughput_times'], visualization_data['rssi_values'], label="RSSI", linestyle='--')
    plt.plot(visualization_data['improved_throughput_times'], visualization_data['phy_gap_values'], label="PHY Gap", linestyle='--')

    plt.axhline(y=visualization_data['max_throughput'], color='r', linestyle='--', label="Max Throughput")
    plt.axhline(y=visualization_data['min_throughput'], color='g', linestyle='--', label="Min Throughput")
    plt.axhline(y=visualization_data['mean_throughput'], color='b', linestyle='--', label="Mean Throughput")
    plt.axhline(y=visualization_data['median_throughput'], color='c', linestyle='--', label="Median Throughput")
    plt.axhline(y=visualization_data['75th_percentile_throughput'], color='m', linestyle='--', label="75th Percentile Throughput")
    plt.axhline(y=visualization_data['95th_percentile_throughput'], color='y', linestyle='--', label="95th Percentile Throughput")
    
    # Plot iPerf throughput
    plt.plot(visualization_data['iperf_throughput_times'], visualization_data['iperf_throughput_values'], marker='s', label="iPerf")
    
    plt.xlabel("Time (s)")
    plt.ylabel("Throughput (Mbps)")
    plt.title("Throughput Every 2 Seconds")
    plt.grid()
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.text(0.01, 0.5, dbg_text, 
                        fontsize=10, ha='left', va='center', family=['monospace'], transform=plt.gca().transAxes)
    plt.axis('off')
            
    plt.tight_layout()
    plt.show()  # Keep the figure open

if __name__ == "__main__":
    # Get the command line arguments.
    parser = argparse.ArgumentParser(description="Process a PCAP file to extract WiFi information.")
    parser.add_argument("-s", "--src", type=str, default="--", help="Source address (default: --).")
    parser.add_argument("-d", "--dst", type=str, default="--", help="Destination address (default: --).")
    parser.add_argument("-l", "--limit", type=int, default=-1, help="Limit the number of packets to process (default: -1 for no limit).")
    parser.add_argument("-f", "--filename", type=str, required=True, help="Path to the PCAP file.")
    parser.add_argument("-if", "--iperf", type=str, required=True, help="Path to iperf log file.")
    parser.add_argument("-mf", "--mfile", type=str, required=True, help="Path to custom log file.")
    parser.add_argument("-dbg", action="store_true", help="Enable debug mode.")
    
    # Parse the arguments.
    args = parser.parse_args()
    filename = args.filename
    packet_limit = args.limit
    src_address = args.src
    dst_address = args.dst
    DBG_MODE = args.dbg
    iperf_json_path = args.iperf
    my_speedtest_path = args.mfile
    
    if DBG_MODE: # Information for debugging
        print(f"Debug mode enabled.")
        print(f"Processing file: {filename.split('/')[-1]}{f' with packet limit: {packet_limit}' if packet_limit > -1 else ''}")
        if src_address != "--" and dst_address != "--":
            print(f"Throughput between {src_address} and {dst_address}")
    
    # Start timer.
    start_time = time.time() 

    # Open reader object.
    reader = PcapReader.PcapReader(filename)
    
    # Process packets and display results.
    process_packets(reader, packet_limit, start_time, src_address, dst_address, iperf_json_path, my_speedtest_path)
    reader.close()
    
    sys.exit(0)