"""
Rule-Based Detection Engine
Hybrid IDS with rule-based fallback for low ML confidence
"""

from dataclasses import dataclass
from datetime import datetime, timezone
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
    
    def _detect_port_scan(self, dst_port: int, packet_size: int,
                      packet_rate: float, tcp_flags: str) -> Tuple[bool, str]:
        """Detect potential port scanning"""
        # Ignore normal web traffic ports for scan detection
        safe_ports = [80, 443, 53, 8080]

        if dst_port in safe_ports:
            return False, ''

        # Detect high-rate port scans (e.g. Nmap)
        if (
            tcp_flags
            and ('S' in tcp_flags or 'F' in tcp_flags or 'N' in tcp_flags)
            and packet_size < 100
            and packet_rate > 20
        ):
            return True, f"Scan attempt on port {dst_port} (Flags: {tcp_flags})"

        return False, ''
    
    def _detect_ddos(self, packet_rate: float, byte_rate: float, 
                     packet_size: int) -> Tuple[bool, str]:
        """Detect DDoS attack patterns"""
        # High packet rate with consistent sizes
        if packet_rate > 500:  # packets per second
            return True, f"Excessive packet rate: {packet_rate:.0f} pps"
        
        # Byte rate exceeding normal thresholds
        if byte_rate > 10_000_000:  # 10 Mbps
            return True, f"Excessive byte rate: {byte_rate/1_000_000:.1f} Mbps"
        
        return False, ''
    
    def _detect_syn_flood(self, tcp_flags: str, packet_rate: float, 
                         packet_size: int, syn_rate: float = 0,
                         syn_count: int = 0) -> Tuple[bool, str]:
        """Detect SYN flood attacks using multiple indicators"""
        # Method 1: High SYN-only rate from rate tracker
        if syn_rate > 10:
            return True, f"SYN Flood detected (SYN rate: {syn_rate:.0f} SYN/s, {syn_count} SYNs in window)"
        
        # Method 2: Classic detection - SYN-only flag with high packet rate
        if (
            tcp_flags == 'S'
            and packet_rate > 50
            and packet_size < 120
        ):
            return True, f"Potential SYN Flood (Rate: {packet_rate:.0f} pps)"
        
        # Method 3: Many SYN packets accumulated in the window
        if syn_count > 30 and tcp_flags == 'S':
            return True, f"SYN Flood burst detected ({syn_count} SYN packets in window)"
        
        return False, ''

    def _detect_brute_force(self, dst_port: int, packet_rate: float,
                           tcp_flags: str) -> Tuple[bool, str]:
        """Detect potential brute force attempts"""
        # Common brute force ports: SSH (22), RDP (3389), SMB (445)
        brute_ports = [22, 3389, 445, 23, 21]
        
        if dst_port in brute_ports and packet_rate > 5:
            if 'P' in tcp_flags or 'PA' in tcp_flags: # Push flag often seen in auth attempts
                return True, f"Brute force attempt on port {dst_port}"
        
        return False, ''

    def detect(self, packet_data: Dict, ml_result: Dict = None) -> DetectionResult:
        """
        Perform rule-based detection.
        Rules can OVERRIDE ML when clear attack signatures are found.
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
        syn_rate = packet_data.get('syn_rate', 0)
        syn_count = packet_data.get('syn_count', 0)
        
        # Rule 1: Port Scanning Detection
        scan_result = self._detect_port_scan(
            dst_port, packet_size, packet_rate, tcp_flags
        )
        if scan_result[0]:
            rules_triggered.append(scan_result[1])
            attack_type = 'Port Scan'
            base_confidence = max(base_confidence, 0.6)
            max_severity = 'medium'
        
        # Rule 2: DDoS Detection
        ddos_result = self._detect_ddos(packet_rate, byte_rate, packet_size)
        if ddos_result[0]:
            rules_triggered.append(ddos_result[1])
            attack_type = 'DDoS'
            base_confidence = max(base_confidence, 0.9)
            max_severity = 'critical'
        
        # Rule 3: SYN Flood Detection (enhanced with syn_rate)
        syn_result = self._detect_syn_flood(
            tcp_flags, packet_rate, packet_size,
            syn_rate=syn_rate, syn_count=syn_count
        )
        if syn_result[0]:
            rules_triggered.append(syn_result[1])
            attack_type = 'SYN Flood'
            base_confidence = max(base_confidence, 0.92)
            max_severity = 'critical'

        # Rule 4: Brute Force Detection
        brute_result = self._detect_brute_force(dst_port, packet_rate, tcp_flags)
        if brute_result[0]:
            rules_triggered.append(brute_result[1])
            attack_type = 'Brute Force'
            base_confidence = max(base_confidence, 0.7)
            max_severity = 'high'
        
        # Rule 5: ICMP Flood Detection
        icmp_result = self._detect_icmp_flood(protocol, packet_rate, packet_size)
        if icmp_result[0]:
            rules_triggered.append(icmp_result[1])
            attack_type = 'ICMP Flood'
            base_confidence = max(base_confidence, 0.8)
            max_severity = 'high'

        # Rule 6: High connection rate from single IP
        connection_count = packet_data.get('connection_count', 0)
        if connection_count > 100 and packet_rate > 30:
            if not rules_triggered:  # Only add if no other rule matched
                rules_triggered.append(
                    f"High connection rate from {src_ip}: {connection_count} connections, {packet_rate:.0f} pps"
                )
                attack_type = 'Flooding'
                base_confidence = max(base_confidence, 0.75)
                max_severity = 'high'
        
        # ===== HYBRID DECISION LOGIC =====
        # KEY FIX: Rules OVERRIDE ML when they detect clear attack patterns
        is_attack = False
        final_confidence = min(base_confidence, 1.0)
        rules_found_attack = len(rules_triggered) > 0
        
        if rules_found_attack and base_confidence >= 0.7:
            # RULES DETECTED A CLEAR ATTACK - always trust rules for these patterns
            is_attack = True
            reason = f"Rule-based detection: {', '.join(rules_triggered)}"
            final_confidence = base_confidence
            # If ML also detected an attack, combine confidence
            if ml_result and ml_result.get('is_attack', False):
                ml_attack_type = ml_result.get('attack_type', '')
                if ml_attack_type and ml_attack_type != 'Benign':
                    attack_type = ml_attack_type  # Use ML's more specific label
                final_confidence = max(base_confidence, ml_result.get('confidence', 0))
                reason = f"Hybrid detection (ML + Rules): {', '.join(rules_triggered)}"
        elif ml_result:
            ml_confidence = ml_result.get('confidence', 0.0)
            ml_is_attack = ml_result.get('is_attack', False)
            
            if ml_is_attack:
                # ML detected an attack
                is_attack = True
                attack_type = ml_result.get('attack_type', attack_type)
                final_confidence = ml_confidence
                reason = f"ML Detection: {attack_type} ({ml_confidence:.1%})"
            elif rules_found_attack:
                # ML says benign but rules found something - trust rules
                is_attack = True
                reason = f"Rule-based detection (ML override): {', '.join(rules_triggered)}"
                final_confidence = base_confidence
            else:
                # Both ML and rules say benign
                is_attack = False
                reason = "Benign traffic"
                attack_type = 'Benign'
                final_confidence = ml_confidence
        else:
            # No ML result - pure rule-based
            is_attack = rules_found_attack
            if is_attack:
                reason = f"Rule-based detection: {', '.join(rules_triggered)}"
            else:
                reason = "Normal traffic"
                attack_type = 'Benign'
        
        return DetectionResult(
            is_attack=is_attack,
            attack_type=attack_type,
            severity=max_severity if is_attack else 'low',
            confidence=final_confidence,
            reason=reason,
            rules_triggered=rules_triggered,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
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
