import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.ticker as ticker

from theme import (
    BG_DARK, BG_MID, BG_SURFACE, BG_SURFACE2,
    VIOLET, ORCHID, LAVENDER, LILAC, MAGENTA_HINT,
    TEAL, CORAL, AMBER, GREEN,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    BORDER, ALGO_COLORS, ALGO_NAMES
)
from performance import DIFFICULTIES, ALGORITHMS

class ChartFrame(ctk.CTkFrame):
    def __init__(self, master, results, **kwargs):
        super().__init__(master, fg_color=BG_DARK, **kwargs)
        self.results = results

        # Create Matplotlib Figure
        self.fig = Figure(figsize=(10, 6.5), dpi=100)
        self.fig.patch.set_facecolor(BG_DARK)

        # Create 2x2 grid of subplots
        self.axs = self.fig.subplots(2, 2)

        # Style helper for subplots
        def style_ax(ax, title, ylabel):
            ax.set_facecolor(BG_SURFACE)
            ax.set_title(title, color=TEXT_PRIMARY, fontname="Segoe UI", fontsize=11, fontweight="bold", pad=10)
            if ylabel:
                ax.set_ylabel(ylabel, color=TEXT_SECONDARY, fontname="Segoe UI", fontsize=9)
            ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
            ax.xaxis.label.set_color(TEXT_SECONDARY)
            ax.yaxis.label.set_color(TEXT_SECONDARY)

            # Style the spines (axes borders)
            for spine in ax.spines.values():
                spine.set_color(BORDER)
                spine.set_linewidth(1.5)

            # Add subtle grid
            ax.grid(True, linestyle="--", color=BORDER, alpha=0.5)

        # ── 1. Solve Time (ms) - Log scale ───────────────────────────────────
        ax_time = self.axs[0, 0]
        style_ax(ax_time, "Solve Time by Difficulty (log scale)", "Time (ms)")

        # ── 2. Search Space (States Explored) - Log scale ───────────────────
        ax_states = self.axs[0, 1]
        style_ax(ax_states, "States Explored (log scale)", "States")

        # ── 3. Backtrack Operations - Symlog scale ───────────────────────────
        ax_backs = self.axs[1, 0]
        style_ax(ax_backs, "Backtrack Operations (symlog scale)", "Backtracks")

        # Plot data for the three line charts
        for algo in ALGORITHMS:
            color = ALGO_COLORS.get(algo, ORCHID)
            name = ALGO_NAMES.get(algo, algo)

            # Times
            times = results.times_by_difficulty(algo)
            ax_time.plot(DIFFICULTIES, times, marker='o', linewidth=2.5, markersize=6, color=color, label=name)

            # States
            states = results.states_by_difficulty(algo)
            ax_states.plot(DIFFICULTIES, states, marker='s', linewidth=2.5, markersize=6, color=color, label=name)

            # Backtracks
            backs = results.backs_by_difficulty(algo)
            ax_backs.plot(DIFFICULTIES, backs, marker='^', linewidth=2.5, markersize=6, color=color, label=name)

        # Set up log scale for Solve Time
        ax_time.set_yscale('log')
        ax_time.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{y:g}"))

        # Set up log scale for States Explored
        ax_states.set_yscale('log')
        ax_states.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{int(y):,}"))

        # Set up symlog scale for Backtracks to handle exactly 0 backtracks correctly
        ax_backs.set_yscale('symlog', linthresh=10)
        ax_backs.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{int(y):,}"))

        # Style and place the legend
        legend = ax_time.legend(
            facecolor=BG_SURFACE,
            edgecolor=BORDER,
            labelcolor=TEXT_PRIMARY,
            loc="upper left",
            prop={"family": "Segoe UI", "size": 8}
        )
        legend.get_frame().set_linewidth(1.2)

        # ── 4. Overall Average Solve Time (Horizontal Bar Chart) ─────────────
        ax_bar = self.axs[1, 1]
        style_ax(ax_bar, "Overall Average Solve Time", "")

        avg_times = [results.avg_time(algo) for algo in ALGORITHMS]
        algo_display_names = [ALGO_NAMES.get(algo, algo) for algo in ALGORITHMS]
        colors = [ALGO_COLORS.get(algo, ORCHID) for algo in ALGORITHMS]

        bars = ax_bar.barh(
            algo_display_names,
            avg_times,
            color=colors,
            edgecolor=BORDER,
            linewidth=1.2,
            height=0.55
        )

        ax_bar.set_xlabel("Time (ms)", color=TEXT_SECONDARY, fontname="Segoe UI", fontsize=9)

        # Annotate bar values
        for bar in bars:
            width = bar.get_width()
            ax_bar.text(
                width + max(0.1, max(avg_times) * 0.02),
                bar.get_y() + bar.get_height() / 2,
                f"{width:.1f} ms",
                va='center',
                ha='left',
                color=TEXT_PRIMARY,
                fontname="Segoe UI",
                fontsize=8.5,
                fontweight="bold"
            )

        if avg_times and max(avg_times) > 0:
            ax_bar.set_xlim(0, max(avg_times) * 1.25)

        # Adjust margins/spacing automatically
        self.fig.tight_layout()

        # Embed into Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        canvas_widget.configure(bg=BG_DARK)