import pyshark
class PcapReader:
    """
    PcapReader.py
    802.11 packet reader using PyShark.
    """
    def __init__(self, file_path):
        """
        Initialize the PcapReader with the path to the pcap file.
        :param file_path: Path to the pcap file.
        """
        self.file_path = file_path
        self.capture = None # Capture object of a pcap file

    def read_packets(self):
        """
        Generator to read packets from the pcap file.
        Yields packets as pyshark.packet.packet.Packet objects.
        """
        try:
            # Initialize capture object and read all packets
            self.capture = pyshark.FileCapture(self.file_path)
            for packet in self.capture:
                yield packet
        except FileNotFoundError:
            self.capture = None
            raise ValueError(f"File not found: {self.file_path}")
        except Exception as e:
            self.capture = None
            raise ValueError(f"Error reading pcap file: {e}")

    def read_next_packet(self):
        """
        Read the next packet from the pcap file.
        :return: pyshark.packet.packet.Packet object or None if end of file is reached.
        """
        if self.capture is None: # initialize a new capture object
            self.capture = pyshark.FileCapture(self.file_path)

        try:
            # Returns next packet
            return self.capture.next()
        except StopIteration:
            self.close()
            return None
        except AttributeError:
            self.close()
            raise ValueError("Error reading next packet. Ensure the capture is valid.")

    def get_80211_info(self, packet):
        """
        Extract 802.11 wireless information from a packet.
        :param packet: pyshark.packet.packet.Packet object.
        :return: Dictionary containing 802.11 information (e.g., source address, destination address, SSID).
        """
        try:
            # Layers
            wlan_layer = packet.get_multiple_layers('wlan')[0]
            wlan_radio_layer = packet.get_multiple_layers('wlan_radio')[0]

            info = {
                # IEEE 802.11 Beacon Frame Information
                'bssid': wlan_layer.get_field('bssid'), # BSSID
                'ta': wlan_layer.get_field('ta'), # Transmitter Address
                'ra': wlan_layer.get_field('ra'), # Receiver Address
                'type_subtype': wlan_layer.get_field('fc_type_subtype'), # Frame Control Type Subtype
                'fc_retry': wlan_layer.get_field('fc_retry'), # Frame Control Retry
                
                # 802.11 Radio Information
                'phy': wlan_radio_layer.get_field('phy'), # Physical Layer
                'data_rate': wlan_radio_layer.get_field('data_rate'), # Data Rate
                'channel': wlan_radio_layer.get_field('channel'), # Channel
                'frequency': wlan_radio_layer.get_field('frequency'), # Frequency
                'signal_dbm': wlan_radio_layer.get_field('signal_dbm'), # Signal Strength (dBm)
                'bandwidth': wlan_radio_layer.get_field('11n_bandwidth'), # Bandwidth
                'short_gi': wlan_radio_layer.get_field('11n_short_gi'), # Short Guard Interval
                'mcs_index': wlan_radio_layer.get_field('11n_mcs_index'), # MCS Index
                'duration': wlan_radio_layer.get_field('duration'), # Duration
                'preamble': wlan_radio_layer.get_field('preamble'), # Preamble
                
                # Extra calculations
                'spatial_streams': self.calculate_spatial_streams(wlan_radio_layer.get_field('11n_mcs_index')), # Number of spatial streams
                'phy_gap': self.get_phy_gap(wlan_radio_layer.get_field('signal_dbm'), 
                                             wlan_radio_layer.get_field('11n_bandwidth'), 
                                             wlan_radio_layer.get_field('11n_mcs_index'),
                                             self.calculate_spatial_streams(wlan_radio_layer.get_field('11n_mcs_index'))), # PHY Gain
                
                # Extra info
                'ssid': self.get_ssid(packet),
                
                'signal_noise_ratio': None, # Didnt find it
            }
            return info
        except AttributeError: # Handle case where layers are not present
            raise ValueError("Not an 802.11 packet.")

    def calculate_spatial_streams(self, mcs_index):
        """
        Calculate the number of spacial streams based on the MCS index.
        :param mcs_index: MCS index value.
        :return: Number of spacial streams.
        """
        # From table: 0 to 7 has 1 spacial stream, 8 to 15 has 2 spacial streams.
        return int(mcs_index) // 8 + 1 if mcs_index is not None else 0

    def get_phy_gap(self, rssi, bandwidth, mcs_index, spatial_streams):
        """
        Calculate the PHY gain based on RSSI and bandwidth.
        :param rssi: Received Signal Strength Indicator (RSSI).
        :param bandwidth: Bandwidth in MHz.
        :return: PHY gain.
        """
        # Convert table for each Bandwidth [0: 20, 1: 40, 2: 80, 3: 160]
        expected_mcs = { 0: [ -82, -79, -77, -74, -70, -66, -65, -64 ],
                         1: [ -79, -76, -74, -71, -67, -63, -62, -61 ],
                         2: [ -76, -73, -71, -68, -64, -60, -59, -58 ],
                         3: [ -73, -70, -68, -65, -61, -57, -56, -55 ] }
        
        if bandwidth is None or mcs_index is None:
            return None # No bandwidth or mcs index means no phy gap
        
        if rssi is None:
            return 4 # Arbitrary value, means no signal strength (bad packet)
        
        # Get expected mcs
        for i, m in  enumerate(expected_mcs[int(bandwidth)]):
            if int(rssi) >= m:
                expected_mcs = i
            else:
                break
        
        # Calculate phy gain
        return expected_mcs + 8 * (spatial_streams-1) - int(mcs_index)

    def get_ssid(self, packet):
        """
        Extract SSID from the packet.
        :param packet: pyshark packet object.
        """
        # Get mgt layer if it exists
        wlan_mgt_layer = packet.get_multiple_layers("wlan.mgt")[0] if packet.get_multiple_layers("wlan.mgt") else None
        if wlan_mgt_layer:
            ssid = wlan_mgt_layer.get_field("ssid")
            if ssid:
                return ssid
        # If something goes wrong, return None (no ssid)
        return None

    def close(self):
        """
        Close the pcap file.
        """
        if self.capture:
            self.capture.close()
            self.capture = None