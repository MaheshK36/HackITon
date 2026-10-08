from typing import List, Dict, Any, Generator
from collections import deque
from preprocessing.flow_extractor import FlowRecord
from preprocessing.feature_engineering import extract_window_features, extract_per_host_features

class TimeWindow:
    """Represents a discrete time window containing flows and extracted features."""
    def __init__(self, start_time: float, end_time: float, flows: List[FlowRecord]):
        self.start_time = start_time
        self.end_time = end_time
        self.flows = flows
        self.duration = end_time - start_time
        self.features = extract_window_features(flows, self.duration)
        self.host_features = extract_per_host_features(flows, self.duration)

class WindowEngine:
    """Chunks flow streams into discrete time windows driven by dataset timestamps."""
    def __init__(self, window_size_sec: float = 10.0, window_step_sec: float = 5.0):
        self.window_size = window_size_sec
        self.window_step = window_step_sec

    def process_records(self, raw_records: List[Dict[str, Any]]) -> List[TimeWindow]:
        if not raw_records:
            return []

        flows = [FlowRecord.from_dict(r) for r in raw_records]
        flows.sort(key=lambda f: f.timestamp)

        min_t = flows[0].timestamp
        max_t = flows[-1].timestamp

        windows = []
        curr_start = min_t

        while curr_start <= max_t:
            curr_end = curr_start + self.window_size
            w_flows = [f for f in flows if curr_start <= f.timestamp < curr_end]
            if w_flows:
                windows.append(TimeWindow(curr_start, curr_end, w_flows))
            curr_start += self.window_step

        return windows

class RollingStateBuffer:
    """Buffers the last N window states to condition sequence predictions."""
    def __init__(self, maxlen: int = 5):
        self.maxlen = maxlen
        self.buffer = deque(maxlen=maxlen)

    def append(self, window_state: Dict[str, Any]):
        self.buffer.append(window_state)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self.buffer)

    def is_ready(self) -> bool:
        return len(self.buffer) > 0

    def clear(self):
        self.buffer.clear()
