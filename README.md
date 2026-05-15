<div align="center">

```
   ██████╗ ██████╗ ██████╗ ███████╗     █████╗ ██████╗  ██████╗██╗  ██╗
  ██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔══██╗██╔══██╗██╔════╝██║  ██║
  ██║     ██║   ██║██║  ██║█████╗      ███████║██████╔╝██║     ███████║
  ██║     ██║   ██║██║  ██║██╔══╝      ██╔══██║██╔══██╗██║     ██╔══██║
  ╚██████╗╚██████╔╝██████╔╝███████╗    ██║  ██║██║  ██║╚██████╗██║  ██║
   ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝

  ░█████╗░██████╗░░█████╗░██╗░░██╗░█████╗░███████╗░█████╗░██╗░░░░░░█████╗░░██████╗░██╗░██████╗████████╗
  ██╔══██╗██╔══██╗██╔══██╗██║░░██║██╔══██╗██╔════╝██╔══██╗██║░░░░░██╔══██╗██╔════╝░██║██╔════╝╚══██╔══╝
  ███████║██████╔╝██║░░╚═╝███████║███████║█████╗░░██║░░██║██║░░░░░██║░░██║██║░░██╗░██║╚█████╗░░░░██║░░░
  ██╔══██║██╔══██╗██║░░██╗██╔══██║██╔══██║██╔══╝░░██║░░██║██║░░░░░██║░░██║██║░░╚██╗██║░╚═══██╗░░░██║░░░
  ██║░░██║██║░░██║╚█████╔╝██║░░██║██║░░██║███████╗╚█████╔╝███████╗╚█████╔╝╚██████╔╝██║██████╔╝░░░██║░░░
```

# 🕵️ Code Archaeologist

**Excavate the mysteries buried in your codebase.**

A developer productivity tool that analyzes legacy and messy codebases — surfacing dead code, complexity hotspots, and a narrative story of how the code evolved.

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018-61DAFB?style=flat-square&logo=react)](https://reactjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen?style=flat-square)]()

</div>

---

## 📖 What is this?

Ever stared at someone else's code (or your own from 6 months ago) and asked **"what on earth was I thinking?"**

Code Archaeologist is a full-stack tool that does the detective work for you. Upload your Python files and get back:

- A **WTF Score** that objectively measures how cursed each function is
- A **Fossil Report** listing dead code accumulating like dust
- **Plain-English summaries** of what each function actually does
- A **visual heatmap** of complexity across your entire codebase
- A **narrative timeline** of how the code evolved — panic commits and all

> *Built with curiosity, caffeine, and a deep respect for cursed legacy code.*

---

## ✨ Features

### 🦕 Fossil Detector
Identifies dead code artifacts left behind over time — functions declared but never called, variables assigned but never used, commented-out blocks, and unreachable branches.

### 😵 WTF Score
Every file and function gets a **WTF Score (0–100)** based on objective complexity metrics:
- Cryptic variable names (`x`, `tmp2`, `asdf`)
- Deep nesting levels (3+ = 🚩)
- Magic numbers with no explanation
- Absence of comments in complex logic

A **"Top 5 Most Cursed Functions"** leaderboard is generated per upload.

### 🧠 Intent Analyzer
Uses NLP to infer what a developer *meant* to write — even when the code is unclear. Powered by `Salesforce/codet5-base-codsum`.

```
calc_x(a, b)  →  "Appears to be an incomplete price discount calculator"
```

### 🗺️ Complexity Heatmap
Color-coded from 🟢 green (clean) to 🔴 red (complex). Drill into any file or function with animated reveal via Framer Motion.

### 📜 Code Story Timeline
Reconstructs the "chapters" of your codebase's development from comments, naming patterns, and logic flow. Detects signs of panic-driven development — e.g., files named `fix_FINAL_v2_REAL.py`.

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Frontend** | React 18, Tailwind CSS, Framer Motion | Fast, modern, internship-relevant |
| **Backend** | FastAPI (Python 3.11+) | Async-ready, auto-docs at `/docs` |
| **Code Parsing** | Python `ast`, `tree-sitter` | Native AST access without dependencies |
| **NLP** | HuggingFace Transformers, spaCy | Pretrained models, no training required |
| **Metrics** | `radon` | Industry-standard cyclomatic complexity |
| **Visualization** | Recharts, D3.js | Flexible charting for heatmaps |
| **Testing** | Pytest (backend), Vitest (frontend) | Standard in production codebases |

---

## 📁 Project Structure

```
code-archaeologist/
│
├── backend/
│   ├── app/
│   │   ├── main.py                  ← FastAPI app entry point + CORS
│   │   ├── routers/
│   │   │   ├── upload.py            ← POST /api/upload
│   │   │   └── analysis.py          ← GET /api/analysis/{session_id}
│   │   ├── services/
│   │   │   ├── fossil_detector.py   ← Dead code detection via AST
│   │   │   ├── wtf_scorer.py        ← WTF Score heuristics + radon
│   │   │   ├── intent_analyzer.py   ← HuggingFace code summarization
│   │   │   └── story_generator.py   ← Narrative generation from metadata
│   │   └── models/
│   │       └── schemas.py           ← Pydantic request/response models
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FossilDetector.jsx
│   │   │   ├── WTFLeaderboard.jsx
│   │   │   ├── ComplexityHeatmap.jsx
│   │   │   ├── CodeStoryTimeline.jsx
│   │   │   └── IntentAnalyzer.jsx
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   └── Dashboard.jsx
│   │   └── App.jsx
│   └── package.json
│
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| pip | latest |
| git | any |

### 1. Clone the Repository

```bash
git clone https://github.com/insha-parveen/code-archaeologist.git
cd code-archaeologist
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --port 8000
```

✅ API running at: `http://localhost:8000`
📚 Interactive API docs at: `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
# In a new terminal tab
cd frontend

npm install
npm run dev
```

✅ App running at: `http://localhost:5173`

---

## 📡 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Health check |
| `/api/upload` | `POST` | Upload one or more `.py` files |
| `/api/analysis/{session_id}` | `GET` | Full analysis report for a session |
| `/api/analysis/{session_id}/leaderboard` | `GET` | Top 5 Most Cursed Functions |

---

## 🧪 NLP Pipeline

```
  Uploaded .py Files
         │
         ▼
  AST / Tree-sitter Parsing
         │
         ├──► Fossil Detection    →  static analysis (unused vars, dead code)
         ├──► WTF Scoring         →  radon + heuristics (nesting, magic numbers)
         ├──► Intent Inference    →  HuggingFace codet5 (plain-English summaries)
         └──► Story Generation    →  narrative from metadata + naming patterns
                   │
                   ▼
         JSON Response  →  React Dashboard
```

**Key models & libraries:**

| Tool | Purpose |
|---|---|
| `Salesforce/codet5-base-codsum` | Code summarization for intent analysis |
| `radon` | Cyclomatic complexity + maintainability index |
| `spaCy` | Entity extraction from comments and docstrings |
| Python `ast` | Native abstract syntax tree parsing |

---

## 🗺️ Roadmap

- [x] Python file support
- [x] WTF Score + Leaderboard
- [x] Fossil Detection (dead code)
- [x] FastAPI backend + React frontend scaffold
- [ ] Intent Analyzer (NLP summaries)
- [ ] Complexity Heatmap visualization
- [ ] Code Story Timeline
- [ ] JavaScript / TypeScript support
- [ ] GitHub repository URL input (no manual upload needed)
- [ ] Exportable PDF report
- [ ] VS Code extension
- [ ] Multi-language support (Java, Go)

---

## 🤝 Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change.

```bash
# Fork the repo, then:
git checkout -b feature/your-feature-name
git commit -m "feat: describe your change"
git push origin feature/your-feature-name
# Open a Pull Request
```

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages:

| Prefix | When to use |
|---|---|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `chore:` | Setup, config, tooling |
| `docs:` | Documentation only |
| `refactor:` | Code restructuring, no behaviour change |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built by** [Insha Parveen](https://github.com/insha-parveen) 
*If this helped you, leave a ⭐ — it means a lot.*

</div>