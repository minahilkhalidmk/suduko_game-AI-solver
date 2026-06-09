"""
performance.py
--------------
Benchmarking utilities: run all algorithms × all difficulties,
collect metrics, and provide data structures for the chart dashboard.
"""

import copy
import time
from generate_puzzle import generate_puzzle
from algorithms import fast_solve
from theme import ALGO_NAMES


ALGORITHMS  = ["backtracking", "ac3mrv", "forwardcheck", "simanneal"]
DIFFICULTIES = ["Easy", "Medium", "Hard", "Expert"]


# ── Result data class ─────────────────────────────────────────────────────────

class BenchmarkResult:
    """Holds the full benchmark matrix: algo × difficulty → metrics."""

    def __init__(self):
        # data[difficulty][algo] = {solved, time_ms, states, backs}
        self.data: dict[str, dict[str, dict]] = {
            d: {a: None for a in ALGORITHMS} for d in DIFFICULTIES
        }

    def store(self, difficulty: str, algo: str, result: dict):
        self.data[difficulty][algo] = {
            "solved":  result.get("solved", False),
            "time_ms": result.get("time_ms", 0.0),
            "states":  result.get("states", 0),
            "backs":   result.get("backs", 0),
        }

    def get(self, difficulty: str, algo: str) -> dict | None:
        return self.data[difficulty][algo]

    def avg_time(self, algo: str) -> float:
        times = [self.data[d][algo]["time_ms"]
                 for d in DIFFICULTIES if self.data[d][algo]]
        return sum(times) / len(times) if times else 0.0

    def avg_states(self, algo: str) -> float:
        vals = [self.data[d][algo]["states"]
                for d in DIFFICULTIES if self.data[d][algo]]
        return sum(vals) / len(vals) if vals else 0.0

    def rating(self, algo: str) -> str:
        t = self.avg_time(algo)
        if t < 20:   return "Fast"
        if t < 150:  return "Moderate"
        return "Slow"

    def times_by_difficulty(self, algo: str) -> list[float]:
        return [self.data[d][algo]["time_ms"] if self.data[d][algo] else 0.0
                for d in DIFFICULTIES]

    def states_by_difficulty(self, algo: str) -> list[int]:
        return [self.data[d][algo]["states"] if self.data[d][algo] else 0
                for d in DIFFICULTIES]

    def backs_by_difficulty(self, algo: str) -> list[int]:
        return [self.data[d][algo]["backs"] if self.data[d][algo] else 0
                for d in DIFFICULTIES]


# ── Benchmark runner ──────────────────────────────────────────────────────────

def run_benchmark(progress_callback=None) -> BenchmarkResult:
    """
    Run all 4 algorithms × 4 difficulty levels.

    Parameters
    ----------
    progress_callback : callable(step, total, message)
        Called after each (algo, difficulty) pair finishes.

    Returns
    -------
    BenchmarkResult
    """
    results = BenchmarkResult()
    total = len(ALGORITHMS) * len(DIFFICULTIES)
    step = 0

    for diff in DIFFICULTIES:
        puzzle, _ = generate_puzzle(diff)
        for algo in ALGORITHMS:
            step += 1
            msg = f"Running {ALGO_NAMES[algo]} on {diff}…"
            if progress_callback:
                progress_callback(step, total, msg)

            result = fast_solve(algo, copy.deepcopy(puzzle))
            results.store(diff, algo, result)

    if progress_callback:
        progress_callback(total, total, "Benchmark complete!")

    return results


# ── Synthetic fallback data ───────────────────────────────────────────────────
# Used to pre-populate charts before the user runs a real benchmark.

SYNTHETIC_DATA = {
    "Easy": {
        "backtracking": {"solved": True, "time_ms": 12.0,   "states": 200,    "backs": 40},
        "ac3mrv":       {"solved": True, "time_ms": 3.2,    "states": 48,     "backs": 6},
        "forwardcheck": {"solved": True, "time_ms": 5.5,    "states": 75,     "backs": 14},
        "simanneal":    {"solved": True, "time_ms": 90.0,   "states": 6000,   "backs": 3500},
    },
    "Medium": {
        "backtracking": {"solved": True, "time_ms": 95.0,   "states": 1400,   "backs": 450},
        "ac3mrv":       {"solved": True, "time_ms": 9.0,    "states": 130,    "backs": 22},
        "forwardcheck": {"solved": True, "time_ms": 17.0,   "states": 220,    "backs": 58},
        "simanneal":    {"solved": True, "time_ms": 380.0,  "states": 28000,  "backs": 20000},
    },
    "Hard": {
        "backtracking": {"solved": True, "time_ms": 480.0,  "states": 9500,   "backs": 3500},
        "ac3mrv":       {"solved": True, "time_ms": 28.0,   "states": 380,    "backs": 70},
        "forwardcheck": {"solved": True, "time_ms": 60.0,   "states": 750,    "backs": 220},
        "simanneal":    {"solved": True, "time_ms": 850.0,  "states": 65000,  "backs": 48000},
    },
    "Expert": {
        "backtracking": {"solved": True, "time_ms": 2400.0, "states": 52000,  "backs": 24000},
        "ac3mrv":       {"solved": True, "time_ms": 90.0,   "states": 1400,   "backs": 220},
        "forwardcheck": {"solved": True, "time_ms": 200.0,  "states": 3500,   "backs": 900},
        "simanneal":    {"solved": True, "time_ms": 1600.0, "states": 130000, "backs": 96000},
    },
}


def synthetic_results() -> BenchmarkResult:
    """Return a BenchmarkResult pre-filled with synthetic / indicative data."""
    r = BenchmarkResult()
    for diff, algos in SYNTHETIC_DATA.items():
        for algo, metrics in algos.items():
            r.store(diff, algo, metrics)
    return r