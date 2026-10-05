import json, unittest
from pathlib import Path
from n8n_workflow_doctor.cli import lint, main

EX = Path(__file__).resolve().parent.parent / "examples"

class T(unittest.TestCase):
    def test_messy_flags(self):
        fs, score = lint(json.loads((EX / "messy-lead-workflow.json").read_text()))
        rules = {f["rule"] for f in fs}
        for r in ("hardcoded-secret", "no-error-workflow", "http-no-retry", "default-node-name",
                  "disabled-node", "orphan-node", "open-webhook"):
            self.assertIn(r, rules)
        self.assertLess(score, 60)

    def test_clean_is_clean(self):
        fs, score = lint(json.loads((EX / "clean-lead-workflow.json").read_text()))
        self.assertEqual(fs, [])
        self.assertEqual(score, 100)

    def test_exit_codes(self):
        self.assertEqual(main([str(EX / "clean-lead-workflow.json")]), 0)
        self.assertEqual(main([str(EX / "messy-lead-workflow.json")]), 1)

if __name__ == "__main__":
    unittest.main()
