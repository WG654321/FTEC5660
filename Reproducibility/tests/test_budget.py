import importlib.util
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('runner', Path(__file__).resolve().parents[1] / 'scripts/run_experiment.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class BudgetTests(unittest.TestCase):
    def test_settlement_and_unknown_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            old = runner.ROOT
            runner.ROOT = Path(directory)
            try:
                meter = runner.Meter(2,8,5)
                reservation = meter.reserve('hello', 100)
                meter.settle(reservation, SimpleNamespace(prompt_tokens=10,completion_tokens=5))
                self.assertAlmostEqual(runner.Meter(2,8,5).spent, 0.00006)
                unknown = meter.reserve('hello', 100)
                meter.settle(unknown, None)
                self.assertGreater(runner.Meter(2,8,5).spent, 0.00006)
            finally:
                runner.ROOT = old

    def test_persistent_reservation_and_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            old = runner.ROOT
            runner.ROOT = Path(directory)
            try:
                meter = runner.Meter(10, 10, 0.1)
                meter.reserve('hello', 100)
                self.assertGreater(runner.Meter(10,10,0.1).spent, 0)
                with self.assertRaises(runner.StopExperiment):
                    meter.reserve('x' * 20000, 100)
            finally:
                runner.ROOT = old

if __name__ == '__main__':
    unittest.main()
