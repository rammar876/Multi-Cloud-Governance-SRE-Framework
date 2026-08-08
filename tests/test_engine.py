import unittest

from mcgsre.engine import evaluate, validate_catalog


CATALOG = {
    "controls": [{
        "id": "TEST-1",
        "title": "Test control",
        "severity": "critical",
        "expected": {"operator": "eq", "value": True},
        "provider_mappings": {"aws": "native control"},
        "remediation": "Fix it",
    }]
}


class EvaluateTests(unittest.TestCase):
    def test_reports_drift_and_weighted_score(self):
        observations = {"observations": [
            {"provider": "aws", "resource_id": "one", "control_id": "TEST-1", "actual": True},
            {"provider": "azure", "resource_id": "two", "control_id": "TEST-1", "actual": False},
        ]}
        report = evaluate(CATALOG, observations)
        self.assertEqual(report["summary"]["drifted"], 1)
        self.assertEqual(report["summary"]["weighted_compliance_score"], 50.0)
        self.assertEqual(report["results"][1]["remediation"], "Fix it")

    def test_rejects_unknown_control(self):
        observations = {"observations": [
            {"provider": "aws", "resource_id": "one", "control_id": "UNKNOWN", "actual": True}
        ]}
        with self.assertRaisesRegex(ValueError, "unknown control"):
            evaluate(CATALOG, observations)

    def test_rejects_duplicate_control_ids(self):
        catalog = {"controls": CATALOG["controls"] * 2}
        with self.assertRaisesRegex(ValueError, "duplicate control"):
            validate_catalog(catalog)


if __name__ == "__main__":
    unittest.main()
