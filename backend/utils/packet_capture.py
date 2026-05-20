"""
Real-Time Packet Sniffing Engine
Uses Scapy for cross-platform packet capture
Supports Windows (Npcap), Linux (libpcap), macOS (libpcap)
"""

import threading
import time
import queue
from typing import Dict, Callable, Optional, List
from datetime import datetime
import logging
from utils.stats_manager import stats_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import Scapy
try:
    from scapy.all import sniff, IP, TCP, UDP, ICMP, Raw
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
                 packet_count: int = 0, filter_expr: str = "ip"):
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
    
    @staticmethod
    def get_interfaces() -> List[str]:
        """Get list of available network interfaces"""
        if not SCAPY_AVAILABLE:
            return ['mock']
        
        try:
            from scapy.all import get_if_list
            return get_if_list()
        except Exception as e:
            logger.error(f"Could not get interfaces: {e}")
            return []
    
    def _packet_callback(self, packet):
        """Process captured packet"""
        try:
            packet_data = self._parse_packet(packet)

            if packet_data:
                stats_manager.update_packet(packet_data)
                self.packet_queue.put(packet_data, timeout=1)
        except Exception as e:
            logger.error(f"Error processing packet: {e}")
    
    @staticmethod
    def _parse_packet(packet) -> Optional[Dict]:
        """
        Parse Scapy packet into dictionary format.
        
        Args:
            packet: Scapy packet object
            
        Returns:
            Dictionary with packet information or None
        """
        try:
            packet_dict = {
                'timestamp': datetime.utcnow().isoformat(),
                'packet_size': len(packet),
                'protocol': 'OTHER',
                'src_ip': '0.0.0.0',
                'dst_ip': '0.0.0.0',
                'src_port': 0,
                'dst_port': 0,
                'tcp_flags': '',
                'raw_data': bytes(packet)[:512],
            }
            
            # IP Layer
            if IP in packet:
                ip_layer = packet[IP]
                packet_dict['src_ip'] = ip_layer.src
                packet_dict['dst_ip'] = ip_layer.dst
                packet_dict['ttl'] = ip_layer.ttl
                packet_dict['ip_flags'] = ip_layer.flags
                
                # TCP Layer
                if TCP in packet:
                    tcp_layer = packet[TCP]
                    packet_dict['protocol'] = 'TCP'
                    packet_dict['src_port'] = tcp_layer.sport
                    packet_dict['dst_port'] = tcp_layer.dport
                    packet_dict['tcp_flags'] = PacketSniffer._parse_tcp_flags(
                        tcp_layer.flags
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
            
            # Payload
            if Raw in packet:
                raw_layer = packet[Raw]
                packet_dict['payload_size'] = len(raw_layer.load)
            else:
                packet_dict['payload_size'] = 0
            
            return packet_dict
            
        except Exception as e:
            logger.error(f"Error parsing packet: {e}")
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
        
        try:
            while self.running:
                sniff(
                    prn=self._packet_callback,
                    store=False,
                    iface=self.interface,
                    filter="ip",
                    timeout=1,
                    stop_filter=lambda x: not self.running
                )
        except PermissionError:
            logger.error("Permission denied. Need admin/root privileges for packet capture.")
            logger.info("Falling back to mock packet generation...")
            self._mock_sniff()
        except Exception as e:
            logger.error(f"Packet capture error: {e}")
            logger.info("Falling back to mock packet generation...")
            self._mock_sniff()
    
    def _mock_sniff(self):
        """Generate mock packets (for testing without Scapy)"""
        import random
        
        protocols = ['TCP', 'UDP', 'ICMP']
        attack_types = ['Normal', 'DDoS', 'PortScan', 'BruteForce']
        
        while self.running:
            try:
                is_attack = random.random() < 0.1
                
                packet_data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'packet_size': random.randint(64, 1500),
                    'protocol': random.choice(protocols),
                    'src_ip': f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                    'dst_ip': f"10.0.{random.randint(1, 255)}.{random.randint(1, 255)}",
                    'src_port': random.randint(1024, 65535),
                    'dst_port': random.choice([22, 80, 443, 3389, 445, 53, 25]),
                    'tcp_flags': random.choice(['S', 'SA', 'A', 'FA', '']),
                    'payload_size': random.randint(0, 1000),
                    'ttl': random.randint(32, 255),
                    'packet_rate': random.uniform(0.1, 1000),
                    'byte_rate': random.uniform(100, 1_000_000),
                    'duration': random.uniform(0.001, 10),
                    'is_attack': is_attack,
                    'attack_type': random.choice(attack_types) if is_attack else 'Normal',
                }
                
                self.packet_queue.put(packet_data, timeout=1)
                time.sleep(random.uniform(0.01, 0.1))
                
            except queue.Full:
                continue
            except Exception as e:
                logger.error(f"Mock packet generation error: {e}")
    
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

