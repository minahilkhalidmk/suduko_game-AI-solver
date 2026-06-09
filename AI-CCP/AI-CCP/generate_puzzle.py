"""
puzzle_generator.py
-------------------
Generates valid, uniquely-solvable Sudoku puzzles at four difficulty levels.

Public API
----------
generate_puzzle(difficulty: str) -> (puzzle, solution)
    difficulty: "Easy" | "Medium" | "Hard" | "Expert"
    Returns a tuple of two 9×9 lists:
        puzzle   — the clue board (0 = empty)
        solution — the fully solved board
"""

import random
import copy
from theme import DIFFICULTY_RANGES


# ── Low-level helpers ────────────────────────────────────────────────────────

def _is_valid(board: list[list[int]], row: int, col: int, num: int) -> bool:
    """Return True if `num` can legally be placed at (row, col)."""
    if num in board[row]:
        return False
    if num in (board[r][col] for r in range(9)):
        return False
    br, bc = (row // 3) * 3, (col // 3) * 3
    for dr in range(3):
        for dc in range(3):
            if board[br + dr][bc + dc] == num:
                return False
    return True


def _shuffle(seq: list) -> list:
    """Return a shuffled copy."""
    s = list(seq)
    random.shuffle(s)
    return s


# ── Solver used during generation ────────────────────────────────────────────

def _solve_random(board: list[list[int]]) -> bool:
    """Fill `board` in-place with a random valid solution. Returns True on success."""
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                for n in _shuffle(list(range(1, 10))):
                    if _is_valid(board, r, c, n):
                        board[r][c] = n
                        if _solve_random(board):
                            return True
                        board[r][c] = 0
                return False  # dead end
    return True


def _count_solutions(board: list[list[int]], limit: int = 2) -> int:
    """Count the number of solutions up to `limit` (used to check uniqueness)."""
    count = [0]

    def _bt():
        if count[0] >= limit:
            return
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    for n in range(1, 10):
                        if _is_valid(board, r, c, n):
                            board[r][c] = n
                            _bt()
                            board[r][c] = 0
                    return
        count[0] += 1

    _bt()
    return count[0]


# ── Public function ───────────────────────────────────────────────────────────

def generate_puzzle(difficulty: str = "Easy") -> tuple[list, list]:
    """
    Generate a valid, uniquely-solvable Sudoku puzzle.

    Parameters
    ----------
    difficulty : str
        One of "Easy", "Medium", "Hard", "Expert".

    Returns
    -------
    puzzle : 9×9 list  (0 = empty cell)
    solution : 9×9 list (fully solved)
    """
    # 1. Build a complete solved board
    solved = [[0] * 9 for _ in range(9)]
    _solve_random(solved)
    solution = copy.deepcopy(solved)

    # 2. Decide target number of filled cells
    lo, hi = DIFFICULTY_RANGES[difficulty]
    target_filled = random.randint(lo, hi)

    # 3. Remove cells while keeping uniqueness
    puzzle = copy.deepcopy(solved)
    cells = _shuffle(list(range(81)))
    filled = 81

    for idx in cells:
        if filled <= target_filled:
            break
        r, c = divmod(idx, 9)
        backup = puzzle[r][c]
        puzzle[r][c] = 0
        test = copy.deepcopy(puzzle)
        if _count_solutions(test) == 1:
            filled -= 1
        else:
            puzzle[r][c] = backup  # restore — would break uniqueness

    return puzzle, solution