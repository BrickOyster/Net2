# Wi-Fi Network Performance Monitor and Analyzer

This repository contains tools for analyzing Wi-Fi network performance using PCAP files. The primary components are `PcapReader.py`, which extracts 802.11 packet information, and `doctor.py`, which processes the packets to monitor and analyze network performance.

---

## Features

- **Packet Reading**: Extract detailed 802.11 packet information, including BSSID, transmitter/receiver addresses, data rates, signal strength, and more.
- **Wi-Fi Network Density Analysis**: Compute channel density and classify channels as not dense, moderately dense, dense, or very dense.
- **Performance Monitoring**: Analyze metrics such as data rate, loss rate, throughput, and PHY gap.
- **Network Analysis**: Evaluate network configuration, channel quality, and interference levels.
- **Dynamic Visualization**: Real-time plotting of network performance metrics.
- **Custom Filtering**: Filter packets by source and destination addresses.

---

## Requirements

- Python 3.7+
- Required Python libraries:
    - `pyshark`
    - `matplotlib`
    - `numpy`
    - `pandas`

Install dependencies using pip:

```bash
pip install pyshark matplotlib numpy pandas
```

---

## File Descriptions

### `PcapReader.py`

A utility for reading and extracting information from PCAP files. Key features include:

- **Packet Reading**: Read packets sequentially or as a generator.
- **802.11 Information Extraction**: Extract details like BSSID, data rate, channel, signal strength, and more.
- **Error Handling**: Handles invalid packets and missing fields gracefully.

### `doctor.py`

Processes packets from a PCAP file to monitor and analyze Wi-Fi network performance. Key features include:

- **Wi-Fi Network Density Analysis**:
    - Calculate channel density based on signal strength and bandwidth.
    - Classify channels into density categories.
- **Performance Metrics**:
    - Average, maximum, and minimum data rates.
    - Loss rate and throughput.
    - PHY gap and channel quality.
- **Visualization**: Real-time plots of performance metrics.
- **Custom Filtering**: Analyze packets based on source and destination addresses.

---

## Usage

### Command-Line Interface

Run `doctor.py` with the following arguments:

```bash
python doctor.py -f <path_to_pcap_file> [options]
```

#### Options

- `-f, --filename`: Path to the PCAP file (required).
- `-s, --src`: Source address to filter packets (default: None).
- `-d, --dst`: Destination address to filter packets (default: None).
- `-l, --limit`: Limit the number of packets to process (default: -1 for no limit).
- `-dbg`: Enable debug mode for detailed logs.

#### Example

```bash
python doctor.py -f HowIWiFi_PCAP.pcap -s 2c:f8:9b:dd:06:a0 -d 00:20:a6:fc:b0:36 -l 1000 -dbg
```

---

## Output

- **Console Output**: Summary of channel density classification, performance metrics, including data rate, loss rate, throughput and network/channel configuration.
- **Plots**: Real-time visualization of metrics such as data rate, PHY gap, signal strength.

---

## How It Works

1. **Packet Reading**: `PcapReader` reads packets from the PCAP file and extracts 802.11 information.
2. **Wi-Fi Network Density Analysis**: Computes channel density and classifies channels based on signal strength and bandwidth.
3. **Performance Monitoring**: Metrics like data rate, loss rate, and PHY gap are calculated.
4. **Network Analysis**: Evaluates network and channel configurations based on thresholds.
5. **Visualization**: Metrics are dynamically plotted for real-time monitoring.

---

## Limitations

- Requires PCAP files with 802.11 packets.
- Performance depends on the size of the PCAP file and the number of packets processed.

---

## License

This project is licensed under no License.

---

## Acknowledgments

- [PyShark](https://github.com/KimiNewt/pyshark) for packet parsing.
- [Matplotlib](https://matplotlib.org/) for visualization.
- [Pandas](https://pandas.pydata.org/) for data manipulation.