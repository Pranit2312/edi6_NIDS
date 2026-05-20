"""
Professional Flow-Based Feature Extractor
CICIDS2017-Compatible Realtime Feature Engineering
"""

import time
from typing import Dict, List, Tuple
import numpy as np


class FeatureExtractor:
    """
    Professional flow-based feature extractor.
    Compatible with CICIDS2017-style features.
    """

    FEATURE_NAMES = [
        'destination_port',
        'flow_duration',
        'total_fwd_packets',
        'total_backward_packets',
        'total_length_of_fwd_packets',
        'total_length_of_bwd_packets',
        'fwd_packet_length_max',
        'fwd_packet_length_min',
        'fwd_packet_length_mean',
        'bwd_packet_length_max',
        'bwd_packet_length_min',
        'bwd_packet_length_mean',
        'flow_bytes_per_sec',
        'flow_packets_per_sec',
        'flow_iat_mean',
        'flow_iat_std',
        'fwd_iat_mean',
        'bwd_iat_mean',
        'fin_flag_count',
        'syn_flag_count',
        'rst_flag_count',
        'psh_flag_count',
        'ack_flag_count',
        'urg_flag_count',
        'average_packet_size',
        'packet_length_variance',
        'idle_mean',
        'active_mean'
    ]

    @staticmethod
    def safe_mean(values):
        return float(np.mean(values)) if values else 0.0

    @staticmethod
    def safe_std(values):
        return float(np.std(values)) if values else 0.0

    @staticmethod
    def safe_max(values):
        return float(np.max(values)) if values else 0.0

    @staticmethod
    def safe_min(values):
        return float(np.min(values)) if values else 0.0

    @staticmethod
    def calculate_iat(timestamps):
        if len(timestamps) < 2:
            return []
        return np.diff(sorted(timestamps))

    @staticmethod
    def count_tcp_flags(packets):
        flags = {
            'FIN': 0,
            'SYN': 0,
            'RST': 0,
            'PSH': 0,
            'ACK': 0,
            'URG': 0
        }

        for packet in packets:
            tcp_flags = str(packet.get('tcp_flags', '')).upper()

            if 'F' in tcp_flags:
                flags['FIN'] += 1
            if 'S' in tcp_flags:
                flags['SYN'] += 1
            if 'R' in tcp_flags:
                flags['RST'] += 1
            if 'P' in tcp_flags:
                flags['PSH'] += 1
            if 'A' in tcp_flags:
                flags['ACK'] += 1
            if 'U' in tcp_flags:
                flags['URG'] += 1

        return flags

    @staticmethod
    def extract_flow_features(flow_packets: List[Dict]) -> Tuple[List[float], Dict]:
        """
        Extract CICIDS-style flow features.
        """

        if not flow_packets:
            return [0.0] * len(FeatureExtractor.FEATURE_NAMES), {}

        try:
            timestamps = []

            for p in flow_packets:

                ts = p.get('timestamp', time.time())

                try:

                    # Handle ISO datetime string
                    if isinstance(ts, str):
                        from datetime import datetime
                        ts = datetime.fromisoformat(ts).timestamp()

                    timestamps.append(float(ts))

                except Exception:
                    timestamps.append(time.time())

            packet_sizes = [
                int(p.get('packet_size', 0))
                for p in flow_packets
            ]

            src_ip = flow_packets[0].get('src_ip', '')
            dst_port = int(flow_packets[0].get('dst_port', 0))

            fwd_packets = [
                p for p in flow_packets
                if p.get('src_ip') == src_ip
            ]

            bwd_packets = [
                p for p in flow_packets
                if p.get('src_ip') != src_ip
            ]

            fwd_sizes = [
                int(p.get('packet_size', 0))
                for p in fwd_packets
            ]

            bwd_sizes = [
                int(p.get('packet_size', 0))
                for p in bwd_packets
            ]

            flow_duration = max(timestamps) - min(timestamps)
            flow_duration = max(flow_duration, 0.000001)

            total_packets = len(flow_packets)
            total_bytes = sum(packet_sizes)

            flow_iat = FeatureExtractor.calculate_iat(timestamps)

            fwd_timestamps = []

            for p in fwd_packets:

                ts = p.get('timestamp', time.time())

                try:

                    if isinstance(ts, str):
                        from datetime import datetime
                        ts = datetime.fromisoformat(ts).timestamp()

                    fwd_timestamps.append(float(ts))

                except Exception:
                    fwd_timestamps.append(time.time())

            bwd_timestamps = []

            for p in bwd_packets:

                ts = p.get('timestamp', time.time())

                try:

                    if isinstance(ts, str):
                        from datetime import datetime
                        ts = datetime.fromisoformat(ts).timestamp()

                    bwd_timestamps.append(float(ts))

                except Exception:
                    bwd_timestamps.append(time.time())

            fwd_iat = FeatureExtractor.calculate_iat(fwd_timestamps)
            bwd_iat = FeatureExtractor.calculate_iat(bwd_timestamps)

            tcp_flags = FeatureExtractor.count_tcp_flags(flow_packets)

            flow_bytes_per_sec = total_bytes / flow_duration
            flow_packets_per_sec = total_packets / flow_duration

            avg_packet_size = FeatureExtractor.safe_mean(packet_sizes)
            packet_variance = FeatureExtractor.safe_std(packet_sizes)

            active_times = flow_iat
            idle_times = [
                x for x in flow_iat
                if x > 1.0
            ]

            features = [
                float(dst_port),
                float(flow_duration),

                float(len(fwd_packets)),
                float(len(bwd_packets)),

                float(sum(fwd_sizes)),
                float(sum(bwd_sizes)),

                FeatureExtractor.safe_max(fwd_sizes),
                FeatureExtractor.safe_min(fwd_sizes),
                FeatureExtractor.safe_mean(fwd_sizes),

                FeatureExtractor.safe_max(bwd_sizes),
                FeatureExtractor.safe_min(bwd_sizes),
                FeatureExtractor.safe_mean(bwd_sizes),

                float(flow_bytes_per_sec),
                float(flow_packets_per_sec),

                FeatureExtractor.safe_mean(flow_iat),
                FeatureExtractor.safe_std(flow_iat),

                FeatureExtractor.safe_mean(fwd_iat),
                FeatureExtractor.safe_mean(bwd_iat),

                float(tcp_flags['FIN']),
                float(tcp_flags['SYN']),
                float(tcp_flags['RST']),
                float(tcp_flags['PSH']),
                float(tcp_flags['ACK']),
                float(tcp_flags['URG']),

                float(avg_packet_size),
                float(packet_variance),

                FeatureExtractor.safe_mean(idle_times),
                FeatureExtractor.safe_mean(active_times)
            ]

            metadata = {
                'src_ip': flow_packets[0].get('src_ip'),
                'dst_ip': flow_packets[0].get('dst_ip'),
                'protocol': flow_packets[0].get('protocol'),
                'packet_count': total_packets,
                'flow_duration': flow_duration
            }

            return features, metadata

        except Exception as e:
            print(f"[FeatureExtractor ERROR] {e}")
            return [0.0] * len(FeatureExtractor.FEATURE_NAMES), {}

    @staticmethod
    def normalize_features(features: List[float], scaler=None):
        """
        Normalize feature vector using trained scaler.
        """

        features_array = np.array(features).reshape(1, -1)

        if scaler is not None:
            return scaler.transform(features_array)[0]

        return features_array[0]


class PacketAggregator:
    """
    Professional flow aggregator.
    """

    def __init__(self, timeout: float = 120.0):
        self.timeout = timeout
        self.flows = {}

    def get_flow_key(self, packet: Dict) -> str:

        src_ip = packet.get('src_ip', '')
        dst_ip = packet.get('dst_ip', '')
        src_port = packet.get('src_port', 0)
        dst_port = packet.get('dst_port', 0)
        protocol = packet.get('protocol', 'TCP')

        endpoints = sorted([
            f"{src_ip}:{src_port}",
            f"{dst_ip}:{dst_port}"
        ])

        return f"{protocol}-{endpoints[0]}-{endpoints[1]}"

    def add_packet(self, packet: Dict) -> str:

        flow_key = self.get_flow_key(packet)

        if flow_key not in self.flows:
            self.flows[flow_key] = {
                'packets': [],
                'created_at': time.time(),
                'last_seen': time.time()
            }

        self.flows[flow_key]['packets'].append(packet)
        self.flows[flow_key]['last_seen'] = time.time()

        return flow_key

    def get_flow(self, flow_key: str) -> List[Dict]:

        if flow_key in self.flows:
            return self.flows[flow_key]['packets']

        return []

    def cleanup_old_flows(self):

        current_time = time.time()

        expired = []

        for flow_key, flow_data in self.flows.items():

            if current_time - flow_data['last_seen'] > self.timeout:
                expired.append(flow_key)

        for flow_key in expired:
            del self.flows[flow_key]

    def get_all_flows(self):

        return self.flows