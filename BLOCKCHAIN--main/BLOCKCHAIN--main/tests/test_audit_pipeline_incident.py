import sys
from pathlib import Path
import unittest
import asyncio

MODULE_DIR = Path(__file__).resolve().parent.parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from agents.pipeline import AccessAuditPipeline


class TestAccessAuditPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = AccessAuditPipeline(poll_interval=10, events_per_cycle=5)

    def test_pipeline_cycle_execution(self):
        anomalies = asyncio.run(self.pipeline.run_cycle())
        stats = self.pipeline.get_stats()

        self.assertEqual(stats["cycles_run"], 1)
        self.assertGreaterEqual(stats["events_processed"], 5)
        self.assertTrue(stats["audit_records_submitted"] >= 5)


if __name__ == "__main__":
    unittest.main()
