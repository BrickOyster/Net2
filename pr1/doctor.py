import PcapReader, pyshark
import argparse
import matplotlib.pyplot as plt
from collections import deque
import pandas as pd
import numpy as np
import time, sys

DBG_MODE = False

"""
Performance monitoring and analysis subroutine
"""
def get_text_from_metrics(density_metrics: list, performance_monitor_data: dict, performance_analysis_data: dict, start_time: float, processed_packets: int) -> str:
    text = []
    text.append(f"\nProcessing {processed_packets} packets")
    text.append(f"\n\n{'-'*80}")

    text.append(f"\n\nDensity")
    ## 1.1 ##
    for metrics in density_metrics:
        text.append(f"\n|Channel {metrics['frequency']} MHz")
        if metrics['density']:
            text.append(f"\n|    Density: {metrics['density']:.2f}")
        else:
            text.append(f"\n|    Density: No data")
        if metrics['classification']:
            text.append(f"\n|    Classification: {metrics['classification']}")
        else:
            text.append(f"\n|    Classification: No data")
    if len(density_metrics) == 0:
        text.append(f"\n|    Density: 0.00")
        text.append(f"\n|    Classification: Not dense channel")

    text.append(f"\n\n{'-'*80}")

    text.append(f"\n\nPerformance Monitor on {performance_monitor_data['total_packets']} packets:")
    if performance_monitor_data['total_packets'] > 0:
        avg_data_rate_ts = (performance_monitor_data['sum_data_rate'] / performance_monitor_data['total_packets'])
        loss_rate = (performance_monitor_data['retry_packets'] / performance_monitor_data['total_packets'])
        
        text.append(f"\n|    Avg data rate: {avg_data_rate_ts:.2f} Mbps")
        text.append(f"\n|    Max data rate: {performance_monitor_data['max_data_rate']:.2f} Mbps")
        text.append(f"\n|    Min data rate: {performance_monitor_data['min_data_rate']:.2f} Mbps")
        text.append(f"\n|    Loss rate: {(loss_rate * 100):.2f} %")
        text.append(f"\n|    Throughput: {(avg_data_rate_ts * (1-loss_rate)):.2f} Mbps")
    else:
        text.append(f"\n|    Avg data rate: 0.00 Mbps")
        text.append(f"\n|    Max data rate: 0.00 Mbps")
        text.append(f"\n|    Min data rate: 0.00 Mbps")
        text.append(f"\n|    Loss rate: -- %")
        text.append(f"\n|    Throughput: 0.00 Mbps")

    text.append(f"\n\n{'-'*80}")

    text.append(f"\n\nPerformance Analysis on {performance_analysis_data['total']} packets:")
    if performance_analysis_data['total'] > 0:
        # Overall performance of network (phy, bandwidth, short GI)
        net_conf = (performance_analysis_data['phy'] + performance_analysis_data['bandwidth'] + performance_analysis_data['sgi'])/(3*performance_analysis_data['total'])
        if net_conf > 0.9:
            text.append(f"\n|Network Configuration: Pristine")
        elif net_conf > 0.6:    
            text.append(f"\n|Network Configuration: Good")
        elif net_conf > 0.3:
            text.append(f"\n|Network Configuration: Fair")
        else:
            text.append(f"\n|Network Configuration: Bad")
        
        # Individual performance of network (phy, bandwidth, short GI)
        text.append(f"\n|    Good PHY: {(100*performance_analysis_data['phy']/performance_analysis_data['total']):.2f} %")
        text.append(f"\n|    Good Bandwidth: {(100*performance_analysis_data['bandwidth']/performance_analysis_data['total']):.2f} %")
        text.append(f"\n|    Good Short GI: {(100*performance_analysis_data['sgi']/performance_analysis_data['total']):.2f} %")
        
        # Overall performance of channel (mcs, signal strength)
        ch_conf = ((performance_analysis_data['ssi'] + performance_analysis_data['mcs'])/(2*performance_analysis_data['total']))
        if ch_conf > 0.9:
            text.append(f"\n|Channel Configuration: Pristine")
        elif ch_conf > 0.6:
            text.append(f"\n|Channel Configuration: Good")
        elif ch_conf > 0.3:
            text.append(f"\n|Channel Configuration: Fair")
        else:
            text.append(f"\n|Channel Configuration: Bad")
        # Individual performance of channel (mcs, signal strength)
        text.append(f"\n|    Good MCS: {(100*performance_analysis_data['mcs']/performance_analysis_data['total']):.2f} %")
        text.append(f"\n|    Good SSI: {(100*performance_analysis_data['ssi']/performance_analysis_data['total']):.2f} %")

        # Overall interference of network (phy_gap)
        phy_gap = (performance_analysis_data['phy_gap'] / performance_analysis_data['total'])
        if phy_gap < 1:
            text.append(f"\n|PHY Gap: Pristine")
        elif phy_gap < 2:
            text.append(f"\n|PHY Gap: Good")
        elif phy_gap < 5:
            text.append(f"\n|PHY Gap: Fair")
        else:
            text.append(f"\n|PHY Gap: Bad")
        # Individual performance of network (phy_gap)
        text.append(f"\n|    PHY Gap: {(performance_analysis_data['phy_gap']/performance_analysis_data['total']):.2f}")

        # Overall performance of network (discarded packets)    
        cntrl_packets = (performance_analysis_data['discarted']/(performance_analysis_data['discarted']+performance_analysis_data['total']))
        if cntrl_packets > 0.9:
            text.append(f"\n\n{performance_analysis_data['discarted']} control packets heavily impact performance")
        elif cntrl_packets > 0.6:
            text.append(f"\n\n{performance_analysis_data['discarted']} control packets moderately impact performance")
        elif cntrl_packets > 0.2:
            text.append(f"\n\n{performance_analysis_data['discarted']} control packets minimally impact performance")
        else:
            text.append(f"\n\n{performance_analysis_data['discarted']} control packets have no impact on performance")
    else:    
            text.append(f"\n|Network Configuration: No data")
            text.append(f"\n|    Good PHY: -- %")
            text.append(f"\n|    Good Bandwidth: -- %")
            text.append(f"\n|    Good Short GI: -- %")    
            text.append(f"\n|Channel Configuration: No data")
            text.append(f"\n|    Good MCS: -- %")
            text.append(f"\n|    Good SSI: -- %")
            text.append(f"\n|PHY Gap: No data")
            text.append(f"\n|    PHY Gap: --")
            text.append(f"\n\nControl Packets: No data")
        
    text.append(f"\n\n{'-'*80}")

    text.append(f"\n\nProcessing runtime {(time.time() - start_time):.3f} seconds.")
    return ''.join(text)

def process_packets(reader, i, start_time, src_address=None, dst_address=None, entries_per_step=5):
    # Initialize variables.
    bandwidth_dict = {0: 20, 1: 40, 2: 80, 2: 160}
    ## 1.1 ##
    data = []
    density_metrics = []

    ## 1.2 Wi-Fi Network Performance Metrics ##
    get_ts = entries_per_step

    # Found on various forums and websites
    # Max threasholds of bad performance ( > thereshold = good performance)
    BAD_PHY = 5
    BAD_MCS = 6
    BAD_BANDWIDTH = 0
    BAD_SIGNAL = -80

    performance_monitor_data = {
        # Total values
        'total_packets': 0, 'retry_packets': 0, 'sum_data_rate': 0, 'max_data_rate': 0, 'min_data_rate': 1000,
        # Last entries
        'data_rate_le': deque(maxlen=30), # Limit the number of entries to 30
    }
    performance_analysis_data = {
        # Total values
        'total': 0, 'discarted': 0, 'phy': 0, 'bandwidth': 0, 'sgi': 0, 'mcs': 0, 'ssi': 0, 'phy_gap': 0
    }

    visualization_data = {
        'data_rate': [],
        'phy': [],
        'bandwidth': [],
        'sgi': [],
        'ssi': [],
        'phy_gap': [],
    }
    
    processed_packets = 0
    plt.figure(1, figsize=(18, 9))
    while processed_packets != i:
        if DBG_MODE:
            print(f"\rProcessing packets...\tTotal packets: {processed_packets}", end="")

        # Read the next packet.
        packet = reader.read_next_packet()
        if packet is None or i == 0:
            break
        info = reader.get_80211_info(packet)
        processed_packets += 1
        
        ## 1.1 Wi-Fi Network Density ##
        if info.get('bssid') and info.get('signal_dbm') and info.get('channel'):
            bssid = info['bssid']
            signal_strength = abs(int(info['signal_dbm']))  # abs ensures positive RSSI
            channel = int(info['channel'])

            # Check if BSSID is already in the list
            existing_entry = next((entry for entry in data if entry['BSSID'] == bssid), None)
            if existing_entry:
                # Update Signal Strength if the new value is stronger (higher)
                existing_entry['signal_strength'] = max(existing_entry['signal_strength'], signal_strength)
            else:
                # Add new entry if BSSID is not in the list
                data.append({
                    'BSSID': bssid,
                    'signal_strength': signal_strength,
                    'Channel': channel
                })

            # Convert the data to a DataFrame
            df = pd.DataFrame(data)

            # Group data by channel to calculate metrics
            grouped = df.groupby('Channel').agg(
                total_signal_strength=('signal_strength', 'sum')  # Sum signal strengths of unique BSSIDs
            )

            # Compute density as the sum of signal strengths of unique BSSIDs divided by channel bandwidth
            bandwidth = info.get('bandwidth')

            grouped['density'] = grouped['total_signal_strength'] / (bandwidth_dict[int(info['bandwidth'])] if info['bandwidth'] else 22)

            # Add frequency information to the result
            grouped['frequency'] = info.get('frequency', 0)  # Get the frequency of the channel

            # Convert to dictionary
            density_per_channel = grouped[['density', 'frequency']].to_dict(orient='index')

            metrics_per_channel = {
                'frequency': 0,
                'density': 0,
                'classification': ""
            }
            
            density_metrics = []
            for channel, metrics in density_per_channel.items():
                metrics_per_channel['frequency'] = metrics['frequency']
                metrics_per_channel['density'] = metrics['density']
                if metrics_per_channel['density'] < 8:
                    metrics_per_channel['classification'] = "Not dense channel"
                elif metrics_per_channel['density'] < 16:
                    metrics_per_channel['classification'] = "Moderately dense"
                elif metrics_per_channel['density'] < 24:
                    metrics_per_channel['classification'] = "Dense"
                else:
                    metrics_per_channel['classification'] = "Very dense"

                density_metrics.append(metrics_per_channel)
        ## 1.1 End ##

        ## 1.2 Wi-Fi Network Performance ## 
        data_rate = float(info.get('data_rate')) if info['data_rate'] else 0
        phy = int(info.get('phy')) if info['phy'] else 0
        bandwidth = int(info.get('bandwidth')) if info['bandwidth'] else 0
        short_gi = int(info.get('short_gi')) if info['short_gi'] else 0
        signal_dbm = int(info.get('signal_dbm')) if info['signal_dbm'] else 0
        phy_gap = info.get('phy_gap') if info['phy_gap'] else 0

        if (src_address and info['ta'] != src_address) or (dst_address and info['ra'] != dst_address):
            pass # Not the requested source address
        else:
            if info['mcs_index']: # Means it is a data packet (Others have minimal impact)
                # Monitor
                performance_monitor_data['retry_packets'] += int(info['fc_retry'])
                performance_monitor_data['total_packets'] += 1
                performance_monitor_data['sum_data_rate'] += data_rate
                performance_monitor_data['max_data_rate'] = max(performance_monitor_data['max_data_rate'], data_rate)
                performance_monitor_data['min_data_rate'] = min(performance_monitor_data['min_data_rate'], data_rate)
                # Add to the list of last entries
                performance_monitor_data['data_rate_le'].append(data_rate)

                # Analysis
                performance_analysis_data['total'] += 1
                # Add one to each metric the packet is over the threshold of "good metric"
                if info['phy']:
                    performance_analysis_data['phy'] += 1 if phy > BAD_PHY else 0
                if info['bandwidth']:
                    performance_analysis_data['bandwidth'] += 1 if bandwidth > BAD_BANDWIDTH else 0
                if info['short_gi']:
                    performance_analysis_data['sgi'] += 1 if short_gi else 0
                if info['mcs_index']:
                    performance_analysis_data['mcs'] += 1 if int(info['mcs_index']) > BAD_MCS else 0
                if info['signal_dbm']: # Some times not reported
                    performance_analysis_data['ssi'] += 1 if signal_dbm > BAD_SIGNAL else 0
                if info['phy_gap']:
                    performance_analysis_data['phy_gap'] += phy_gap          
            else:
                performance_analysis_data['discarted'] += 1
        ## 1.2 End ##

        ## Visualization ##
        get_ts -= 1
        if get_ts == 0 or processed_packets == 1:
            visualization_data['data_rate'].append((np.mean(performance_monitor_data['data_rate_le'])*(1-performance_monitor_data['retry_packets']/performance_monitor_data['total_packets'])) if len(performance_monitor_data['data_rate_le']) > 0 else 0)
            visualization_data['phy_gap'].append(phy_gap)
            visualization_data['phy'].append(phy)
            visualization_data['bandwidth'].append(bandwidth)
            visualization_data['sgi'].append(short_gi)
            visualization_data['ssi'].append(signal_dbm)
            # Plotting
            plt.clf()
            plt.subplot(1,2,1)
            plt.plot(visualization_data['data_rate'], label="Throughput (Mbps)")
            plt.plot(visualization_data['phy_gap'], label="PHY Gap")
            plt.plot(visualization_data['phy'], label="PHY")
            plt.plot(visualization_data['bandwidth'], label="Bandwidth")
            plt.plot(visualization_data['sgi'], label="Short GI (0/1)")
            plt.plot(visualization_data['ssi'], label="Signal Strength (dBm)")
            plt.xlabel("Time Steps")
            plt.ylabel("Value")
            plt.title("Dynamic Network Performance")
            plt.legend()
            plt.grid()

            plt.subplot(1,2,2)
            plt.text(0.01, 0.5, get_text_from_metrics(density_metrics, performance_monitor_data, performance_analysis_data, start_time, processed_packets), 
                        fontsize=10, ha='left', va='center', family=['monospace'], transform=plt.gca().transAxes)
            plt.axis('off')
            
            plt.pause(0.01)  # Pause to update the plot dynamically
            get_ts = entries_per_step
        
    if DBG_MODE:
    ## 1.1 Results ##
        
    ## 1.2 Results ##
        print(get_text_from_metrics(density_metrics, performance_monitor_data, performance_analysis_data, start_time, processed_packets))
    
    # Keep the last plot open until the user closes it
    plt.show()  # Keep the figure open

if __name__ == "__main__":
    # Get the command line arguments.
    parser = argparse.ArgumentParser(description="Process a PCAP file to extract WiFi information.")
    parser.add_argument("-s", "--src", type=str, default="--", help="Source address (default: --).")
    parser.add_argument("-d", "--dst", type=str, default="--", help="Destination address (default: --).")
    parser.add_argument("-l", "--limit", type=int, default=-1, help="Limit the number of packets to process (default: -1 for no limit).")
    parser.add_argument("-f", "--filename", type=str, required=True, help="Path to the PCAP file.")
    parser.add_argument("-dbg", action="store_true", help="Enable debug mode.")
    
    # Parse the arguments.
    args = parser.parse_args()
    filename = args.filename
    packet_limit = args.limit
    src_address = args.src
    dst_address = args.dst
    DBG_MODE = args.dbg
    
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
    process_packets(reader, packet_limit, start_time, src_address, dst_address)
    reader.close()
    
    sys.exit(0)