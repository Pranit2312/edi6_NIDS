from collections import defaultdict
from datetime import datetime
import threading


class StatsManager:
    def __init__(self):
        self.lock = threading.Lock()

        self.total_packets = 0
        self.total_bytes = 0

        self.protocol_counts = defaultdict(int)
        self.ip_counts = defaultdict(int)
        self.alert_counts = defaultdict(int)

        self.start_time = datetime.now()

    def update_packet(self, packet_data):
        with self.lock:
            self.total_packets += 1

            size = packet_data.get('size', 0)
            self.total_bytes += size

            protocol = packet_data.get('protocol', 'UNKNOWN')
            self.protocol_counts[protocol] += 1

            src_ip = packet_data.get('src_ip', 'unknown')
            self.ip_counts[src_ip] += 1

    def update_alert(self, alert_type):
        with self.lock:
            self.alert_counts[alert_type] += 1

    def get_stats(self):
        with self.lock:
            return {
                'total_packets': self.total_packets,
                'total_bytes': self.total_bytes,
                'protocol_distribution': dict(self.protocol_counts),
                'top_ips': dict(sorted(
                    self.ip_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]),
                'alerts': dict(self.alert_counts)
            }


stats_manager = StatsManager()