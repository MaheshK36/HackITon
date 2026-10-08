from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, List
from ingestion.csv_reader import CSVFlowReader

class BaseTelemetryStream(ABC):
    """Pluggable base class for all ingestion readers (CSV, PCAP, Zeek, Suricata)."""
    @abstractmethod
    def get_records(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def stream(self) -> Iterator[Dict[str, Any]]:
        pass

class CSVTelemetryStream(BaseTelemetryStream):
    def __init__(self, csv_file_path: str):
        self.reader = CSVFlowReader(csv_file_path)

    def get_records(self) -> List[Dict[str, Any]]:
        return self.reader.read_all()

    def stream(self) -> Iterator[Dict[str, Any]]:
        return self.reader.stream_records()

    @property
    def start_time(self) -> float:
        return self.reader.start_time

    @property
    def end_time(self) -> float:
        return self.reader.end_time

class PCAPTelemetryStream(BaseTelemetryStream):
    def __init__(self, pcap_file_path: str):
        from ingestion.pcap_reader import PCAPFlowReader
        self.reader = PCAPFlowReader(pcap_file_path)

    def get_records(self) -> List[Dict[str, Any]]:
        return self.reader.read_all()

    def stream(self) -> Iterator[Dict[str, Any]]:
        return self.reader.stream_records()
