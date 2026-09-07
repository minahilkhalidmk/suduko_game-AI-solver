# 🧩 Sudoku Game & AI Solver

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-CustomTkinter-7B2FBE?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![Visualization](https://img.shields.io/badge/Visualization-Matplotlib-11557c?style=for-the-badge&logo=python&logoColor=white)](https://matplotlib.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

An advanced, interactive **Sudoku Game & AI Solver** built with Python and CustomTkinter. The application combines classic Sudoku puzzle gameplay with a suite of **Constraint Satisfaction Problem (CSP)** and **Search Algorithms**, providing real-time visual step-by-step solver animation, performance benchmarking charts, interactive algorithm theory breakdowns, and an adversarial AI race mode.

---

## 🌟 Key Features

- **🎮 Interactive Sudoku Canvas**: 9×9 grid with custom clue generation, manual cell editing, difficulty controls, and real-time validity checks.
- **⚡ 4 AI Search Algorithms**:
  - **Backtracking (DFS)**: Uninformed depth-first search solver.
  - **AC-3 + MRV**: Arc Consistency 3 constraint propagation paired with Minimum Remaining Values (MRV) and Degree heuristics.
  - **Forward Checking**: Early constraint propagation to eliminate invalid cell domains before recursive branching.
  - **Simulated Annealing**: Stochastic metaheuristic optimization solver.
- **👁️ Real-Time Solver Animation**: Adjustable speed control (0ms to 200ms delay) allowing users to watch the AI test candidate values, propagate constraints, and backtrack live on the grid.
- **📊 Embedded Benchmark Dashboard**: Multi-panel Matplotlib dashboard analyzing execution time, explored search states, and backtrack operations across Easy, Medium, Hard, and Expert difficulties.
- **🏎️ Adversarial AI Race Mode**: Head-to-head competition mode running two algorithms simultaneously on identical boards to compare speed and node exploration live.
- **📖 Interactive Theory Guide**: Comprehensive documentation on CSP formulas, time/space complexities, heuristics, and algorithmic tradeoffs.

---

## 🧠 AI Solvers & Heuristics Breakdown

| Algorithm | Type | Strategy | Best Used For | Time Complexity |
| :--- | :--- | :--- | :--- | :--- |
| **Backtracking (DFS)** | Uninformed Search | Depth-First search testing valid numbers from 1 to 9. Undoes placement on conflict. | Simple puzzles | $\mathcal{O}(9^d)$ |
| **AC-3 + MRV** | CSP / Heuristic | Enforces pairwise arc consistency between peer cells; selects unassigned variable with fewest legal values remaining (MRV). | Expert puzzles / Hard CSPs | Sub-exponential |
| **Forward Checking** | CSP / Pruning | Filters domains of row/column/box neighbors whenever a number is assigned, pruning invalid subtrees early. | General board solving | Reduced search tree |
| **Simulated Annealing** | Metaheuristic | Starts with a full board and minimizes row/column conflicts via probabilistic temperature-decay swaps ($\mathbb{P} = e^{-\Delta E / T}$). | Non-deterministic optimization | $O(k \cdot N)$ iterations |

---

## 🛠️ Project Structure

```text
suduko_game-AI-solver/
├── main.py                     # Root launcher script
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
└── AI-CCP/
    └── AI-CCP/
        ├── main_gui.py         # Main CustomTkinter multi-tab application UI
        ├── algorithms.py       # Core AI search algorithms & CSP solvers
        ├── generate_puzzle.py  # Sudoku puzzle generator with unique-solution verifier
        ├── performance.py     # Benchmark suite & data metrics collector
        ├── charts.py           # Matplotlib log-scale chart renderer
        └── theme.py            # Design tokens, color palettes & fonts
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** installed on your system. Verify with:
  ```bash
  python --version
  ```

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/minahilkhalidmk/suduko_game-AI-solver.git
   cd suduko_game-AI-solver
   ```

2. **Install Required Packages**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🎯 How to Run

Launch the application directly from the workspace root:

```bash
python main.py
```

*Alternatively, you can run the GUI script directly:*
```bash
python AI-CCP/AI-CCP/main_gui.py
```

---

## 📱 Application Modules & Tabs

1. **🧩 Solver Tab**:
   - Generate puzzles categorized by **Easy** (36–40 clues), **Medium** (27–35 clues), **Hard** (20–26 clues), or **Expert** (17–19 clues).
   - Select your preferred algorithm and animation delay.
   - Click **Solve** to visualize the solution step-by-step, or **Fast Solve** for instantaneous results.
   - Use **Reset** or **Clear** to input custom Sudoku puzzles.

2. **📊 Performance Benchmark Tab**:
   - Run automated benchmarks across all 4 algorithms and 4 difficulty levels.
   - View interactive Matplotlib graphs for **Solve Time (ms)**, **States Explored**, **Backtrack Count**, and **Average Solve Speed**.

3. **📖 CSP Theory Tab**:
   - Read theoretical explanations, pseudo-code formulas, heuristic rationale, and complexity analysis for each solver.

4. **🏎️ Adversarial Mode Tab**:
   - Select two solvers (e.g., *Backtracking* vs *AC-3 + MRV*).
   - Start the race and observe live side-by-side performance metrics on identical board states.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
