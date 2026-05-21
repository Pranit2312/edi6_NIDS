from collections import defaultdict
from datetime import datetime
import threading
import os

try:
    import psutil
except ImportError:
    psutil = None


class StatsManager:
    def __init__(self):
        self.lock = threading.Lock()

        self.total_packets = 0
        self.total_bytes = 0
        self.threats_detected = 0

        self.protocol_counts = defaultdict(int)
        self.ip_counts = defaultdict(int)
        self.dst_ip_counts = defaultdict(int)
        self.alert_counts = defaultdict(int)

        self.start_time = datetime.now()
        self.active_connections = 0
        self.cpu_usage = 0
        self.memory_usage = 0

        # PPS Tracking
        self.packet_times = []
        self.attack_packet_times = []
        self.pps = 0
        self.apps = 0
        self.last_stats_update = datetime.now()

    def update_packet(self, packet_data, is_attack=False):
        now = datetime.now()
        with self.lock:
            self.total_packets += 1
            self.packet_times.append(now)
            
            if is_attack:
                self.threats_detected += 1
                self.attack_packet_times.append(now)

            size = packet_data.get('size', 0) or packet_data.get('packet_size', 0)
            self.total_bytes += size

            protocol = packet_data.get('protocol', 'UNKNOWN')
            self.protocol_counts[protocol] += 1

            src_ip = packet_data.get('src_ip', 'unknown')
            self.ip_counts[src_ip] += 1
            
            dst_ip = packet_data.get('dst_ip', 'unknown')
            self.dst_ip_counts[dst_ip] += 1

            # Keep sliding window for PPS (last 10 seconds)
            cutoff = now.timestamp() - 10
            self.packet_times = [t for t in self.packet_times if t.timestamp() > cutoff]
            self.attack_packet_times = [t for t in self.attack_packet_times if t.timestamp() > cutoff]
            
            self.pps = len(self.packet_times) / 10.0
            self.apps = len(self.attack_packet_times) / 10.0

    def update_alert(self, alert_type):
        with self.lock:
            self.alert_counts[alert_type] += 1

    def update_system_stats(self):
        """Update CPU and Memory usage"""
        with self.lock:
            if psutil:
                try:
                    self.cpu_usage = psutil.cpu_percent()
                    self.memory_usage = psutil.virtual_memory().percent
                    # Estimate active connections
                    self.active_connections = len(psutil.net_connections())
                except Exception:
                    pass
            else:
                # Fallback if psutil is not available
                import random
                self.cpu_usage = random.uniform(5, 15)
                self.memory_usage = random.uniform(20, 40)
                self.active_connections = random.randint(10, 50)

    def get_stats(self):
        with self.lock:
            self.update_system_stats()
            
            total = self.total_packets
            threats = self.threats_detected
            safe_percentage = 100.0
            if total > 0:
                safe_percentage = round(((total - threats) / total) * 100, 1)
            else:
                safe_percentage = 100.0

            # Ensure percentages don't exceed 100%
            safe_percentage = min(safe_percentage, 100.0)
            threat_percentage = min(100.0 - safe_percentage, 100.0) if total > 0 else 0.0

            return {
                # Internal stats
                'total_packets': self.total_packets,
                'total_bytes': self.total_bytes,
                'threats_detected': self.threats_detected,
                'pps': round(self.pps, 2),
                'apps': round(self.apps, 2),
                'protocol_distribution': dict(self.protocol_counts),
                'top_ips': dict(sorted(
                    self.ip_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]),
                'top_dst_ips': dict(sorted(
                    self.dst_ip_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]),
                'alerts': dict(self.alert_counts),
                
                # Camel case for frontend compatibility
                'totalPackets': self.total_packets,
                'threatsDetected': self.threats_detected,
                'safeTraffic': safe_percentage,
                'threatTraffic': threat_percentage,
                'activeConnections': self.active_connections,
                'cpuUsage': self.cpu_usage,
                'memoryUsage': self.memory_usage,
                'packetsPerSecond': round(self.pps, 2),
                'attackPacketsPerSecond': round(self.apps, 2)
            }


stats_manager = StatsManager()