# Speedtest

A C-based client-server application to measure downlink throughput between a client and server, with improved logging and live traffic analysis.

## Features

- **Server**: Listens for client connections, receives data, and logs throughput in JSON format.
- **Client**: Connects to the server and sends data at high speed for a configurable duration.
- **Logging**: Throughput and statistics are logged for further analysis.
Integration: Results can be analyzed with the Python doctor.py script for visualization and comparison with PCAP-based metrics.
Building

---

## Usage

#### Server

 - `-p`: Port to listen on (default: 5001)
 - `-b`: Buffer size in bytes (default: 131072)
 - `-i`: Throughput calculation interval in seconds (default: 2)
 - `-l`: Connection limit (default: -1, unlimited)
 - `-f`: Log file for throughput data (default: throughput_log.json)

```bash
./server [-p port] [-b buffer_size] [-i interval] [-l connection_limit] [-f log_file]
```

#### Client

```bash
./client [-a server_ip] [-p port] [-b buffer_size] [-i interval] [-d duration]
```

 - `-a`: Server IP address (default: 0.0.0.0)
 - `-p`: Server port (default: 5001)
 - `-b`: Buffer size in bytes (default: 131072)
 - `-i`: Print interval in seconds (default: 2)
 - `-d`: Test duration in seconds (default: 30)

Example

```bash
# Start the server: 
./server -p 5001 -b 131072 -i 2 -f throughput_log.json
# Run the client:
./client -a 192.168.1.10 -p 5001 -b 131072 -i 2 -d 30
```

Analyzing Results (example for 2.4GHz close to AP)

Use the Python script to analyze and visualize throughput logs and PCAP files: 
```bash
python doctor.py -f logs/wslog_f_24.pcapng -if logs/iperflog_f_24 -mf logs/mylog_f_24 -s 02:43:31:39:9c:ef -d b8:1e:a4:6c:d8:09 -dbg
```