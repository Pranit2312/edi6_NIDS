"""
Real-Time Packet Sniffing Engine
Uses Scapy for cross-platform packet capture
Supports Windows (Npcap), Linux (libpcap), macOS (libpcap)
"""

import threading
import time
import queue
import os
from typing import Dict, Callable, Optional, List
from datetime import datetime, timezone
import logging
from utils.stats_manager import stats_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RateTracker:
    """
    Tracks per-source-IP packet rates in real-time using sliding windows.
    Enriches raw packets with computed rate fields so the rule engine
    can detect SYN floods, DDoS, port scans, and brute force attacks.
    """

    def __init__(self, window_seconds=5):
        self.window = window_seconds
        self.lock = threading.Lock()
        # Per source-IP tracking
        self.ip_packets = {}      # ip -> [timestamps]
        self.ip_bytes = {}        # ip -> [(timestamp, size)]
        self.ip_syn_packets = {}  # ip -> [timestamps of SYN-only packets]
        # Per flow tracking: (src_ip, dst_ip, dst_port, protocol) -> [packet_data]
        self.flow_packets = {}

    def _cleanup_list(self, lst, cutoff):
        """Remove entries older than cutoff from a list of timestamps."""
        # Since timestamps are appended in order, find first valid index
        i = 0
        for i, val in enumerate(lst):
            t = val if isinstance(val, (int, float)) else val[0]
            if t > cutoff:
                break
        else:
            if lst:
                t = lst[-1] if isinstance(lst[-1], (int, float)) else lst[-1][0]
                if t <= cutoff:
                    return []
            return lst
        return lst[i:]

    def record_packet(self, packet_data):
        """
        Record a packet and return enriched copy with computed rate fields.
        This is the key function that bridges raw packet capture and detection.
        """
        now = time.time()
        src_ip = packet_data.get('src_ip', '0.0.0.0')
        dst_ip = packet_data.get('dst_ip', '0.0.0.0')
        dst_port = packet_data.get('dst_port', 0)
        protocol = packet_data.get('protocol', 'OTHER')
        size = packet_data.get('packet_size', 0)
        tcp_flags = packet_data.get('tcp_flags', '')

        with self.lock:
            cutoff = now - self.window

            # --- Per-IP packet timestamps ---
            if src_ip not in self.ip_packets:
                self.ip_packets[src_ip] = []
            self.ip_packets[src_ip].append(now)
            self.ip_packets[src_ip] = [t for t in self.ip_packets[src_ip] if t > cutoff]

            # --- Per-IP byte tracking ---
            if src_ip not in self.ip_bytes:
                self.ip_bytes[src_ip] = []
            self.ip_bytes[src_ip].append((now, size))
            self.ip_bytes[src_ip] = [(t, s) for t, s in self.ip_bytes[src_ip] if t > cutoff]

            # --- Per-IP SYN-only packet tracking ---
            if src_ip not in self.ip_syn_packets:
                self.ip_syn_packets[src_ip] = []
            # SYN-only: has S flag but NOT A (SYN-ACK) flag
            if 'S' in tcp_flags and 'A' not in tcp_flags:
                self.ip_syn_packets[src_ip].append(now)
            self.ip_syn_packets[src_ip] = [t for t in self.ip_syn_packets[src_ip] if t > cutoff]

            # --- Flow tracking ---
            flow_key = f"{src_ip}-{dst_ip}-{dst_port}-{protocol}"
            if flow_key not in self.flow_packets:
                self.flow_packets[flow_key] = []
            self.flow_packets[flow_key].append(packet_data)
            # Keep only last 50 packets per flow to limit memory
            if len(self.flow_packets[flow_key]) > 50:
                self.flow_packets[flow_key] = self.flow_packets[flow_key][-50:]

            # --- Compute rates ---
            packet_count = len(self.ip_packets[src_ip])
            packet_rate = packet_count / self.window  # packets per second

            total_bytes = sum(s for _, s in self.ip_bytes[src_ip])
            byte_rate = total_bytes / self.window  # bytes per second

            syn_count = len(self.ip_syn_packets[src_ip])
            syn_rate = syn_count / self.window  # SYN packets per second

            flow_packet_list = list(self.flow_packets[flow_key])

        # Return enriched copy of packet data
        enriched = dict(packet_data)
        enriched['packet_rate'] = packet_rate
        enriched['byte_rate'] = byte_rate
        enriched['syn_rate'] = syn_rate
        enriched['syn_count'] = syn_count
        enriched['flow_packets'] = flow_packet_list
        enriched['connection_count'] = packet_count

        return enriched

    def cleanup_stale(self):
        """Periodic cleanup of stale entries to prevent memory leaks."""
        now = time.time()
        cutoff = now - self.window * 3
        with self.lock:
            for ip in list(self.ip_packets.keys()):
                self.ip_packets[ip] = [t for t in self.ip_packets[ip] if t > cutoff]
                if not self.ip_packets[ip]:
                    del self.ip_packets[ip]
                    self.ip_bytes.pop(ip, None)
                    self.ip_syn_packets.pop(ip, None)

            for fk in list(self.flow_packets.keys()):
                if not self.flow_packets[fk]:
                    del self.flow_packets[fk]


# Global rate tracker instance
rate_tracker = RateTracker(window_seconds=5)


# Try to import Scapy
try:
    from scapy.all import sniff, IP, IPv6, TCP, UDP, ICMP, ICMPv6EchoRequest, ARP, Raw, conf, get_if_list, Ether
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    logger.warning("Scapy not available. Packet capture will use mock data.")


class PacketSniffer:
    """
    Real-time packet sniffer using Scapy.
    Thread-safe and handles errors gracefully.
    """
    
    def __init__(self, packet_queue: queue.Queue, interface: Optional[str] = None,
                 packet_count: int = 0, filter_expr: str = "ip or ip6 or arp"):
        """
        Initialize packet sniffer.
        
        Args:
            packet_queue: Queue to put captured packets
            interface: Network interface to sniff on (auto-detect if None)
            packet_count: Max packets to capture (0 = unlimited)
            filter_expr: BPF filter expression
        """
        self.packet_queue = packet_queue
        self.interface = interface
        self.packet_count = packet_count
        self.filter_expr = filter_expr
        self.running = False
        self.thread = None
        self.packet_callback = None
        self.dropped_count = 0
    
    @staticmethod
    def get_interfaces() -> List[Dict]:
        """Get list of available network interfaces with details"""
        interfaces = []
        if not SCAPY_AVAILABLE:
            return [{'name': 'mock', 'description': 'Mock Interface'}]
        
        try:
            from scapy.all import get_if_list, conf
            if_list = get_if_list()
            for iface in if_list:
                interfaces.append({
                    'name': iface,
                    'description': str(iface)
                })
            return interfaces
        except Exception as e:
            logger.error(f"Could not get interfaces: {e}")
            return []
    
    def _packet_callback(self, packet):
        """Process captured packet"""
        try:
            packet_data = self._parse_packet(packet)

            if packet_data:
                # Update stats_manager
                stats_manager.update_packet(packet_data)
                
                # Put in queue with timeout to avoid blocking
                try:
                    self.packet_queue.put(packet_data, block=False)
                except queue.Full:
                    self.dropped_count += 1
                    if self.dropped_count % 100 == 0:
                        logger.warning(f"Queue full! Dropped {self.dropped_count} packets.")
        except Exception as e:
            logger.error(f"Error processing packet: {e}")
    
    @staticmethod
    def _parse_packet(packet) -> Optional[Dict]:
        """
        Parse Scapy packet into dictionary format.
        Supports IPv4, IPv6, TCP, UDP, ICMP, ARP.
        """
        try:
            packet_dict = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'packet_size': len(packet),
                'protocol': 'OTHER',
                'src_ip': '0.0.0.0',
                'dst_ip': '0.0.0.0',
                'src_port': 0,
                'dst_port': 0,
                'tcp_flags': '',
                'raw_data': bytes(packet)[:512],
                'ether_type': 'Unknown'
            }

            # Ethernet Layer
            if Ether in packet:
                packet_dict['src_mac'] = packet[Ether].src
                packet_dict['dst_mac'] = packet[Ether].dst
            
            # IP Layer (v4)
            if IP in packet:
                ip_layer = packet[IP]
                packet_dict['src_ip'] = ip_layer.src
                packet_dict['dst_ip'] = ip_layer.dst
                packet_dict['ttl'] = ip_layer.ttl
                packet_dict['ip_flags'] = str(ip_layer.flags)
                packet_dict['protocol_num'] = ip_layer.proto
                
                # TCP Layer
                if TCP in packet:
                    tcp_layer = packet[TCP]
                    packet_dict['protocol'] = 'TCP'
                    packet_dict['src_port'] = tcp_layer.sport
                    packet_dict['dst_port'] = tcp_layer.dport
                    packet_dict['tcp_flags'] = PacketSniffer._parse_tcp_flags(
                        int(tcp_layer.flags)
                    )
                    packet_dict['tcp_seq'] = tcp_layer.seq
                    packet_dict['tcp_ack'] = tcp_layer.ack
                    
                # UDP Layer
                elif UDP in packet:
                    udp_layer = packet[UDP]
                    packet_dict['protocol'] = 'UDP'
                    packet_dict['src_port'] = udp_layer.sport
                    packet_dict['dst_port'] = udp_layer.dport
                    
                # ICMP Layer
                elif ICMP in packet:
                    packet_dict['protocol'] = 'ICMP'
                    icmp_layer = packet[ICMP]
                    packet_dict['icmp_type'] = icmp_layer.type
                    packet_dict['icmp_code'] = icmp_layer.code

            # IPv6 Layer
            elif IPv6 in packet:
                ipv6_layer = packet[IPv6]
                packet_dict['src_ip'] = ipv6_layer.src
                packet_dict['dst_ip'] = ipv6_layer.dst
                packet_dict['protocol'] = 'IPv6'
                
                if TCP in packet:
                    packet_dict['protocol'] = 'TCP'
                    packet_dict['src_port'] = packet[TCP].sport
                    packet_dict['dst_port'] = packet[TCP].dport
                elif UDP in packet:
                    packet_dict['protocol'] = 'UDP'
                    packet_dict['src_port'] = packet[UDP].sport
                    packet_dict['dst_port'] = packet[UDP].dport
                elif ICMPv6EchoRequest in packet:
                    packet_dict['protocol'] = 'ICMPv6'

            # ARP Layer
            elif ARP in packet:
                arp_layer = packet[ARP]
                packet_dict['protocol'] = 'ARP'
                packet_dict['src_ip'] = arp_layer.psrc
                packet_dict['dst_ip'] = arp_layer.pdst
            
            # Payload
            if Raw in packet:
                raw_layer = packet[Raw]
                packet_dict['payload_size'] = len(raw_layer.load)
            else:
                packet_dict['payload_size'] = 0
            
            return packet_dict
            
        except Exception as e:
            # Skip malformed packets
            return None
    
    @staticmethod
    def _parse_tcp_flags(flags_int: int) -> str:
        """Convert TCP flags integer to string"""
        flag_map = {
            1: 'F',
            2: 'S',
            4: 'R',
            8: 'P',
            16: 'A',
            32: 'U',
            64: 'E',
            128: 'C',
        }
        
        flags_str = ''
        for value, flag in sorted(flag_map.items()):
            if flags_int & value:
                flags_str += flag
        
        return flags_str
    
    def start(self):
        """Start packet sniffing in background thread"""
        if self.running:
            logger.warning("Sniffer already running")
            return
        
        self.running = True
        self.thread = threading.Thread(
            target=self._sniff_thread,
            daemon=False
        )
        self.thread.start()
        logger.info(f"Packet sniffer started on {self.interface}")
    
    def _sniff_thread(self):
        """Thread function for packet sniffing"""
        if not SCAPY_AVAILABLE:
            logger.warning("Using mock packet generation (Scapy not available)")
            self._mock_sniff()
            return
        
        # On Windows, try to find a valid interface if none specified
        if self.interface is None and os.name == 'nt':
            try:
                import psutil
                # Find interface with most traffic
                stats = psutil.net_io_counters(pernic=True)
                # Filter out loopback and interfaces with 0 traffic
                active_ifs = {name: s.bytes_sent + s.bytes_recv for name, s in stats.items() 
                             if s.bytes_sent > 0 and 'loopback' not in name.lower()}
                
                if active_ifs:
                    best_if = max(active_ifs.items(), key=lambda x: x[1])[0]
                    logger.info(f"Auto-detected active interface: {best_if}")
                    
                    # Map psutil name to scapy name/GUID if needed
                    # For now, let's try using the name directly
                    self.interface = best_if
                else:
                    logger.info(f"No active interfaces with traffic found. Using Scapy default: {conf.iface}")
            except Exception as e:
                logger.error(f"Error detecting active interface: {e}")

        logger.info(f"Starting real-time sniff on {self.interface or 'default interface'}")
        
        try:
            while self.running:
                sniff(
                    prn=self._packet_callback,
                    store=False,
                    iface=self.interface,
                    filter=self.filter_expr,
                    timeout=1.0,  # Short timeout to allow checking self.running
                    stop_filter=lambda x: not self.running,
                    promisc=True  # Support promiscuous mode for all traffic
                )
        except PermissionError as e:
            logger.error(f"Permission denied: {e}")
            logger.error(f"Need admin/root privileges for packet capture on {self.interface or 'default interface'}")
            logger.info("Falling back to mock packet generation...")
            self._mock_sniff()
        except Exception as e:
            logger.error(f"Packet capture error: {e}")
            logger.info("Falling back to mock packet generation...")
            self._mock_sniff()
    
    def _mock_sniff(self):
        """Generate mock packets (for testing without Scapy)"""
        import random
        
        protocols = ['TCP', 'UDP', 'ICMP', 'ARP']
        attack_types = ['Normal', 'DDoS', 'Port Scan', 'SYN Flood', 'Brute Force']
        
        logger.info("Starting mock packet generation mode...")
        packet_count = 0
        
        # Attacker simulation
        attacker_ip = f"192.168.1.{random.randint(100, 200)}"
        victim_ip = "10.20.2.117" # User's IP from ipconfig

        while self.running:
            try:
                # Randomly simulate attacks
                is_attack = random.random() < 0.15
                attack_type = 'Normal'
                
                if is_attack:
                    attack_type = random.choice(attack_types[1:])
                
                # Generate VARYING packet sizes each time
                random_size = random.randint(64, 1500)
                
                packet_data = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'packet_size': random_size,
                    'size': random_size,
                    'protocol': random.choice(protocols),
                    'src_ip': attacker_ip if is_attack else f"192.168.1.{random.randint(2, 254)}",
                    'dst_ip': victim_ip,
                    'src_port': random.randint(1024, 65535),
                    'dst_port': random.choice([22, 80, 443, 3389, 445, 53, 25]),
                    'tcp_flags': 'S' if attack_type == 'SYN Flood' else random.choice(['S', 'SA', 'A', 'FA', '']),
                    'payload_size': random.randint(0, 1000),
                    'ttl': random.randint(32, 255),
                    'packet_rate': random.uniform(10, 2000) if is_attack else random.uniform(0.1, 100),
                    'byte_rate': random.uniform(1000, 5_000_000) if is_attack else random.uniform(100, 100_000),
                    'duration': random.uniform(0.001, 10),
                    'is_attack': is_attack,
                    'attack_type': attack_type,
                }
                
                # Update stats_manager
                stats_manager.update_packet(packet_data, is_attack=is_attack)
                
                try:
                    self.packet_queue.put(packet_data, block=False)
                except queue.Full:
                    pass

                packet_count += 1
                if packet_count % 500 == 0:
                    logger.info(f"Mock packets processed: {packet_count}")
                
                # Control simulation speed
                time.sleep(random.uniform(0.005, 0.02))
                
            except Exception as e:
                logger.error(f"Mock packet generation error: {e}")
                continue
    
    def stop(self):
        """Stop packet sniffing"""
        self.running = False

        # Do NOT block forever waiting for sniff thread
        if self.thread and self.thread.is_alive():
            try:
                self.thread.join(timeout=1)
            except:
                pass
        
        logger.info("Packet sniffer stopped")


class PacketProcessor:
    """
    Process packets from queue and send to detection engine.
    """
    
    def __init__(self, packet_queue: queue.Queue, 
                 detection_callback: Callable[[Dict], None],
                 batch_size: int = 1):
        """
        Initialize processor.
        
        Args:
            packet_queue: Queue of packets to process
            detection_callback: Callback function for detected attacks
            batch_size: Number of packets to batch before processing
        """
        self.packet_queue = packet_queue
        self.detection_callback = detection_callback
        self.batch_size = batch_size
        self.running = False
        self.thread = None
    
    def start(self):
        """Start processing packets"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(
            target=self._process_thread,
            daemon=False
        )
        self.thread.start()
        logger.info("Packet processor started")
    
    def _process_thread(self):
        """Process packets from queue"""
        batch = []
        
        while self.running:
            try:
                # Try to get packet with timeout
                packet = self.packet_queue.get(timeout=1)
                batch.append(packet)
                
                # Process batch when full
                if len(batch) >= self.batch_size:
                    for pkt in batch:
                        self.detection_callback(pkt)
                    batch = []
                    
            except queue.Empty:
                # Process any remaining packets in batch
                if batch:
                    for pkt in batch:
                        self.detection_callback(pkt)
                    batch = []
                continue
    
    def stop(self):
        """Stop processing"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Packet processor stopped")

