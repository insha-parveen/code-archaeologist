# 🕵️ Code Archaeologist

> Excavate the mysteries buried in your codebase.

Code Archaeologist is a full-stack AI-powered developer productivity tool that analyzes legacy or messy codebases and surfaces hidden insights — dead code, complexity hotspots, LLM-generated function summaries, refactoring suggestions, and a narrative story of how the code evolved.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![React](https://img.shields.io/badge/React-18-blue)
![Groq](https://img.shields.io/badge/LLM-Groq%20%2F%20Llama%203.1-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📖 What is this?

Ever stared at someone else's code (or your own from 6 months ago) and asked **"what on earth was I thinking?"**

Code Archaeologist is a full-stack tool that does the detective work for you. Upload your Python files and get back:

- A **WTF Score** that objectively measures how cursed each function is
- A **Fossil Report** listing dead code accumulating like dust
- **Plain-English summaries** of what each function actually does
- A **visual heatmap** of complexity across your entire codebase
- A **narrative timeline** of how the code evolved — panic commits and all

## ✨ Features

### 🦕 Fossil Detector

Identifies dead code artifacts using AST analysis:

- Functions defined but never called
- Variables assigned but never read
- Commented-out code blocks left behind

### 😵 WTF Score

Every file and function gets a **WTF Score (0–100)** based on objective complexity metrics:

- Cryptic variable names (`x`, `tmp2`, `asdf`)
- Deep nesting levels (3+ = 🚩)
- Magic numbers with no explanation
- Absence of comments in complex logic

A **"Top 5 Most Cursed Functions"** leaderboard is generated per upload.

### 🧠 Intent Analyzer

LLM-powered plain English summaries for every function:

- Uses Groq API (Llama 3.1 8B) for real semantic understanding
- Generates targeted refactoring suggestions for high-WTF functions
- Cached — same function analyzed once, reused forever

### 📜 Code Story Timeline

Generates a narrative of the codebase's evolution:

- LLM-written prose describing development history
- Pattern-based chapter detection (panic mode, early exploration, maturity)
- Development style classification

### 🌐 Multi-Language Support

- **Python** — full AST parsing, precise fossil detection
- **JavaScript / TypeScript / JSX / TSX** — LLM-based parsing
- **Java, Go, Rust, C++, C#, Ruby, PHP, Kotlin, Swift** — universal LLM parser with regex fallback

### 🐙 GitHub Integration

- Paste any GitHub file URL → instant analysis
- Paste a repo URL → scan up to 20 files, browse results
- Handles rate limits, retries, branch resolution automatically

### ⚡ Smart Caching

- File-level cache (1hr TTL) — same file analyzed once
- Function-level LLM cache (24hr TTL) — reuses summaries across files
- Cache hit rate monitoring via `/api/cache/stats`

### 📄 PDF Export

- One-click export of full analysis report
- Programmatically generated — works across all browsers and OS

---

## 🛠️ Tech Stack

| Layer             | Technology                                 |
| ----------------- | ------------------------------------------ |
| Frontend          | React 18, Tailwind CSS v4, Vite            |
| Backend           | FastAPI (Python 3.11+)                     |
| Python Parsing    | Python `ast` module                      |
| Universal Parsing | Groq API (Llama 3.1 8B)                    |
| Metrics           | `radon`                                  |
| LLM Provider      | Groq (free tier, 14,400 req/day)           |
| GitHub Fetch      | `httpx` with retry + backoff             |
| PDF Export        | `jsPDF`                                  |
| Caching           | In-memory with TTL (Redis-ready interface) |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Groq API key (free at [console.groq.com](https://console.groq.com))
- GitHub token (optional, increases rate limits)

### 1. Clone the Repository

```bash
git clone https://github.com/insha-parveen/code-archaeologist.git
cd code-archaeologist
```

### Backend Setup

```bash
git clone https://github.com/YOUR_USERNAME/code-archaeologist.git
cd code-archaeologist/backend

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Create `backend/.env`:

```
GROQ_API_KEY=gsk_your_key_here
GITHUB_TOKEN=ghp_your_token_here   # optional
```

Start the server:

```bash
uvicorn app.main:app --reload --port 8000
```

API docs at `http://localhost:8000/docs`

### Frontend Setup

```bash
cd ../frontend
npm install
```

Create `frontend/.env`:

```
VITE_API_BASE=http://127.0.0.1:8000
```

Start the dev server:

```bash
npm run dev
```

App available at `http://localhost:5173`

---

## 📡 API Reference

| Endpoint               | Method | Description                          |
| ---------------------- | ------ | ------------------------------------ |
| `/api/upload`        | POST   | Upload a code file for full analysis |
| `/api/github`        | POST   | Analyze from a GitHub URL            |
| `/api/analysis/full` | POST   | Analyze source code sent as JSON     |
| `/api/cache/stats`   | GET    | View cache hit rates                 |
| `/api/cache/clear`   | DELETE | Clear all caches                     |

---

## 🏗️ Project Structure

```
code-archaeologist/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry point + CORS
│   │   ├── routers/
│   │   │   ├── upload.py              # File upload endpoint
│   │   │   ├── analysis.py            # Analysis + cache endpoints
│   │   │   └── github.py              # GitHub URL endpoint
│   │   └── services/
│   │       ├── ast_parser.py          # Python AST traversal
│   │       ├── wtf_scorer.py          # Complexity heuristics
│   │       ├── fossil_detector.py     # Dead code detection (Python)
│   │       ├── universal_parser.py    # LLM-based multi-language parser
│   │       ├── language_detector.py   # File extension → language mapping
│   │       ├── llm_analyzer.py        # Groq API — summaries + refactoring
│   │       ├── story_generator.py     # Narrative timeline generation
│   │       ├── github_fetcher.py      # GitHub API + raw content fetcher
│   │       └── cache.py               # In-memory cache with TTL
│   └── requirements.txt
│
└── frontend/
    └── src/
        ├── pages/
        │   ├── Home.jsx               # Upload + GitHub URL input
        │   ├── Dashboard.jsx          # Single file results
        │   └── MultiResults.jsx       # Multi-file repo results
        ├── components/
        │   ├── WTFLeaderboard.jsx     # Top cursed functions panel
        │   ├── FossilDetector.jsx     # Dead code panel
        │   ├── CodeStoryTimeline.jsx  # Story chapters timeline
        │   ├── ExportButton.jsx       # PDF export trigger
        │   └── GalaxyBackground.jsx   # Animated canvas background
        ├── hooks/
        │   └── useExportPDF.js        # jsPDF programmatic export
        └── config.js                  # API base URL configuration
```

---

## 🧠 Architecture Decisions

**Why Groq instead of local models?**
Local models (CodeT5, Llama via Ollama) require 4-8GB downloads and are slow on CPU. Groq runs Llama 3.1 on specialized LPU hardware — same model, 10x faster, free tier sufficient for a portfolio project.

**Why AST for Python but LLM for other languages?**
Python's built-in `ast` module is precise, fast, and free. For other languages, language-specific parsers (tree-sitter) have version conflicts across platforms. LLM-based parsing is universal, zero-dependency, and handles any language automatically.

**Why in-memory cache instead of Redis?**
Redis requires a separate service to run. The cache is built with a Redis-compatible interface — swapping to Redis in production requires changing two lines. This keeps the dev setup simple without sacrificing the architecture.

**Why jsPDF instead of html2canvas?**
Tailwind v4 uses oklch() color space which html2canvas cannot parse. Programmatic PDF generation via jsPDF avoids the dependency entirely and produces cleaner output.

---


## 📄 License

MIT License. See `LICENSE` for details.

---

*Built with curiosity, caffeine, and a deep respect for cursed legacy code.*


**By** [Insha Parveen](https://github.com/insha-parveen)
*If this helped you, leave a ⭐ — it means a lot.*
