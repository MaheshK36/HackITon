"""
test_end_to_end.py - Comprehensive End-to-End System Verification Test Suite

Verifies:
  1. Feature vector normalization
  2. AttackWorldModel tensor predictions
  3. Digital Twin autoregressive rollout
  4. Twin fidelity benchmarking
  5. Cryptographic audit log hash chaining & tamper verification
  6. FastAPI REST endpoints (Health, Audit, Twin State, Ingest, Model Info, Replay, Frontend)
  7. Replay telemetry pipeline & Digital Twin graph updates
"""

import unittest
import numpy as np
import torch

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = ROOT.parent.parent
for p in [str(ROOT), str(REPO_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.adapters.normalization import normalize_flow_dict, normalize_access_event
from models.attack_world_model import AttackWorldModel, ModelConfig
from models.graph_encoder import GraphEncoder
from digital_twin.state import NetworkGraphState
from digital_twin.twin_engine import DigitalTwinEngine
from digital_twin.validation import validate_twin_fidelity
from blockchain.audit_agent import BlockchainAuditAgent
from fastapi.testclient import TestClient
from backend.server import app


class TestUnifiedCybersecuritySystem(unittest.TestCase):

    def setUp(self):
        self.model_cfg = ModelConfig(input_size=42, hidden_size=64, num_stages=7)
        self.model = AttackWorldModel(self.model_cfg)
        self.model.eval()
        self.twin = DigitalTwinEngine(model=self.model)
        self.client = TestClient(app)

    def test_01_feature_normalization(self):
        raw_flow = {
            "Flow Duration": 125000,
            "Total Fwd Packets": 45,
            "SYN Flag Count": 1,
            "bytes_per_sec": 1024.5,
        }
        vec = normalize_flow_dict(raw_flow)
        self.assertEqual(len(vec), 42)
        self.assertIsInstance(vec, np.ndarray)

    def test_02_model_prediction(self):
        sample_input = np.random.randn(42).astype(np.float32)
        res = self.model.predict(sample_input)
        self.assertIn("next_state_pred", res)
        self.assertIn("infiltration_prob", res)
        self.assertIn("predicted_stage", res)
        self.assertEqual(len(res["next_state_pred"]), 42)

    def test_03_digital_twin_rollout(self):
        seed_state = NetworkGraphState()
        trajectory = self.twin.rollout(seed_state=seed_state, k_steps=5, stop_on_terminal=False)
        self.assertEqual(len(trajectory), 5)
        self.assertIn("target_ip", trajectory[0])
        self.assertIn("predicted_stage", trajectory[0])

    def test_04_twin_fidelity_benchmark(self):
        seed_state = NetworkGraphState()
        gt_sequence = [seed_state.clone() for _ in range(4)]
        report = validate_twin_fidelity(twin=self.twin, ground_truth_sequences=[gt_sequence], k_steps=3)
        self.assertIn("overall_state_mse", report)
        self.assertIn("horizon_drift_curve_mse", report)

    def test_05_blockchain_hash_verification(self):
        agent = BlockchainAuditAgent()
        evt = {"user_id": "test_user", "event_type": "login", "ip_address": "192.168.1.50"}
        rec = agent.record_event(evt)
        v_res = agent.verify_hash(rec.event_id, rec.log_hash)
        self.assertTrue(v_res["verified"])
        self.assertEqual(v_res["status"], "VALID_TAMPER_FREE")

    def test_06_fastapi_endpoints(self):
        # 1. Health check
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "online")

        # 2. Audit logs
        res = self.client.get("/api/audit-logs")
        self.assertEqual(res.status_code, 200)

        # 3. Digital Twin state
        res = self.client.get("/api/v1/twin/state")
        self.assertEqual(res.status_code, 200)

        # 4. CyberSeer forecast
        res = self.client.post("/api/v1/forecast/propagation", json={"steps": 3})
        self.assertEqual(res.status_code, 200)

        # 5. Model info endpoint
        res = self.client.get("/api/v1/model/info")
        self.assertEqual(res.status_code, 200)
        self.assertIn("is_model_trained", res.json())
        self.assertIn("model_version", res.json())

        # 6. Valid canonical event runs through validation, normalization, graph, risk and audit.
        res = self.client.post("/api/v1/flows/ingest", json={
            "source_ip": "198.51.100.10", "destination_ip": "10.0.0.20",
            "destination_port": 22, "protocol": "tcp", "packets": 2,
            "duration": 0.1, "metadata": {"syn_flag_count": 1, "port_scan": True},
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn(res.json()["decision"]["inference_mode"], ["TRAINED_MODEL_INFERENCE", "HEURISTIC_FALLBACK"])

        # The shared digital twin exposes the ingested destination host.
        state = self.client.get("/api/v1/twin/state").json()
        self.assertTrue(any(node["ip_address"] == "10.0.0.20" for node in state["nodes"]))

        # Malformed addresses are rejected by the typed public API.
        bad = self.client.post("/api/v1/flows/ingest", json={"source_ip": "not-an-ip", "destination_ip": "10.0.0.1"})
        self.assertEqual(bad.status_code, 422)

        # 7. Static frontend serving
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)

    def test_07_replay_pipeline(self):
        # 1. Scenarios listing
        res = self.client.get("/api/v1/replay/scenarios")
        self.assertEqual(res.status_code, 200)
        scenarios = res.json()
        self.assertIsInstance(scenarios, list)

        # 2. Replay execution
        res = self.client.post("/api/v1/replay/start?scenario=scenario_a&max_events=10")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "replayed")
        self.assertGreaterEqual(data["replayed_events_count"], 1)

        # Verify nodes exist in digital twin
        nodes = data["platform_snapshot"]["nodes"]
        self.assertGreater(len(nodes), 0)


if __name__ == "__main__":
    unittest.main()
