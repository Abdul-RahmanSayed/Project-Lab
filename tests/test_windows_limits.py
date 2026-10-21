"""Temporary benchmark sleep requests must restore the prior thread state."""

from pathlib import Path
import sys
import unittest
from unittest.mock import call, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data-build"))
from windows_limits import prevent_idle_sleep


@unittest.skipUnless(sys.platform == "win32", "Windows execution-state API only")
class SleepGuardTests(unittest.TestCase):
    def test_restores_previous_state(self):
        with patch("windows_limits.ctypes.WinDLL") as library:
            request = library.return_value.SetThreadExecutionState
            request.side_effect = [0x80000000, 0x80000001]
            with prevent_idle_sleep():
                self.assertEqual(request.call_count, 1)
            self.assertEqual(request.call_args_list, [call(0x80000003), call(0x80000000)])

    def test_restores_even_when_benchmark_fails(self):
        with patch("windows_limits.ctypes.WinDLL") as library:
            request = library.return_value.SetThreadExecutionState
            request.side_effect = [0x80000000, 0x80000001]
            with self.assertRaisesRegex(ValueError, "benchmark failed"):
                with prevent_idle_sleep():
                    raise ValueError("benchmark failed")
            self.assertEqual(request.call_args_list, [call(0x80000003), call(0x80000000)])

    def test_failed_request_does_not_enter_guard(self):
        with patch("windows_limits.ctypes.WinDLL") as library:
            request = library.return_value.SetThreadExecutionState
            request.return_value = 0
            with self.assertRaisesRegex(RuntimeError, "Could not request"):
                with prevent_idle_sleep():
                    self.fail("Failed request must not run the benchmark")
            self.assertEqual(request.call_count, 1)


if __name__ == "__main__":
    unittest.main()
