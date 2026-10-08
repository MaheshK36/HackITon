import sys
from pathlib import Path
import unittest
import hashlib
import json

MODULE_DIR = Path(__file__).resolve().parent.parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from agents.anomaly.anomaly_agent import AnomalyFinding


class TestHashIntegrity(unittest.TestCase):
    def test_sha256_hash_deterministic(self):
        finding1 = AnomalyFinding(
            finding_id="ANOM-001",
            anomaly_type="failed_login_burst",
            user_id="usr_alice",
            timestamp="2026-08-30T12:00:00Z",
            confidence=0.92,
            description="Failed login burst detected",
            event_ids=["EVT-1", "EVT-2", "EVT-3"]
        )

        finding2 = AnomalyFinding(
            finding_id="ANOM-001",
            anomaly_type="failed_login_burst",
            user_id="usr_alice",
            timestamp="2026-08-30T12:00:00Z",
            confidence=0.92,
            description="Failed login burst detected",
            event_ids=["EVT-1", "EVT-2", "EVT-3"]
        )

        hash1 = finding1.sha256_hash()
        hash2 = finding2.sha256_hash()

        self.assertEqual(len(hash1), 64)
        self.assertEqual(hash1, hash2)

    def test_tamper_evidence(self):
        finding1 = AnomalyFinding(
            finding_id="ANOM-001",
            anomaly_type="failed_login_burst",
            user_id="usr_alice",
            timestamp="2026-08-30T12:00:00Z",
            confidence=0.92,
            description="Failed login burst detected",
            event_ids=["EVT-1", "EVT-2"]
        )

        # Modify user_id
        finding2 = AnomalyFinding(
            finding_id="ANOM-001",
            anomaly_type="failed_login_burst",
            user_id="usr_hacker",
            timestamp="2026-08-30T12:00:00Z",
            confidence=0.92,
            description="Failed login burst detected",
            event_ids=["EVT-1", "EVT-2"]
        )

        self.assertNotEqual(finding1.sha256_hash(), finding2.sha256_hash())


if __name__ == "__main__":
    unittest.main()
