import pandas as pd
from typing import Iterator, Dict, Any, List

class CSVFlowReader:
    """Reads flow data from CSV files sorted chronologically by timestamp."""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = pd.read_csv(file_path)
        
        # Ensure timestamp column is numeric POSIX timestamp
        if "timestamp" in self.df.columns:
            self.df["timestamp"] = pd.to_numeric(self.df["timestamp"], errors="coerce")
            self.df = self.df.sort_values("timestamp").reset_index(drop=True)
        else:
            raise ValueError(f"CSV file {file_path} must contain a 'timestamp' column.")

    def read_all(self) -> List[Dict[str, Any]]:
        return self.df.to_dict(orient="records")

    def stream_records(self) -> Iterator[Dict[str, Any]]:
        for record in self.df.to_dict(orient="records"):
            yield record

    @property
    def start_time(self) -> float:
        return float(self.df["timestamp"].min()) if not self.df.empty else 0.0

    @property
    def end_time(self) -> float:
        return float(self.df["timestamp"].max()) if not self.df.empty else 0.0
