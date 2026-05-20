"""
Rule-Based Detection Engine
Hybrid IDS with rule-based fallback for low ML confidence
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple
import ipaddress


@dataclass
class DetectionResult:
    """Detection result object"""
    is_attack: bool
    attack_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    confidence: float  # 0.0 - 1.0
    reason: str
    rules_triggered: List[str]
    timestamp: str
    
    def to_dict(self):
        return {
            'is_attack': self.is_attack,
            'attack_type': self.attack_type,
            'severity': self.severity,
            'confidence': self.confidence,
            'reason': self.reason,
            'rules_triggered': self.rules_triggered,
            'timestamp': self.timestamp
        }


class RuleBasedDetector:
    """
    Rule-based anomaly detection engine.
    Used as fallback when ML confidence is low.
    """
    
    def __init__(self, ml_confidence_threshold=0.7):
        self.ml_confidence_threshold = ml_confidence_threshold
        
        # Suspicious port mappings
        self.suspicious_ports = {
            # Port Scanning
            135: ('port_scan', 'RPC Endpoint Mapper'),
            139: ('port_scan', 'NetBIOS'),
            445: ('port_scan', 'SMB'),
            3389: ('port_scan', 'RDP'),
            
            # SSH Brute Force targets
            22: ('brute_force', 'SSH'),
            
            # SMTP Abuse
            25: ('smtp_abuse', 'SMTP'),
            587: ('smtp_abuse', 'SMTP Submission'),
            
            # DNS/DHCP abuse
            53: ('dns_abuse', 'DNS'),
            67: ('dhcp_abuse', 'DHCP'),
            68: ('dhcp_abuse', 'DHCP'),
            
            # Database targets
            3306: ('db_attack', 'MySQL'),
            5432: ('db_attack', 'PostgreSQL'),
            1433: ('db_attack', 'MSSQL'),
            5984: ('db_attack', 'CouchDB'),
            6379: ('db_attack', 'Redis'),
            27017: ('db_attack', 'MongoDB'),
        }
        
        # Botnet C&C ports
        self.botnet_ports = {
            6667: 'IRC',  # IRC Command & Control
            8080: 'HTTP Proxy',
            9090: 'SOCKS5',
        }
    
    def detect(self, packet_data: Dict, ml_result: Dict = None) -> DetectionResult:
        """
        Perform rule-based detection.
        
        Args:
            packet_data: Packet information
            ml_result: ML model prediction result (optional)
            
        Returns:
            DetectionResult object
        """
        rules_triggered = []
        attack_type = 'Unknown'
        max_severity = 'low'
        base_confidence = 0.0
        reason = ''
        
        # Extract packet information
        src_ip = packet_data.get('src_ip', '')
        dst_ip = packet_data.get('dst_ip', '')
        protocol = packet_data.get('protocol', '').upper()
        src_port = packet_data.get('src_port', 0)
        dst_port = packet_data.get('dst_port', 0)
        packet_size = packet_data.get('packet_size', 0)
        packet_rate = packet_data.get('packet_rate', 0)
        byte_rate = packet_data.get('byte_rate', 0)
        tcp_flags = packet_data.get('tcp_flags', '')
        
        # Rule 1: Port Scanning Detection
        scan_result = self._detect_port_scan(
            dst_port, packet_size, packet_rate, tcp_flags
        )
        if scan_result[0]:
            rules_triggered.append(f"Port Scan: {scan_result[1]}")
            attack_type = 'Port Scan'
            base_confidence += 0.3
            if max_severity in ['low']:
                max_severity = 'medium'
        
        # Rule 2: DDoS Detection
        ddos_result = self._detect_ddos(packet_rate, byte_rate, packet_size)
        if ddos_result[0]:
            rules_triggered.append(f"DDoS Attack: {ddos_result[1]}")
            attack_type = 'DDoS'
            base_confidence += 0.4
            max_severity = 'critical'
        
        # Rule 3: SYN Flood Detection
        syn_result = self._detect_syn_flood(tcp_flags, packet_rate, packet_size)
        if syn_result[0]:
            rules_triggered.append(f"SYN Flood: {syn_result[1]}")
            attack_type = 'SYN Flood'
            base_confidence += 0.35
            max_severity = 'critical'
        
        # Rule 4: ICMP Flood Detection
        icmp_result = self._detect_icmp_flood(protocol, packet_rate, packet_size)
        if icmp_result[0]:
            rules_triggered.append(f"ICMP Flood: {icmp_result[1]}")
            attack_type = 'ICMP Flood'
            base_confidence += 0.35
            max_severity = 'critical'
        
        # Rule 5: Suspicious Port Access
        suspicious_result = self._detect_suspicious_port(
            dst_port, src_ip, dst_ip
        )
        if suspicious_result[0]:
            rules_triggered.append(f"Suspicious Port: {suspicious_result[1]}")
            if attack_type == 'Unknown':
                attack_type = suspicious_result[2]
            base_confidence += 0.2
            if max_severity in ['low']:
                max_severity = 'medium'
        
        # Rule 6: Large Packet Anomaly
        large_pkt_result = self._detect_large_packets(packet_size, protocol)
        if large_pkt_result[0]:
            rules_triggered.append(f"Large Packet: {large_pkt_result[1]}")
            base_confidence += 0.15
        
        # Rule 7: Unusual Traffic Pattern
        traffic_result = self._detect_unusual_traffic(
            packet_rate, byte_rate, packet_size
        )
        if traffic_result[0]:
            rules_triggered.append(f"Unusual Traffic: {traffic_result[1]}")
            base_confidence += 0.2
        
        # Determine final decision
        is_attack = False
        final_confidence = min(base_confidence, 1.0)
        
        # Use ML result if available
        if ml_result:
            ml_confidence = ml_result.get('confidence', 0.0)
            ml_is_attack = ml_result.get('is_attack', False)
            
            # If ML confidence is high, use ML result
            if ml_confidence >= self.ml_confidence_threshold:
                is_attack = ml_is_attack
                final_confidence = ml_confidence
                
                if ml_is_attack:
                    attack_type = ml_result.get('attack_type', 'Unknown')
                    reason = f"ML Detection ({final_confidence:.2%}) - {attack_type}"
                    if max_severity == 'low':
                        max_severity = 'high'
                else:
                    reason = f"Benign (ML confidence: {final_confidence:.2%})"
            else:
                # ML confidence is low, use rule-based result
                is_attack = len(rules_triggered) > 0 and final_confidence > 0.3
                reason = f"Rule-based detection (Rules: {len(rules_triggered)})"
        else:
            # No ML result, use pure rule-based detection
            is_attack = len(rules_triggered) > 0 and final_confidence > 0.3
            reason = f"Rule-based detection (Rules: {len(rules_triggered)})"
            if not is_attack and attack_type == 'Unknown':
                attack_type = 'Benign'
        
        result = DetectionResult(
            is_attack=is_attack,
            attack_type=attack_type,
            severity=max_severity,
            confidence=final_confidence,
            reason=reason,
            rules_triggered=rules_triggered,
            timestamp=datetime.utcnow().isoformat()
        )
        
        return result
    
    def _detect_port_scan(self, dst_port: int, packet_size: int,
                      packet_rate: float, tcp_flags: str) -> Tuple[bool, str]:
        """Detect potential port scanning"""

        # Ignore normal traffic
        safe_ports = [80, 443, 53, 8080]

        if dst_port in safe_ports:
            return False, ''

        # Realistic port scan conditions
        if (
            tcp_flags
            and 'S' in tcp_flags
            and 'A' not in tcp_flags
            and packet_size < 60
            and packet_rate > 200
        ):
            return True, f"High-rate SYN scan on port {dst_port}"

        return False, ''
    
    def _detect_ddos(self, packet_rate: float, byte_rate: float, 
                     packet_size: int) -> Tuple[bool, str]:
        """Detect DDoS attack patterns"""
        # High packet rate with consistent sizes
        if packet_rate > 1000:  # packets per second
            return True, f"Excessive packet rate: {packet_rate:.0f} pps"
        
        # Byte rate exceeding normal thresholds
        if byte_rate > 10_000_000:  # 10 Mbps
            return True, f"Excessive byte rate: {byte_rate/1_000_000:.1f} Mbps"
        
        return False, ''
    
    def _detect_syn_flood(self, tcp_flags: str, packet_rate: float, 
                          packet_size: int) -> Tuple[bool, str]:
        """Detect SYN flood attack"""
        # Many SYN packets with no DATA
        if tcp_flags and 'S' in tcp_flags and 'A' not in tcp_flags:
            if packet_rate > 500:
                return True, f"SYN flood: {packet_rate:.0f} SYN packets/sec"
        
        return False, ''
    
    def _detect_icmp_flood(self, protocol: str, packet_rate: float, 
                           packet_size: int) -> Tuple[bool, str]:
        """Detect ICMP flood attack"""
        if protocol == 'ICMP':
            if packet_rate > 1000:
                return True, f"ICMP flood: {packet_rate:.0f} ICMP packets/sec"
        
        return False, ''
    
    def _detect_suspicious_port(self, dst_port: int, src_ip: str,
                            dst_ip: str) -> Tuple[bool, str, str]:
        """Detect suspicious ports with stricter logic"""

        # Ignore localhost/internal traffic
        if src_ip.startswith("127.") or dst_ip.startswith("127."):
            return False, '', 'Unknown'

        if src_ip.startswith("192.168.") or src_ip.startswith("172."):
            return False, '', 'Unknown'

        # Only detect botnet ports
        if dst_port in self.botnet_ports:
            return True, (
                f"Botnet C&C port {dst_port}: "
                f"{self.botnet_ports[dst_port]}"
            ), 'Botnet'

        return False, '', 'Unknown'
    
    def _detect_large_packets(self, packet_size: int, protocol: str) -> Tuple[bool, str]:
        """Detect abnormally large packets"""
        # Standard MTU is 1500 bytes
        if packet_size > 2000:
            return True, f"Jumbo packet ({packet_size} bytes)"
        
        # ICMP packets should be relatively small
        if protocol == 'ICMP' and packet_size > 1000:
            return True, f"Oversized ICMP packet ({packet_size} bytes)"
        
        return False, ''
    
    def _detect_unusual_traffic(self, packet_rate: float, byte_rate: float, 
                                packet_size: int) -> Tuple[bool, str]:
        """Detect unusual traffic patterns"""
        avg_packet_size = byte_rate / max(packet_rate, 1)
        
        # Very small average packet size = many control packets
        if avg_packet_size < 50 and packet_rate > 100:
            return True, f"Unusual small packets: avg {avg_packet_size:.0f} bytes"
        
        return False, ''


class HybridDetector:
    """
    Hybrid detector combining ML and rule-based detection.
    """
    
    def __init__(self, ml_model=None, ml_confidence_threshold=0.7):
        self.ml_model = ml_model
        self.rule_detector = RuleBasedDetector(ml_confidence_threshold)
    
    def detect(self, packet_data: Dict, ml_prediction=None) -> DetectionResult:
        """
        Perform hybrid detection using ML and rules.
        """
        return self.rule_detector.detect(packet_data, ml_prediction)
