import sys
import unittest
from pathlib import Path
import pandas as pd

DT2_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = DT2_DIR.parent
for p in [str(DT2_DIR), str(ROOT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from ingestion.stream import CSVTelemetryStream
from preprocessing.windowing import WindowEngine
from prediction.inference import InferencePipeline
from digital_twin.state_manager import DigitalTwinStateManager
from evaluation.evaluator import SystemEvaluator

class TestCyberattackDigitalTwinPipeline(unittest.TestCase):

    def setUp(self):
        data_dir = ROOT_DIR / "data" / "raw"
        if not (data_dir / "scenario_a_recon_bruteforce_exfil.csv").exists():
            data_dir = DT2_DIR / "data" / "raw"

        self.scenario_a_path = str(data_dir / "scenario_a_recon_bruteforce_exfil.csv")
        self.scenario_b_path = str(data_dir / "scenario_b_dos_command_exec.csv")
        self.benign_path = str(data_dir / "scenario_c_benign.csv")
        self.engine = WindowEngine(window_size_sec=10.0, window_step_sec=5.0)

    def test_criterion_1_swapping_dataset_changes_behavior(self):
        """Acceptance Criterion 1: Swapping input PCAP/CSV changes detected and predicted behavior."""
        # Process Scenario A
        stream_a = CSVTelemetryStream(self.scenario_a_path)
        windows_a = self.engine.process_records(stream_a.get_records())
        pipeline_a = InferencePipeline(model_type="baseline")
        results_a = [pipeline_a.process_window(w) for w in windows_a]
        labels_a = [r["raw_detected_label"] for r in results_a]

        # Process Scenario B
        stream_b = CSVTelemetryStream(self.scenario_b_path)
        windows_b = self.engine.process_records(stream_b.get_records())
        pipeline_b = InferencePipeline(model_type="baseline")
        results_b = [pipeline_b.process_window(w) for w in windows_b]
        labels_b = [r["raw_detected_label"] for r in results_b]

        self.assertNotEqual(labels_a, labels_b, "Changing input dataset must change detected progression.")
        self.assertIn("BruteForce", labels_a, "Scenario A should detect BruteForce.")
        self.assertIn("DoS", labels_b, "Scenario B should detect DoS.")

    def test_criterion_2_benign_traffic_no_attack(self):
        """Acceptance Criterion 2: Removing attack traffic stops UI attack progression."""
        stream_c = CSVTelemetryStream(self.benign_path)
        windows_c = self.engine.process_records(stream_c.get_records())
        pipeline = InferencePipeline(model_type="baseline")

        for w in windows_c:
            out = pipeline.process_window(w)
            self.assertEqual(out["current_detection"]["state"], "BENIGN", "Benign traffic must fall back to BENIGN state.")

    def test_criterion_3_traceable_inference(self):
        """Acceptance Criterion 3 & 8: Every prediction has top feature attribution explanation."""
        stream_a = CSVTelemetryStream(self.scenario_a_path)
        windows_a = self.engine.process_records(stream_a.get_records())
        pipeline = InferencePipeline(model_type="baseline")
        out = pipeline.process_window(windows_a[0])

        self.assertIn("feature_explanations", out)
        self.assertGreater(len(out["feature_explanations"]), 0, "Feature explanations ('Why') must be present.")

    def test_criterion_5_digital_twin_deterministic_update(self):
        """Acceptance Criterion 5: Digital Twin graph updates ONLY via current window flows and model outputs."""
        stream_a = CSVTelemetryStream(self.scenario_a_path)
        windows_a = self.engine.process_records(stream_a.get_records())
        pipeline = InferencePipeline(model_type="baseline")
        out = pipeline.process_window(windows_a[0])

        state_mgr = DigitalTwinStateManager()
        state_mgr.update_window_state(
            window_flows=windows_a[0].flows,
            current_detection=out["current_detection"],
            per_host_detections=out["per_host_detections"],
            predictions=out["next_predictions"],
            window_timestamp=windows_a[0].end_time
        )

        self.assertGreater(state_mgr.graph.number_of_nodes(), 0)
        self.assertGreater(state_mgr.graph.number_of_edges(), 0)

    def test_criterion_11_swappable_predictor_interface(self):
        """Acceptance Criterion 11 & 12: Predictor model is swappable behind one interface."""
        pipeline = InferencePipeline(model_type="baseline")
        self.assertIn("Baseline", pipeline.predictor.model_name)

        pipeline.switch_model("deep_learning")
        self.assertIn("Deep Learning", pipeline.predictor.model_name)

if __name__ == "__main__":
    unittest.main()
