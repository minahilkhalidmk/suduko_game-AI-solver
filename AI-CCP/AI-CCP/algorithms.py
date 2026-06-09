"""
algorithms.py
-------------
Four AI search / constraint-satisfaction algorithms for Sudoku.

Each solver returns a dict:
    {
        "solved":  bool,
        "board":   9×9 list,
        "states":  int,   # nodes / states explored
        "backs":   int,   # backtracks / rejected moves
        "time_ms": float, # wall-clock milliseconds
    }

Callback signature (optional, for live visualisation):
    callback(row, col, value, event_type)
    event_type: "place" | "backtrack" | "check" | "done"
"""

import copy
import time
import math
import random


# ══════════════════════════════════════════════════════════════════════════════
# Shared helpers
# ══════════════════════════════════════════════════════════════════════════════

def _is_valid(board, row, col, num):
    """Return True if num can be placed at (row, col) without conflict."""
    if num in board[row]:
        return False
    for r in range(9):
        if board[r][col] == num:
            return False
    br, bc = (row // 3) * 3, (col // 3) * 3
    for dr in range(3):
        for dc in range(3):
            if board[br + dr][bc + dc] == num:
                return False
    return True


def _get_peers(row, col):
    """Return all peer (r,c) positions that share a row, column, or box."""
    peers = set()
    for i in range(9):
        if i != col:
            peers.add((row, i))
        if i != row:
            peers.add((i, col))
    br, bc = (row // 3) * 3, (col // 3) * 3
    for dr in range(3):
        for dc in range(3):
            nr, nc = br + dr, bc + dc
            if (nr, nc) != (row, col):
                peers.add((nr, nc))
    return peers


def _get_domain(board, row, col):
    """Return the set of legal values for an empty cell."""
    if board[row][col] != 0:
        return {board[row][col]}
    used = set()
    for c in range(9):
        if board[row][c]:
            used.add(board[row][c])
    for r in range(9):
        if board[r][col]:
            used.add(board[r][col])
    br, bc = (row // 3) * 3, (col // 3) * 3
    for dr in range(3):
        for dc in range(3):
            if board[br + dr][bc + dc]:
                used.add(board[br + dr][bc + dc])
    return set(range(1, 10)) - used


# ══════════════════════════════════════════════════════════════════════════════
# Algorithm 1 — Backtracking (uninformed DFS)
# ══════════════════════════════════════════════════════════════════════════════

def solve_backtracking(puzzle, callback=None, stop_flag=None):
    """
    Plain depth-first backtracking — uninformed baseline.
    Explores cells left-to-right, top-to-bottom; tries digits 1–9 in order.
    """
    board = [row[:] for row in puzzle]
    stats = {"states": 0, "backs": 0}
    start = time.perf_counter()

    def bt(pos=0):
        if stop_flag and stop_flag():
            return False
        if pos == 81:
            return True
        r, c = divmod(pos, 9)
        if board[r][c] != 0:
            return bt(pos + 1)

        stats["states"] += 1
        if callback:
            callback(r, c, 0, "check")

        for n in range(1, 10):
            if stop_flag and stop_flag():
                return False
            if _is_valid(board, r, c, n):
                board[r][c] = n
                stats["states"] += 1
                if callback:
                    callback(r, c, n, "place")
                if bt(pos + 1):
                    return True
                board[r][c] = 0
                stats["backs"] += 1
                if callback:
                    callback(r, c, 0, "backtrack")
        return False

    solved = bt()
    elapsed = (time.perf_counter() - start) * 1000
    if solved and callback:
        callback(-1, -1, -1, "done")
    return {
        "solved":  solved,
        "board":   board,
        "states":  stats["states"],
        "backs":   stats["backs"],
        "time_ms": elapsed,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Algorithm 2 — AC-3 + MRV + Degree Heuristic (informed)
# ══════════════════════════════════════════════════════════════════════════════

def _ac3(board, domains):
    """
    Enforce arc consistency via AC-3.
    Modifies `domains` in-place.  Returns False if any domain becomes empty.
    """
    queue = []
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                for pr, pc in _get_peers(r, c):
                    queue.append((r, c, pr, pc))

    while queue:
        r, c, pr, pc = queue.pop(0)
        if board[r][c] != 0:
            continue
        prev_size = len(domains[r][c])
        # Remove values from domains[r][c] that are arc-inconsistent
        domains[r][c] -= {v for v in list(domains[r][c])
                          if domains[pr][pc] == {v}}
        if not domains[r][c]:
            return False
        if len(domains[r][c]) < prev_size:
            for nr, nc in _get_peers(r, c):
                queue.append((nr, nc, r, c))
    return True


def _mrv_cell(board, domains):
    """
    Select the unassigned cell with the fewest remaining values (MRV).
    Ties broken by the Degree heuristic (most constraints on other unassigned vars).
    """
    best, best_size, best_degree = None, 10, -1
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                sz = len(domains[r][c])
                deg = sum(1 for pr, pc in _get_peers(r, c) if board[pr][pc] == 0)
                if sz < best_size or (sz == best_size and deg > best_degree):
                    best, best_size, best_degree = (r, c), sz, deg
    return best


def solve_ac3_mrv(puzzle, callback=None, stop_flag=None):
    """
    Backtracking with AC-3 arc consistency + MRV + Degree heuristic.
    Informed search — dramatically reduces the search space.
    """
    board = [row[:] for row in puzzle]
    stats = {"states": 0, "backs": 0}
    start = time.perf_counter()

    def init_domains():
        return [[_get_domain(board, r, c) for c in range(9)] for r in range(9)]

    def bt(domains):
        if stop_flag and stop_flag():
            return False
        cell = _mrv_cell(board, domains)
        if cell is None:
            return True
        r, c = cell
        stats["states"] += 1
        if callback:
            callback(r, c, 0, "check")

        for val in sorted(domains[r][c]):
            if stop_flag and stop_flag():
                return False
            board[r][c] = val
            stats["states"] += 1
            if callback:
                callback(r, c, val, "place")

            # Deep-copy domains and propagate
            new_doms = [row[:] for row in domains]
            new_doms = [[copy.copy(new_doms[rr][cc]) for cc in range(9)] for rr in range(9)]
            new_doms[r][c] = {val}
            if _ac3(board, new_doms):
                if bt(new_doms):
                    return True
            board[r][c] = 0
            stats["backs"] += 1
            if callback:
                callback(r, c, 0, "backtrack")
        return False

    domains = init_domains()
    _ac3(board, domains)
    solved = bt(domains)
    elapsed = (time.perf_counter() - start) * 1000
    if solved and callback:
        callback(-1, -1, -1, "done")
    return {
        "solved":  solved,
        "board":   board,
        "states":  stats["states"],
        "backs":   stats["backs"],
        "time_ms": elapsed,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Algorithm 3 — Forward Checking with constraint propagation
# ══════════════════════════════════════════════════════════════════════════════

def solve_forward_checking(puzzle, callback=None, stop_flag=None):
    """
    Backtracking enhanced with forward checking.
    After each assignment, propagates the constraint to all unassigned
    neighbours, eliminating impossible values before recursing deeper.
    """
    board = [row[:] for row in puzzle]
    stats = {"states": 0, "backs": 0}
    start = time.perf_counter()

    def init_domains():
        return [[_get_domain(board, r, c) for c in range(9)] for r in range(9)]

    def _next_cell(b, doms):
        best, best_sz = None, 10
        for r in range(9):
            for c in range(9):
                if b[r][c] == 0:
                    sz = len(doms[r][c])
                    if sz < best_sz:
                        best, best_sz = (r, c), sz
        return best

    def forward_check(b, doms, r, c, val):
        """
        Remove `val` from peer domains.
        Returns list of (r,c,val) removals, or None on failure.
        """
        removed = []
        for pr, pc in _get_peers(r, c):
            if b[pr][pc] == 0 and val in doms[pr][pc]:
                doms[pr][pc].discard(val)
                removed.append((pr, pc, val))
                if not doms[pr][pc]:
                    # Restore and signal failure
                    for rr, rc, rv in removed:
                        doms[rr][rc].add(rv)
                    return None
        return removed

    def bt(doms):
        if stop_flag and stop_flag():
            return False
        cell = _next_cell(board, doms)
        if cell is None:
            return True
        r, c = cell
        stats["states"] += 1
        if callback:
            callback(r, c, 0, "check")

        for val in sorted(doms[r][c]):
            if stop_flag and stop_flag():
                return False
            board[r][c] = val
            stats["states"] += 1
            if callback:
                callback(r, c, val, "place")

            new_doms = [[copy.copy(doms[rr][cc]) for cc in range(9)] for rr in range(9)]
            new_doms[r][c] = {val}
            saved = forward_check(board, new_doms, r, c, val)
            if saved is not None:
                if bt(new_doms):
                    return True
            board[r][c] = 0
            stats["backs"] += 1
            if callback:
                callback(r, c, 0, "backtrack")
        return False

    domains = init_domains()
    solved = bt(domains)
    elapsed = (time.perf_counter() - start) * 1000
    if solved and callback:
        callback(-1, -1, -1, "done")
    return {
        "solved":  solved,
        "board":   board,
        "states":  stats["states"],
        "backs":   stats["backs"],
        "time_ms": elapsed,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Algorithm 4 — Simulated Annealing (local search)
# ══════════════════════════════════════════════════════════════════════════════

def _count_conflicts(board):
    """Count total row + column constraint violations (box conflicts ignored — boxes stay filled 1-9)."""
    conflicts = 0
    for i in range(9):
        row_seen, col_seen = set(), set()
        for j in range(9):
            rv = board[i][j]
            if rv in row_seen:
                conflicts += 1
            else:
                row_seen.add(rv)
            cv = board[j][i]
            if cv in col_seen:
                conflicts += 1
            else:
                col_seen.add(cv)
    return conflicts


def solve_simulated_annealing(puzzle, callback=None, stop_flag=None):
    """
    Local search via Simulated Annealing.

    Initialises each 3×3 box with a permutation of 1–9 (respecting givens).
    Then iteratively swaps two non-given cells within a randomly chosen box.
    Accepts improvements always; accepts worsening with P = exp(-ΔE/T).
    Temperature decreases geometrically until Tmin or energy == 0.
    """
    board = [row[:] for row in puzzle]
    given = [[puzzle[r][c] != 0 for c in range(9)] for r in range(9)]
    stats = {"states": 0, "backs": 0}
    start = time.perf_counter()

    # ── Initialise: fill each box with missing numbers ──────────────────────
    for br in range(3):
        for bc in range(3):
            present = set()
            free_cells = []
            for dr in range(3):
                for dc in range(3):
                    r, c = br * 3 + dr, bc * 3 + dc
                    if given[r][c]:
                        present.add(board[r][c])
                    else:
                        free_cells.append((r, c))
            missing = list(set(range(1, 10)) - present)
            random.shuffle(missing)
            for (r, c), val in zip(free_cells, missing):
                board[r][c] = val

    if callback:
        for r in range(9):
            for c in range(9):
                if not given[r][c]:
                    callback(r, c, board[r][c], "check")

    # ── Annealing schedule ───────────────────────────────────────────────────
    T = 2.0
    T_min = 0.001
    cooling = 0.99995
    energy = _count_conflicts(board)
    report_interval = 500
    itr = 0

    while T > T_min and energy > 0:
        if stop_flag and stop_flag():
            break
        itr += 1

        # Pick a random box
        br, bc = random.randint(0, 2), random.randint(0, 2)
        free = [(br * 3 + dr, bc * 3 + dc)
                for dr in range(3)
                for dc in range(3)
                if not given[br * 3 + dr][bc * 3 + dc]]
        if len(free) < 2:
            T *= cooling
            continue

        (r1, c1), (r2, c2) = random.sample(free, 2)
        # Swap
        board[r1][c1], board[r2][c2] = board[r2][c2], board[r1][c1]
        new_energy = _count_conflicts(board)
        dE = new_energy - energy
        stats["states"] += 1

        if dE < 0 or (T > 0 and random.random() < math.exp(-dE / T)):
            energy = new_energy
            if callback and itr % report_interval == 0:
                callback(r1, c1, board[r1][c1], "place")
                callback(r2, c2, board[r2][c2], "place")
        else:
            # Undo swap
            board[r1][c1], board[r2][c2] = board[r2][c2], board[r1][c1]
            stats["backs"] += 1

        T *= cooling

    solved = energy == 0
    elapsed = (time.perf_counter() - start) * 1000
    if callback:
        for r in range(9):
            for c in range(9):
                if not given[r][c]:
                    callback(r, c, board[r][c], "done" if solved else "backtrack")
        callback(-1, -1, -1, "done")

    return {
        "solved":  solved,
        "board":   board,
        "states":  stats["states"],
        "backs":   stats["backs"],
        "time_ms": elapsed,
        "energy":  energy,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Fast (no-callback) runner — used for benchmarking
# ══════════════════════════════════════════════════════════════════════════════

def fast_solve(algo: str, puzzle: list) -> dict:
    """Run `algo` on `puzzle` without any visualisation callback."""
    dispatch = {
        "backtracking": solve_backtracking,
        "ac3mrv":       solve_ac3_mrv,
        "forwardcheck": solve_forward_checking,
        "simanneal":    solve_simulated_annealing,
    }
    return dispatch[algo](puzzle)