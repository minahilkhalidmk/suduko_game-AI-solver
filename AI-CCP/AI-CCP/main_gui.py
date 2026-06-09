"""
main_gui.py
-----------
Main application window using tkinter + customtkinter.

Tabs
----
  1. Solver      — interactive puzzle board with live algorithm animation
  2. Performance — benchmark charts (matplotlib embedded)
  3. CSP Theory  — conceptual explanations of each algorithm
  4. Adversarial — two agents race on the same puzzle

Run
---
    python main_gui.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import threading
import time
import copy

from theme import *
from generate_puzzle import generate_puzzle
from algorithms import (
    solve_backtracking,
    solve_ac3_mrv,
    solve_forward_checking,
    solve_simulated_annealing,
    fast_solve,
)
from performance import run_benchmark, synthetic_results, ALGORITHMS, DIFFICULTIES
from charts import ChartFrame


# ── customtkinter global setup ────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


# ══════════════════════════════════════════════════════════════════════════════
# Sudoku Board Widget
# ══════════════════════════════════════════════════════════════════════════════

CELL_SIZE = 52

class SudokuBoard(tk.Canvas):
    """
    A 9×9 Sudoku grid drawn on a tk.Canvas.
    Supports cell colouring for algorithm animation.
    """

    CELL_COLORS = {
        "given":     (BG_SURFACE2,   TEXT_PRIMARY),
        "empty":     (BG_SURFACE,    TEXT_MUTED),
        "current":   ("#3B2A6E",     ORCHID),
        "checking":  ("#2A2310",     AMBER),
        "backtrack": ("#2A1010",     CORAL),
        "solved":    ("#0E2A24",     TEAL),
        "conflict":  ("#3A1010",     CORAL),
    }

    def __init__(self, master, cell_size=CELL_SIZE, **kwargs):
        self.cs = cell_size
        size = self.cs * 9 + 4
        super().__init__(master, width=size, height=size,
                         bg=BG_DARK, highlightthickness=0, **kwargs)
        self._puzzle  = [[0]*9 for _ in range(9)]
        self._given   = [[False]*9 for _ in range(9)]
        self._states  = [["empty"]*9 for _ in range(9)]
        self._values  = [[0]*9 for _ in range(9)]
        self._items   = {}   # (r,c) -> (rect_id, text_id)
        self._draw_grid()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw_grid(self):
        self.delete("all")
        self._items.clear()
        cs = self.cs
        for r in range(9):
            for c in range(9):
                x0 = c * cs + 2
                y0 = r * cs + 2
                x1 = x0 + cs
                y1 = y0 + cs
                rect = self.create_rectangle(x0, y0, x1, y1,
                                             fill=BG_SURFACE, outline=BORDER, width=1)
                txt = self.create_text(x0 + cs//2, y0 + cs//2,
                                       text="", font=FONT_CELL,
                                       fill=TEXT_MUTED)
                self._items[(r, c)] = (rect, txt)

        # thick box borders
        for i in range(4):
            lw = 3 if i % 3 == 0 else 1
            col = ORCHID if i % 3 == 0 else BORDER
            x = i * 3 * cs + 2
            self.create_line(x, 2, x, 9*cs+2, fill=col, width=lw)
            self.create_line(2, x, 9*cs+2, x, fill=col, width=lw)
        # right/bottom edge
        self.create_line(9*cs+2, 2, 9*cs+2, 9*cs+3, fill=ORCHID, width=3)
        self.create_line(2, 9*cs+2, 9*cs+3, 9*cs+2, fill=ORCHID, width=3)

    def load_puzzle(self, puzzle):
        self._puzzle  = [row[:] for row in puzzle]
        self._given   = [[v != 0 for v in row] for row in puzzle]
        self._values  = [row[:] for row in puzzle]
        self._states  = [["given" if puzzle[r][c] else "empty"
                          for c in range(9)] for r in range(9)]
        self._refresh_all()

    def _refresh_all(self):
        for r in range(9):
            for c in range(9):
                self._draw_cell(r, c)

    def _draw_cell(self, r, c):
        rect, txt = self._items[(r, c)]
        state = self._states[r][c]
        bg, fg = self.CELL_COLORS.get(state, (BG_SURFACE, TEXT_MUTED))
        val = self._values[r][c]
        self.itemconfig(rect, fill=bg)
        self.itemconfig(txt, text=str(val) if val else "", fill=fg)

    def set_cell(self, r, c, value, state="current"):
        if self._given[r][c]:
            return
        if value:
            self._values[r][c] = value
        self._states[r][c] = state
        self.after(0, self._draw_cell, r, c)

    def reset_solved_cells(self):
        for r in range(9):
            for c in range(9):
                if not self._given[r][c]:
                    self._values[r][c] = 0
                    self._states[r][c] = "empty"
        self._refresh_all()

    def mark_all_solved(self, board):
        for r in range(9):
            for c in range(9):
                if not self._given[r][c]:
                    self._values[r][c] = board[r][c]
                    self._states[r][c] = "solved"
        self._refresh_all()


# ══════════════════════════════════════════════════════════════════════════════
# Log Widget
# ══════════════════════════════════════════════════════════════════════════════

class LogPanel(ctk.CTkTextbox):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=BG_DARK, text_color=TEXT_SECONDARY,
                         font=FONT_MONO, **kwargs)
        self.configure(state="disabled")
        self._count = 0

    def append(self, msg: str, color: str = None):
        self._count += 1
        self.configure(state="normal")
        tag = f"t{self._count}"
        line = f"{self._count:04d}  {msg}\n"
        self.insert("end", line, tag)
        if color:
            self.tag_config(tag, foreground=color)
        self.see("end")
        self.configure(state="disabled")

    def clear(self):
        self._count = 0
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.configure(state="disabled")


# ══════════════════════════════════════════════════════════════════════════════
# Solver Tab
# ══════════════════════════════════════════════════════════════════════════════

class SolverTab(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=BG_DARK, **kwargs)
        self._puzzle    = []
        self._solution  = []
        self._algo      = "backtracking"
        self._difficulty = "Easy"
        self._solving   = False
        self._stop_flag = False
        self._thread    = None
        self._speed     = 3          # 1–5
        self._step_delays = {1: 0.18, 2: 0.07, 3: 0.025, 4: 0.008, 5: 0.0}
        self._build_ui()
        self.generate_new()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # ── Left controls ──────────────────────────────────────────────────
        ctrl = ctk.CTkFrame(self, fg_color=BG_MID, corner_radius=14, width=210)
        ctrl.grid(row=0, column=0, sticky="ns", padx=(0, 16), pady=0)
        ctrl.grid_propagate(False)
        ctrl.columnconfigure(0, weight=1)

        _label(ctrl, "DIFFICULTY", TEXT_MUTED, 9).grid(row=0, column=0, sticky="w", padx=16, pady=(18,6))
        self._diff_btns = {}
        for i, d in enumerate(["Easy", "Medium", "Hard", "Expert"]):
            b = _tag_btn(ctrl, d, DIFFICULTY_COLORS[d],
                         lambda x=d: self._set_difficulty(x))
            b.grid(row=i+1, column=0, sticky="ew", padx=12, pady=3)
            self._diff_btns[d] = b

        _sep(ctrl).grid(row=5, column=0, sticky="ew", padx=12, pady=8)
        _label(ctrl, "ALGORITHM", TEXT_MUTED, 9).grid(row=6, column=0, sticky="w", padx=16, pady=(0,6))
        self._algo_btns = {}
        rows_start = 7
        for i, a in enumerate(ALGORITHMS):
            b = _algo_btn(ctrl, a, lambda x=a: self._set_algo(x))
            b.grid(row=rows_start+i, column=0, sticky="ew", padx=12, pady=3)
            self._algo_btns[a] = b

        _sep(ctrl).grid(row=rows_start+4, column=0, sticky="ew", padx=12, pady=8)
        _label(ctrl, "ANIMATION SPEED", TEXT_MUTED, 9).grid(row=rows_start+5, column=0, sticky="w", padx=16, pady=(0,4))
        self._speed_var = tk.IntVar(value=3)
        speed_sl = ctk.CTkSlider(ctrl, from_=1, to=5, number_of_steps=4,
                                  variable=self._speed_var,
                                  button_color=ORCHID, progress_color=VIOLET,
                                  fg_color=BG_SURFACE2,
                                  command=self._on_speed)
        speed_sl.grid(row=rows_start+6, column=0, sticky="ew", padx=12)
        self._speed_lbl = _label(ctrl, "Normal", LAVENDER, 10)
        self._speed_lbl.grid(row=rows_start+7, column=0, pady=2)

        _sep(ctrl).grid(row=rows_start+8, column=0, sticky="ew", padx=12, pady=8)
        self._solve_btn = ctk.CTkButton(ctrl, text="▶  Solve Puzzle",
                                         fg_color=VIOLET, hover_color=ORCHID,
                                         text_color="white", font=FONT_HEADING,
                                         corner_radius=10,
                                         command=self._toggle_solve)
        self._solve_btn.grid(row=rows_start+9, column=0, sticky="ew", padx=12, pady=3)
        ctk.CTkButton(ctrl, text="⟳  New Puzzle",
                      fg_color=BG_SURFACE2, hover_color=BG_SURFACE,
                      text_color=TEXT_SECONDARY, font=FONT_BODY,
                      corner_radius=10,
                      command=self.generate_new).grid(row=rows_start+10, column=0, sticky="ew", padx=12, pady=3)

        # ── Board + Metrics ────────────────────────────────────────────────
        right = ctk.CTkFrame(self, fg_color=BG_DARK)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(1, weight=1)
        right.rowconfigure(1, weight=1)

        # Board section
        board_wrap = ctk.CTkFrame(right, fg_color=BG_MID, corner_radius=14)
        board_wrap.grid(row=0, column=0, rowspan=2, sticky="n", padx=(0,16))
        self._board_title = _label(board_wrap, "EASY  —  Backtracking", LAVENDER, 10)
        self._board_title.pack(padx=16, pady=(14,6))
        self._board = SudokuBoard(board_wrap, cell_size=CELL_SIZE)
        self._board.pack(padx=12, pady=(0,6))
        self._progress = ctk.CTkProgressBar(board_wrap, width=CELL_SIZE*9,
                                             fg_color=BG_SURFACE2, progress_color=ORCHID,
                                             corner_radius=4)
        self._progress.set(0)
        self._progress.pack(padx=12, pady=(0,10))

        # Mode pill
        self._mode_var = tk.StringVar(value="⬤  Idle")
        self._mode_lbl = ctk.CTkLabel(board_wrap, textvariable=self._mode_var,
                                       font=FONT_SMALL, text_color=TEXT_MUTED,
                                       fg_color=BG_SURFACE2, corner_radius=10)
        self._mode_lbl.pack(padx=12, pady=(0,12))

        # Metrics grid
        met = ctk.CTkFrame(right, fg_color=BG_DARK)
        met.grid(row=0, column=1, sticky="new")
        met.columnconfigure((0,1), weight=1)

        self._m_states = self._metric_card(met, "STATES",   "—", ORCHID,  0, 0)
        self._m_backs  = self._metric_card(met, "BACKTRACKS","—", CORAL,   0, 1)
        self._m_time   = self._metric_card(met, "TIME (ms)", "—", TEAL,    1, 0)
        self._m_eff    = self._metric_card(met, "EFFICIENCY","—", GREEN,   1, 1)

        # Algo description
        self._desc_frame = ctk.CTkFrame(right, fg_color=BG_SURFACE, corner_radius=12)
        self._desc_frame.grid(row=1, column=1, sticky="new", pady=(12,0))
        _label(self._desc_frame, "ALGORITHM DESCRIPTION", TEXT_MUTED, 9).pack(anchor="w", padx=14, pady=(10,4))
        self._algo_lbl = ctk.CTkLabel(self._desc_frame, text=ALGO_NAMES["backtracking"],
                                       font=FONT_HEADING, text_color=ORCHID)
        self._algo_lbl.pack(anchor="w", padx=14)
        self._desc_lbl = ctk.CTkLabel(self._desc_frame,
                                       text=ALGO_DESCRIPTIONS["backtracking"],
                                       font=FONT_BODY, text_color=TEXT_SECONDARY,
                                       justify="left")
        self._desc_lbl.pack(anchor="w", padx=14, pady=(4,12))

        # Log
        log_frame = ctk.CTkFrame(right, fg_color=BG_MID, corner_radius=12)
        log_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(16,0))
        _label(log_frame, "SOLVER LOG", TEXT_MUTED, 9).pack(anchor="w", padx=14, pady=(10,4))
        self._log = LogPanel(log_frame, height=140)
        self._log.pack(fill="x", padx=10, pady=(0,10))

        # Initialise button states
        self._set_difficulty("Easy")
        self._set_algo("backtracking")

    def _metric_card(self, parent, label, initial, color, r, c):
        card = ctk.CTkFrame(parent, fg_color=BG_SURFACE, corner_radius=12)
        card.grid(row=r, column=c, sticky="ew", padx=5, pady=5)
        _label(card, label, TEXT_MUTED, 9).pack(anchor="w", padx=12, pady=(10,0))
        val_lbl = ctk.CTkLabel(card, text=initial, font=FONT_METRIC, text_color=color)
        val_lbl.pack(anchor="w", padx=12, pady=(2,10))
        return val_lbl

    # ── Event handlers ────────────────────────────────────────────────────────

    def _set_difficulty(self, d):
        self._difficulty = d
        for k, b in self._diff_btns.items():
            b.configure(fg_color=DIFFICULTY_COLORS[k] if k == d else BG_SURFACE2,
                        text_color="white" if k == d else TEXT_SECONDARY)

    def _set_algo(self, a):
        self._algo = a
        for k, b in self._algo_btns.items():
            b.configure(fg_color=ALGO_COLORS[k] if k == a else BG_SURFACE2,
                        text_color="white" if k == a else TEXT_SECONDARY)
        self._algo_lbl.configure(text=ALGO_NAMES[a], text_color=ALGO_COLORS[a])
        self._desc_lbl.configure(text=ALGO_DESCRIPTIONS[a])

    def _on_speed(self, v):
        self._speed = int(float(v))
        labels = {1:"Slow", 2:"Relaxed", 3:"Normal", 4:"Fast", 5:"Instant"}
        self._speed_lbl.configure(text=labels[self._speed])

    def generate_new(self):
        if self._solving:
            self._stop_flag = True
            return
        puzzle, solution = generate_puzzle(self._difficulty)
        self._puzzle   = puzzle
        self._solution = solution
        self._board.load_puzzle(puzzle)
        self._board_title.configure(
            text=f"{self._difficulty.upper()}  —  {ALGO_NAMES[self._algo]}"
        )
        self._reset_metrics()
        self._log.clear()
        self._log.append(f"Generated {self._difficulty} puzzle", LAVENDER)
        self._progress.set(0)
        self._set_mode(False)

    def _toggle_solve(self):
        if self._solving:
            self._stop_flag = True
            self._solve_btn.configure(text="▶  Solve Puzzle")
            return
        self._start_solve()

    def _start_solve(self):
        self._stop_flag = False
        self._solving   = True
        self._board.reset_solved_cells()
        self._reset_metrics()
        self._log.clear()
        self._set_mode(True)
        self._solve_btn.configure(text="⏹  Stop")
        self._board_title.configure(
            text=f"{self._difficulty.upper()}  —  {ALGO_NAMES[self._algo]}"
        )
        self._log.append(f"Algorithm : {ALGO_NAMES[self._algo]}", ORCHID)
        self._log.append(f"Difficulty: {self._difficulty}", LAVENDER)

        dispatch = {
            "backtracking": solve_backtracking,
            "ac3mrv":       solve_ac3_mrv,
            "forwardcheck": solve_forward_checking,
            "simanneal":    solve_simulated_annealing,
        }
        solver = dispatch[self._algo]

        self._step_count = 0
        self._log_throttle = 0

        def callback(r, c, v, event):
            if self._stop_flag:
                return
            self._step_count += 1
            d = self._step_delays[self._speed]
            if event == "check":
                self._board.set_cell(r, c, v or None, "checking")
            elif event == "place":
                self._board.set_cell(r, c, v, "current")
                self._log_throttle += 1
                if self._log_throttle % 60 == 0:
                    self.after(0, self._log.append,
                               f"Placed {v} → ({r+1},{c+1})", TEAL)
            elif event == "backtrack":
                self._board.set_cell(r, c, None, "backtrack")
                self._log_throttle += 1
                if self._log_throttle % 60 == 0:
                    self.after(0, self._log.append,
                               f"Backtrack ← ({r+1},{c+1})", CORAL)
            elif event == "done":
                return
            if d > 0:
                time.sleep(d)
            # update progress bar roughly
            if self._step_count % 100 == 0:
                prog = min(0.99, self._step_count / max(1, self._step_count + 200))
                self.after(0, self._progress.set, prog)

        def _run():
            puzzle_copy = [row[:] for row in self._puzzle]
            result = solver(puzzle_copy, callback=callback,
                            stop_flag=lambda: self._stop_flag)
            self.after(0, self._on_done, result)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def _on_done(self, result):
        self._solving = False
        self._stop_flag = False
        self._solve_btn.configure(text="▶  Solve Puzzle")
        self._set_mode(False)
        self._progress.set(1 if result.get("solved") else 0.5)

        self._m_states.configure(text=f"{result['states']:,}")
        self._m_backs.configure(text=f"{result['backs']:,}")
        self._m_time.configure(text=f"{result['time_ms']:.1f}")
        eff = result['states'] / max(result['time_ms'], 0.001)
        self._m_eff.configure(text=f"{eff:.1f}")

        if result.get("solved"):
            self._board.mark_all_solved(result["board"])
            self._log.append(
                f"✓ Solved! States={result['states']:,} "
                f"Backs={result['backs']:,} "
                f"Time={result['time_ms']:.1f}ms", GREEN
            )
        else:
            self._log.append("✗ Could not solve (try SA with more iterations)", CORAL)

    def _reset_metrics(self):
        for lbl in (self._m_states, self._m_backs, self._m_time, self._m_eff):
            lbl.configure(text="—")

    def _set_mode(self, running: bool):
        if running:
            self._mode_var.set("⬤  Solving…")
            self._mode_lbl.configure(text_color=ORCHID)
        else:
            self._mode_var.set("⬤  Idle")
            self._mode_lbl.configure(text_color=TEXT_MUTED)


# ══════════════════════════════════════════════════════════════════════════════
# Performance Tab
# ══════════════════════════════════════════════════════════════════════════════

class PerformanceTab(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=BG_DARK, **kwargs)
        self._results = synthetic_results()
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Top toolbar
        bar = ctk.CTkFrame(self, fg_color=BG_MID, corner_radius=12)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ctk.CTkLabel(bar, text="Performance Dashboard",
                     font=FONT_TITLE, text_color=LAVENDER).pack(side="left", padx=16, pady=10)
        self._bench_btn = ctk.CTkButton(bar, text="⚡  Run Benchmark",
                                         fg_color=VIOLET, hover_color=ORCHID,
                                         text_color="white", font=FONT_HEADING,
                                         corner_radius=10,
                                         command=self._run_bench)
        self._bench_btn.pack(side="right", padx=12, pady=8)
        self._prog_lbl = ctk.CTkLabel(bar, text="Using synthetic data — run benchmark for real results",
                                       font=FONT_SMALL, text_color=TEXT_MUTED)
        self._prog_lbl.pack(side="right", padx=4)

        # Charts
        self._chart_frame = ChartFrame(self, self._results)
        self._chart_frame.grid(row=1, column=0, sticky="nsew")

    def _run_bench(self):
        self._bench_btn.configure(state="disabled", text="Running…")

        def _worker():
            def _progress(step, total, msg):
                self.after(0, self._prog_lbl.configure, {"text": msg})
            results = run_benchmark(progress_callback=_progress)
            self.after(0, self._on_bench_done, results)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_bench_done(self, results):
        self._results = results
        self._bench_btn.configure(state="normal", text="⚡  Run Benchmark")
        self._prog_lbl.configure(text="Benchmark complete!")
        self._chart_frame.destroy()
        self._chart_frame = ChartFrame(self, results)
        self._chart_frame.grid(row=1, column=0, sticky="nsew")


# ══════════════════════════════════════════════════════════════════════════════
# CSP Theory Tab
# ══════════════════════════════════════════════════════════════════════════════

THEORY_CARDS = [
    ("🔍", "CSP Formulation",
     "Sudoku as a Constraint Satisfaction Problem:\n\n"
     "• Variables:   81 cells (X₁₁ … X₉₉)\n"
     "• Domains:     {1, 2, 3, 4, 5, 6, 7, 8, 9}\n"
     "• Constraints:\n"
     "    – AllDiff(row)    × 9\n"
     "    – AllDiff(col)    × 9\n"
     "    – AllDiff(box)    × 9\n"
     "• Goal: complete, consistent assignment\n\n"
     "State space: up to 9^81 ≈ 2×10^77 assignments.\n"
     "Constraints reduce this dramatically.",
     ORCHID, "FOUNDATION"),
    ("🌲", "Backtracking Search",
     "Uninformed DFS baseline:\n\n"
     "1. Select next empty cell (left→right, top→bottom)\n"
     "2. Try digits 1–9 in order\n"
     "3. If valid, recurse deeper\n"
     "4. If no digit works → BACKTRACK\n\n"
     "Complexity: O(9^n) worst case (n = empty cells)\n"
     "No domain pruning — explores many dead-ends.\n"
     "Correct & complete but inefficient on hard puzzles.",
     ORCHID, "UNINFORMED"),
    ("⚡", "AC-3 + MRV Heuristic",
     "Informed search with arc consistency:\n\n"
     "AC-3 enforces arc consistency:\n"
     "  For each arc (Xᵢ, Xⱼ): remove values from\n"
     "  domain(Xᵢ) with no support in domain(Xⱼ)\n\n"
     "MRV (Minimum Remaining Values):\n"
     "  Select cell with fewest legal values first\n"
     "  → most constrained variable, fewest choices\n\n"
     "Degree Heuristic (tie-breaker):\n"
     "  Prefer cell involved in most constraints\n"
     "  on other unassigned variables.",
     TEAL, "INFORMED"),
    ("🔗", "Forward Checking",
     "Constraint propagation during search:\n\n"
     "After assigning value v to cell Xᵢ:\n"
     "  For each unassigned peer Xⱼ:\n"
     "    Remove v from domain(Xⱼ)\n"
     "    If domain(Xⱼ) becomes empty → FAIL EARLY\n\n"
     "Detects failures earlier than backtracking\n"
     "without full AC-3 overhead.\n\n"
     "Trade-off: FC overhead < backtracking waste\n"
     "on medium/hard puzzles.",
     AMBER, "PROPAGATION"),
    ("🌡️", "Simulated Annealing",
     "Local search / optimisation approach:\n\n"
     "Initialisation:\n"
     "  Fill each 3×3 box with 1–9 (random perm)\n"
     "  → complete but possibly conflicting board\n\n"
     "Energy = row + column constraint violations\n\n"
     "Each iteration:\n"
     "  Swap two non-given cells in a random box\n"
     "  If ΔE < 0 (improvement) → always accept\n"
     "  If ΔE ≥ 0 → accept with P = e^(-ΔE/T)\n\n"
     "Temperature T decreases geometrically (cooling)\n"
     "until T < Tₘᵢₙ or energy = 0 (solved).",
     CORAL, "LOCAL SEARCH"),
    ("📊", "Complexity Analysis",
     "Empirical comparison (typical 9×9):\n\n"
     "Algorithm       Easy    Hard    Expert\n"
     "─────────────────────────────────────\n"
     "Backtracking    ~12ms   ~480ms  ~2400ms\n"
     "AC-3 + MRV      ~3ms    ~28ms   ~90ms\n"
     "Forward Check   ~5ms    ~60ms   ~200ms\n"
     "Sim. Annealing  ~90ms   ~850ms  ~1600ms\n\n"
     "AC-3+MRV is 10–30× faster than backtracking.\n"
     "SA time is non-deterministic (stochastic).\n"
     "SA may fail to find solution in one run.",
     MAGENTA_HINT, "ANALYSIS"),
]

class TheoryTab(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=BG_DARK, **kwargs)
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="CSP Theory & Algorithm Design",
                     font=FONT_TITLE, text_color=LAVENDER).pack(anchor="w", padx=0, pady=(0,16))

        scroll = ctk.CTkScrollableFrame(self, fg_color=BG_DARK)
        scroll.pack(fill="both", expand=True)
        scroll.columnconfigure((0,1), weight=1)

        for i, (icon, title, text, color, tag) in enumerate(THEORY_CARDS):
            r, c = divmod(i, 2)
            card = ctk.CTkFrame(scroll, fg_color=BG_SURFACE, corner_radius=14,
                                border_width=1, border_color=BORDER)
            card.grid(row=r, column=c, sticky="nsew", padx=8, pady=8)
            card.columnconfigure(0, weight=1)

            hdr = ctk.CTkFrame(card, fg_color=BG_SURFACE)
            hdr.pack(fill="x", padx=16, pady=(14,0))
            ctk.CTkLabel(hdr, text=icon, font=("Segoe UI Emoji", 22)).pack(side="left")
            ctk.CTkLabel(hdr, text=title, font=FONT_HEADING, text_color=color).pack(side="left", padx=8)
            tag_lbl = ctk.CTkLabel(hdr, text=tag, font=FONT_SMALL,
                                    text_color=color, fg_color=BG_SURFACE2,
                                    corner_radius=6)
            tag_lbl.pack(side="right")

            ctk.CTkLabel(card, text=text, font=FONT_MONO,
                         text_color=TEXT_SECONDARY, justify="left",
                         anchor="w").pack(fill="x", padx=16, pady=(8,16))


# ══════════════════════════════════════════════════════════════════════════════
# Adversarial Tab
# ══════════════════════════════════════════════════════════════════════════════

class AdversarialTab(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=BG_DARK, **kwargs)
        self._puzzle   = []
        self._running  = False
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure((0,1), weight=1)
        self.rowconfigure(2, weight=1)

        title = ctk.CTkFrame(self, fg_color=BG_MID, corner_radius=12)
        title.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0,16))
        ctk.CTkLabel(title, text="⚔  Adversarial Race Mode",
                     font=FONT_TITLE, text_color=MAGENTA_HINT).pack(side="left", padx=16, pady=10)
        ctk.CTkLabel(title,
                     text="Two AI agents race to solve the same puzzle. Best algorithm wins!",
                     font=FONT_BODY, text_color=TEXT_SECONDARY).pack(side="left", padx=4)

        # Controls row
        ctrl = ctk.CTkFrame(self, fg_color=BG_MID, corner_radius=12)
        ctrl.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0,16))
        ctk.CTkLabel(ctrl, text="Agent 1:", font=FONT_BODY, text_color=TEXT_SECONDARY).pack(side="left", padx=(14,4), pady=10)
        self._a1_var = tk.StringVar(value="backtracking")
        ctk.CTkOptionMenu(ctrl, values=list(ALGO_NAMES.values()),
                           variable=tk.StringVar(value=ALGO_NAMES["backtracking"]),
                           fg_color=BG_SURFACE2, button_color=VIOLET,
                           command=lambda v: self._a1_var.set(self._name_to_key(v))
                           ).pack(side="left", padx=4)
        ctk.CTkLabel(ctrl, text="vs", font=FONT_HEADING, text_color=ORCHID).pack(side="left", padx=8)
        self._a2_var = tk.StringVar(value="ac3mrv")
        ctk.CTkOptionMenu(ctrl, values=list(ALGO_NAMES.values()),
                           variable=tk.StringVar(value=ALGO_NAMES["ac3mrv"]),
                           fg_color=BG_SURFACE2, button_color=TEAL,
                           command=lambda v: self._a2_var.set(self._name_to_key(v))
                           ).pack(side="left", padx=4)
        ctk.CTkLabel(ctrl, text="Difficulty:", font=FONT_BODY, text_color=TEXT_SECONDARY).pack(side="left", padx=(16,4))
        self._adv_diff = tk.StringVar(value="Medium")
        ctk.CTkOptionMenu(ctrl, values=DIFFICULTIES,
                           variable=self._adv_diff,
                           fg_color=BG_SURFACE2, button_color=VIOLET
                           ).pack(side="left", padx=4)
        self._race_btn = ctk.CTkButton(ctrl, text="⚔  Start Race",
                                        fg_color=VIOLET, hover_color=ORCHID,
                                        text_color="white", font=FONT_HEADING,
                                        corner_radius=10,
                                        command=self._start_race)
        self._race_btn.pack(side="right", padx=12, pady=8)

        # Agent panels
        self._panel1 = self._agent_panel(0, "Agent 1", ORCHID)
        self._panel2 = self._agent_panel(1, "Agent 2", TEAL)

        # Result banner
        self._result = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=12,
                                     border_width=1, border_color=BORDER)
        self._result.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(16,0))
        self._result_lbl = ctk.CTkLabel(self._result, text="",
                                         font=FONT_HEADING, text_color=GREEN)
        self._result_lbl.pack(pady=14)

    def _agent_panel(self, col, label, color):
        frame = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=14,
                              border_width=1, border_color=BORDER)
        frame.grid(row=2, column=col, sticky="nsew", padx=(0 if col else 0, 8 if col==0 else 0))
        frame.columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(frame, fg_color=BG_SURFACE2, corner_radius=10)
        hdr.pack(fill="x", padx=12, pady=(12,8))
        crown = ctk.CTkLabel(hdr, text="", font=("Segoe UI Emoji",18))
        crown.pack(side="right", padx=8)
        name_lbl = ctk.CTkLabel(hdr, text=label, font=FONT_HEADING, text_color=color)
        name_lbl.pack(side="left", padx=12, pady=6)
        algo_lbl = ctk.CTkLabel(hdr, text=ALGO_NAMES["backtracking" if col==0 else "ac3mrv"],
                                  font=FONT_SMALL, text_color=TEXT_MUTED)
        algo_lbl.pack(side="left")

        board = SudokuBoard(frame, cell_size=40)
        board.pack(padx=12)

        met = ctk.CTkFrame(frame, fg_color=BG_SURFACE)
        met.pack(fill="x", padx=12, pady=8)
        met.columnconfigure((0,1), weight=1)
        t_lbl = ctk.CTkLabel(met, text="—", font=FONT_METRIC, text_color=color)
        t_lbl.grid(row=0, column=0, padx=8, pady=4)
        ctk.CTkLabel(met, text="ms", font=FONT_SMALL, text_color=TEXT_MUTED).grid(row=1,column=0)
        s_lbl = ctk.CTkLabel(met, text="—", font=FONT_METRIC, text_color=color)
        s_lbl.grid(row=0, column=1, padx=8, pady=4)
        ctk.CTkLabel(met, text="states", font=FONT_SMALL, text_color=TEXT_MUTED).grid(row=1,column=1)

        return {"frame":frame, "board":board, "algo_lbl":algo_lbl,
                "t_lbl":t_lbl, "s_lbl":s_lbl, "crown":crown}

    @staticmethod
    def _name_to_key(name):
        return {v:k for k,v in ALGO_NAMES.items()}.get(name, "backtracking")

    def _start_race(self):
        if self._running:
            return
        self._running = True
        self._race_btn.configure(state="disabled", text="Racing…")
        self._result_lbl.configure(text="")

        a1 = self._a1_var.get()
        a2 = self._a2_var.get()
        diff = self._adv_diff.get()

        self._panel1["algo_lbl"].configure(text=ALGO_NAMES[a1])
        self._panel2["algo_lbl"].configure(text=ALGO_NAMES[a2])
        self._panel1["crown"].configure(text="")
        self._panel2["crown"].configure(text="")

        puzzle, _ = generate_puzzle(diff)
        self._panel1["board"].load_puzzle(puzzle)
        self._panel2["board"].load_puzzle(puzzle)

        def _run():
            import copy
            r1 = fast_solve(a1, copy.deepcopy(puzzle))
            r2 = fast_solve(a2, copy.deepcopy(puzzle))
            self.after(0, self._on_race_done, r1, r2, a1, a2, puzzle)

        threading.Thread(target=_run, daemon=True).start()

    def _on_race_done(self, r1, r2, a1, a2, puzzle):
        self._running = False
        self._race_btn.configure(state="normal", text="⚔  Start Race")
        given = [[v!=0 for v in row] for row in puzzle]

        self._panel1["t_lbl"].configure(text=f"{r1['time_ms']:.1f}")
        self._panel1["s_lbl"].configure(text=f"{r1['states']:,}")
        self._panel2["t_lbl"].configure(text=f"{r2['time_ms']:.1f}")
        self._panel2["s_lbl"].configure(text=f"{r2['states']:,}")

        if r1.get("solved"):
            self._panel1["board"].mark_all_solved(r1["board"])
        if r2.get("solved"):
            self._panel2["board"].mark_all_solved(r2["board"])

        winner = 1 if r1["time_ms"] <= r2["time_ms"] else 2
        self._panel1["crown"].configure(text="👑" if winner==1 else "")
        self._panel2["crown"].configure(text="👑" if winner==2 else "")
        ratio = max(r1["time_ms"],r2["time_ms"]) / max(min(r1["time_ms"],r2["time_ms"]),0.01)
        win_name = ALGO_NAMES[a1 if winner==1 else a2]
        self._result_lbl.configure(
            text=f"🏆  {win_name} wins!  ·  {ratio:.1f}× faster  "
                 f"·  States: {r1['states']:,} vs {r2['states']:,}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# Helper widget factories
# ══════════════════════════════════════════════════════════════════════════════

def _label(parent, text, color=TEXT_SECONDARY, size=11):
    return ctk.CTkLabel(parent, text=text, font=("Segoe UI", size),
                        text_color=color)

def _sep(parent):
    return ctk.CTkFrame(parent, fg_color=BORDER, height=1)

def _tag_btn(parent, text, color, cmd):
    return ctk.CTkButton(parent, text=text, fg_color=BG_SURFACE2,
                         hover_color=BG_SURFACE, text_color=TEXT_SECONDARY,
                         font=FONT_BODY, corner_radius=8, height=34,
                         command=cmd)

def _algo_btn(parent, algo_key, cmd):
    return ctk.CTkButton(parent, text=ALGO_NAMES[algo_key],
                         fg_color=BG_SURFACE2, hover_color=BG_SURFACE,
                         text_color=TEXT_SECONDARY, font=FONT_SMALL,
                         corner_radius=8, height=36, anchor="w",
                         command=cmd)


# ══════════════════════════════════════════════════════════════════════════════
# Main Application Window
# ══════════════════════════════════════════════════════════════════════════════

class SudokuApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("AI Sudoku Solver & Evaluator  —  CSC202")
        self.geometry("1280x820")
        self.minsize(1100, 720)
        self.configure(fg_color=BG_DARK)
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # ── Top header bar ──────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=BG_MID, corner_radius=0, height=60)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="🧩", font=("Segoe UI Emoji",22)).pack(side="left", padx=(16,4), pady=10)
        ctk.CTkLabel(header, text="AI SUDOKU SOLVER", font=FONT_TITLE,
                     text_color=ORCHID).pack(side="left", padx=4)
        ctk.CTkLabel(header, text="CSC202  ·  UET Lahore  ·  Constraint Satisfaction Problem",
                     font=FONT_SMALL, text_color=TEXT_MUTED).pack(side="left", padx=16)

        # ── Tab bar ─────────────────────────────────────────────────────────
        tab_bar = ctk.CTkFrame(self, fg_color=BG_MID, corner_radius=0, height=44)
        tab_bar.grid(row=1, column=0, sticky="new")
        self._tabs = {}
        self._tab_frames = {}
        tab_names = [
            ("🎮 Solver", "solver"),
            ("📊 Performance", "perf"),
            ("📚 CSP Theory", "theory"),
            ("⚔ Adversarial", "adv"),
        ]
        for label, key in tab_names:
            b = ctk.CTkButton(tab_bar, text=label,
                               fg_color=BG_MID, hover_color=BG_SURFACE,
                               text_color=TEXT_SECONDARY,
                               font=FONT_BODY, corner_radius=0,
                               width=150, height=44,
                               command=lambda k=key: self._switch_tab(k))
            b.pack(side="left")
            self._tabs[key] = b

        # ── Content area ─────────────────────────────────────────────────────
        content = ctk.CTkFrame(self, fg_color=BG_DARK)
        content.grid(row=2, column=0, sticky="nsew", padx=20, pady=16)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._tab_frames["solver"] = SolverTab(content)
        self._tab_frames["perf"]   = PerformanceTab(content)
        self._tab_frames["theory"] = TheoryTab(content)
        self._tab_frames["adv"]    = AdversarialTab(content)

        for frame in self._tab_frames.values():
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_remove()

        self._switch_tab("solver")

    def _switch_tab(self, key):
        for k, frame in self._tab_frames.items():
            frame.grid_remove()
        self._tab_frames[key].grid()
        for k, btn in self._tabs.items():
            btn.configure(
                fg_color=VIOLET if k == key else BG_MID,
                text_color=TEXT_PRIMARY if k == key else TEXT_SECONDARY,
            )


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = SudokuApp()
    app.mainloop()