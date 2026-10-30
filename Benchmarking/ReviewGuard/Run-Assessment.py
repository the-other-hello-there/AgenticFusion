"""Reproduce control tests, local capability probes and explicitly simulated ledgers."""
import argparse
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "AgenticFusionTemplate/.agents/review_guard"))
from adapters import probe
from core import Hold
from supervisor import Supervisor

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path)
args = parser.parse_args()
spec = importlib.util.spec_from_file_location("review_tests", ROOT / "Benchmarking/Test-ReviewGuard.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
log = io.StringIO()
result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
examples = []
for scenario in ("unfamiliar", "revise", "fabricated_approval"):
    with tempfile.TemporaryDirectory(prefix="AgenticFusion-review-assessment-") as temporary:
        folder = Path(temporary)
        workspace = folder / "workspace"
        workspace.mkdir()
        fixture = folder / "trusted-fixture.py"
        shutil.copyfile(ROOT / "Benchmarking/ReviewGuard/runtime_fixture.py", fixture)
        policy = json.loads((ROOT / "AgenticFusionTemplate/Review-Policy.json").read_text())
        policy.update(primary_command=[sys.executable, str(fixture), "primary", scenario],
                      reviewer_command=[sys.executable, str(fixture), "review", "normal"],
                      reviewer_enforces_charge_ceiling=True)
        controller = Supervisor(workspace, folder / "state", policy, "Write exactly eight entries.", agent="custom")
        try:
            controller.run()
            status = "cleared"
        except Hold:
            status = "held"
        examples.append({"scenario": scenario, "status": status,
                         "simulated_usd_ledger": controller.engine.ledger.report()})
report = {"assessment_kind": "deterministic_control_tests_not_live_AI_detection",
          "tests_run": result.testsRun, "tests_passed": result.wasSuccessful(),
          "failures": [name.id() for name, _ in result.failures + result.errors],
          "runtime_capability_probe": probe(), "examples": examples,
          "remote_primary_or_reviewer_model_calls": 0,
          "actual_reviewer_model_charges_usd": "0",
          "live_AI_detection_accuracy": "not measured",
          "native_paid_review_ready": False}
payload = json.dumps(report, indent=2) + "\n"
if args.output:
    args.output.write_text(payload, encoding="utf-8")
else:
    print(payload)
if not result.wasSuccessful():
    print(log.getvalue(), file=sys.stderr)
    raise SystemExit(1)
