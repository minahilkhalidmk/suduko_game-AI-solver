
🧩 Sudoku Solver AIAn intelligent web application that solves any valid 9x9 Sudoku puzzle instantly using advanced artificial intelligence search algorithms. The system allows users to input custom boards, generates randomized puzzles across varying difficulties, and visualizes the AI's backtracking and constraint satisfaction process in real time.🚀 FeaturesIntelligent Solvers: Combines recursive backtracking search with forward checking for lightning-fast puzzle completion.Real-time Visualization: Watch the AI dynamically try, fail, and backtrack numbers directly on the grid UI.Difficulty Generator: Generates valid boards categorized by Easy, Medium, Hard, and Expert levels.Input Validation: Automatically flags invalid initial configurations (e.g., duplicate numbers in rows, columns, or 3x3 grids) before triggering the solver.Leaderboard & History: Saves user solving times and AI benchmarking stats to the cloud.🛠️ Tech StackFrontend: React (Vite)Backend / Database: Firebase (Authentication and Cloud Firestore)Styling: Tailwind CSS🧠 AI Techniques UsedThis application leverages core Artificial Intelligence and Constraint Satisfaction Problem (CSP) techniques:Backtracking Search: A depth-first search approach that systematically tests values for empty cells.Constraint Propagation: Applies Sudoku rule constraints to eliminate invalid numbers early in the search tree.Heuristics (Optional/Customizable): Implements Minimum Remaining Values (MRV) to prioritize cells with the fewest possible legal moves, drastically reducing execution time.💻 Getting Started1. Clone the Repositorybashgit clone https://github.com

cd sudoku-solver-ai

Use code with caution.2. Install Dependenciesbashnpm install

Use code with caution.3. Set Up Environment VariablesCreate a .env file in the root directory and add your Firebase credentials:envVITE_FIREBASE_API_KEY=your_api_key_here

VITE_FIREBASE_AUTH_DOMAIN=your_auth_domain_here


VITE_FIREBASE_PROJECT_ID=your_project_id_here

VITE_FIREBASE_STORAGE_BUCKET=your_storage_bucket_here

VITE_FIREBASE_MESSAGING_SENDER_ID=your_messaging_sender_id_here

VITE_FIREBASE_APP_ID=your_app_id_here


Use code with caution.4. Run Locallybashnpm run dev

Use code with caution.Open your browser and navigate to http://localhost:5173.📁 Project Structuretext├── public/                # Static assets and icons

├── src/

│   ├── components/        # Sudoku Grid, Controls, and Leaderboard components

│   ├── firebase/          # Firebase initialization and database services

│   ├── solver/            # Core AI logic (CSPs, validation, logic steps)

│   │   ├── sudokuEngine.js

│   │   └── heuristics.js

│   ├── App.jsx            # Layout manager

│   └── main.jsx           # App entry point

├── .env                   # Local variables (git ignored)

├── package.json           # Scripts and dependency configurations

└── README.md              # Documentation

Use code with caution.🌐 DeploymentInstall Firebase CLI:bashnpm install -g firebase-tools

Use code with caution.Authenticate and Build:bashfirebase login

npm run build

Use code with caution.Deploy:bashfirebase deploy

Use code with caution.




