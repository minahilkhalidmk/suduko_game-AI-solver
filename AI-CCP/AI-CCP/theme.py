"""
theme.py
--------
Centralised colour palette and font constants.
Purple / Violet / Orchid design language.
"""

# ── Background layers ────────────────────────────────────────────────────────
BG_DARK       = "#0D0B14"   # deepest background
BG_MID        = "#130F20"   # sidebar / panels
BG_SURFACE    = "#1C1630"   # card surfaces
BG_SURFACE2   = "#251E3A"   # slightly lighter surface

# ── Accent spectrum (violet → orchid) ───────────────────────────────────────
VIOLET        = "#7B2FBE"   # strong violet
ORCHID        = "#A855F7"   # main accent orchid
LAVENDER      = "#C084FC"   # light orchid/lavender
LILAC         = "#DDD6FE"   # near-white lilac
MAGENTA_HINT  = "#E879F9"   # bright fuchsia highlight

# ── Semantic colours ─────────────────────────────────────────────────────────
TEAL          = "#2DD4BF"   # success / solved
CORAL         = "#F87171"   # backtrack / error
AMBER         = "#FBBF24"   # warning / checking
GREEN         = "#4ADE80"   # done / efficiency

# ── Text ─────────────────────────────────────────────────────────────────────
TEXT_PRIMARY   = "#EDE9FE"  # main text (lavender-white)
TEXT_SECONDARY = "#A78BFA"  # muted text
TEXT_MUTED     = "#6D5A9C"  # hints / labels

# ── Borders ──────────────────────────────────────────────────────────────────
BORDER         = "#2E2450"  # subtle border
BORDER_ACCENT  = "#7B2FBE"  # highlighted border

# ── Algorithm colours ────────────────────────────────────────────────────────
ALGO_COLORS = {
    "backtracking": ORCHID,
    "ac3mrv":       TEAL,
    "forwardcheck": AMBER,
    "simanneal":    CORAL,
}

ALGO_NAMES = {
    "backtracking": "Backtracking (DFS)",
    "ac3mrv":       "AC-3 + MRV",
    "forwardcheck": "Forward Checking",
    "simanneal":    "Simulated Annealing",
}

ALGO_DESCRIPTIONS = {
    "backtracking": (
        "Uninformed depth-first search.\n"
        "Places digits one by one; undoes the\n"
        "last assignment on conflict. No domain\n"
        "knowledge used — worst-case O(9^n)."
    ),
    "ac3mrv": (
        "AC-3 enforces arc consistency, pruning\n"
        "variable domains. MRV picks the most\n"
        "constrained cell first + Degree heuristic\n"
        "as tie-breaker. Dramatically fewer nodes."
    ),
    "forwardcheck": (
        "After each placement, propagates\n"
        "constraints to neighbours, eliminating\n"
        "impossible values early before deep\n"
        "recursion. Faster than pure backtracking."
    ),
    "simanneal": (
        "Starts from a complete (possibly invalid)\n"
        "board. Swaps values within boxes to reduce\n"
        "row/column conflicts. Accepts bad moves\n"
        "with P = exp(-ΔE/T), T cools over time."
    ),
}

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_TITLE   = ("Segoe UI", 22, "bold")
FONT_HEADING = ("Segoe UI", 13, "bold")
FONT_BODY    = ("Segoe UI", 11)
FONT_SMALL   = ("Segoe UI", 9)
FONT_MONO    = ("Consolas", 11)
FONT_CELL    = ("Consolas", 16, "bold")
FONT_CELL_SM = ("Consolas", 13, "bold")
FONT_METRIC  = ("Consolas", 22, "bold")

# ── Difficulty ────────────────────────────────────────────────────────────────
DIFFICULTY_RANGES = {
    "Easy":   (36, 40),
    "Medium": (27, 35),
    "Hard":   (20, 26),
    "Expert": (17, 19),
}

DIFFICULTY_COLORS = {
    "Easy":   "#4ADE80",
    "Medium": AMBER,
    "Hard":   CORAL,
    "Expert": MAGENTA_HINT,
}