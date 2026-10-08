import sys
from pathlib import Path
import unittest

MODULE_DIR = Path(__file__).resolve().parent.parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from agents.collector.collector_agent import CollectorAgent
from agents.anomaly.anomaly_agent import AnomalyAgent, AnomalyFinding


class TestAccessAnomalyDetection(unittest.TestCase):
    def setUp(self):
        self.collector = CollectorAgent()
        self.detector = AnomalyAgent()

    def test_event_ingestion(self):
        evt = self.collector.add_event({
            "user_id": "usr_alice",
            "event_type": "login",
            "ip_address": "192.168.1.100",
            "location": "US-East",
            "device_info": "Chrome/MacOS"
        })
        self.assertEqual(evt["user_id"], "usr_alice")
        self.assertEqual(evt["event_type"], "login")

    def test_normal_events_no_anomaly(self):
        events = [
            {
                "user_id": "usr_normal",
                "event_type": "login",
                "ip_address": "192.168.1.50",
                "location": "US-East",
                "device_info": "Chrome/Windows",
                "status": "success"
            }
            for _ in range(2)
        ]
        anomalies = self.detector.analyze_events(events)
        self.assertEqual(len(anomalies), 0)

    def test_burst_failed_logins_anomaly(self):
        # Ingest burst of failed logins from suspicious geo
        events = [
            {
                "event_id": f"EVT-FAIL-{i}",
                "user_id": "usr_hacker",
                "event_type": "failed_login",
                "ip_address": "198.51.100.5",
                "location": "RU-Moscow",
                "device_info": "Automated-Script-v1",
                "status": "failed"
            }
            for i in range(10)
        ]

        # Add normal events for context
        for name in ["usr_bob", "usr_charlie", "usr_dave", "usr_eve"]:
            events.append({
                "event_id": f"EVT-NORM-{name}",
                "user_id": name,
                "event_type": "login",
                "ip_address": "192.168.1.10",
                "location": "US-West",
                "device_info": "Firefox/Windows",
                "status": "success"
            })

        anomalies = self.detector.analyze_events(events)
        self.assertTrue(len(anomalies) >= 1)
        hacker_anom = [a for a in anomalies if a.user_id == "usr_hacker"][0]
        self.assertTrue(hacker_anom.confidence >= 0.80)
        self.assertTrue(len(hacker_anom.methods_agreed) >= 2)
        self.assertIn("rule_heuristics", hacker_anom.methods_agreed)


if __name__ == "__main__":
    unittest.main()
