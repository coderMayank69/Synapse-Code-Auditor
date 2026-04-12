# SYNAPSE CODE AUDITOR

> **AI-powered code review that catches what humans miss.**

[![HuggingFace](https://img.shields.io/badge/HuggingFace-Space-yellow?logo=huggingface)](https://huggingface.co/spaces/coderMayank69/Synapse_Code_Auditor)
[![License: MIT](https://img.shields.io/badge/License-MIT-white.svg)](LICENSE)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org/)
[![Groq](https://img.shields.io/badge/Powered%20by-Groq-orange)](https://groq.com)

Synapse Code Auditor is a production-ready AI code review system. It detects security vulnerabilities, race conditions, architectural issues, and performance problems in AI-generated code — in under 8 seconds.

---

## Why Synapse

AI writes code that *looks* correct but hides real bugs. Synapse is trained to catch exactly those patterns:

| Category       | Examples                                             |
|----------------|------------------------------------------------------|
| **Security**   | SQL injection, XSS, hardcoded secrets, OWASP Top 10 |
| **Concurrency**| Race conditions, missing locks, async misuse         |
| **Architecture**| Blocking I/O, missing error handling, bad design   |
| **Performance**| N+1 queries, unnecessary allocations, no caching    |
| **Quality**    | 0–100 score + corrected code in every review        |

---

## Repository Structure

```
.
├── landing/               # Next.js landing page + live demo
│   ├── src/app/
│   │   ├── page.tsx       # Main landing page
│   │   ├── layout.tsx     # Root layout + SEO metadata
│   │   ├── globals.css    # Design system (Bebas Neue, dark minimal)
│   │   ├── api/audit/
│   │   │   └── route.ts   # POST /api/audit — Groq integration
│   │   └── components/
│   │       └── CodeAuditor.tsx  # Interactive live demo component
│   ├── .env.example       # Environment variable template
│   ├── vercel.json        # Vercel deployment config
│   └── package.json
│
├── app/                   # Python OpenEnv environment (RL backend)
│   ├── env.py             # OpenEnv environment class
│   ├── grader.py          # Deterministic code review grader
│   ├── tasks.py           # 3 tasks: easy / medium / hard
│   ├── models.py          # Pydantic models
│   └── main.py            # FastAPI server
│
├── inference.py           # Baseline RL inference runner
├── validate_submission.py # Pre-submission validator
├── openenv.yaml           # OpenEnv manifest
├── Dockerfile             # Docker build for HuggingFace Spaces
└── requirements.txt       # Python dependencies
```

---

## Quick Start — Landing Page

### 1. Clone and install

```bash
git clone https://github.com/coderMayank69/Synapse-Code-Auditor.git
cd Synapse-Code-Auditor/landing
npm install
```

### 2. Set environment variable

```bash
cp .env.example .env.local
# Edit .env.local and add your GROQ_API_KEY
# Get one free at https://console.groq.com
```

```env
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Run dev server

```bash
npm run dev
# Open http://localhost:3000
```

---

## Deploy to Vercel (1 click)

```bash
cd landing
npx vercel --prod
```

Then set `GROQ_API_KEY` in **Vercel → Project → Settings → Environment Variables**.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/coderMayank69/Synapse-Code-Auditor&project-name=synapse-code-auditor&env=GROQ_API_KEY&envDescription=Your%20Groq%20API%20key)

---

## API Reference

### `POST /api/audit`

Analyze any code snippet and receive a structured review.

**Request**
```json
{
  "code": "def auth(u, p, db): ...",
  "language": "python"
}
```

**Response**
```json
{
  "review": "## 🔴 Critical Issues\n...",
  "model": "llama-3.3-70b-versatile",
  "usage": {
    "prompt_tokens": 312,
    "completion_tokens": 487,
    "total_tokens": 799
  }
}
```

Supported languages: `python`, `javascript`, `typescript`, `go`, `rust`, `java`, `cpp`, `sql`

---

## IDE Integration

Call `/api/audit` from any editor, script, or CI pipeline:

```python
import requests

def audit_file(path: str, api_url: str = "https://your-app.vercel.app/api/audit"):
    with open(path) as f:
        code = f.read()

    res = requests.post(api_url, json={"code": code, "language": "python"})
    print(res.json()["review"])

audit_file("my_module.py")
```

**VS Code Task (`tasks.json`)**
```json
{
  "version": "2.0.0",
  "tasks": [{
    "label": "Synapse Audit",
    "type": "shell",
    "command": "python synapse_audit.py ${file}",
    "problemMatcher": []
  }]
}
```

**Pre-commit hook**
```bash
#!/bin/sh
python synapse_audit.py $(git diff --cached --name-only --diff-filter=AM | grep '\.py$')
```

---

## OpenEnv Backend (RL Environment)

The Python backend implements the [OpenEnv](https://huggingface.co/spaces/coderMayank69/Synapse_Code_Auditor) interface for training RL agents to review code.

### Local run

```bash
python -m venv .venv
. .venv/Scripts/activate      # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 7860
```

### Endpoints

| Method | Path     | Description                        |
|--------|----------|------------------------------------|
| GET    | /health  | Health check                       |
| POST   | /reset   | Start new task (`easy/medium/hard`) |
| POST   | /step    | Submit review, receive reward      |
| GET    | /state   | Current environment state          |

### Tasks

| Task   | Description                       | Difficulty |
|--------|-----------------------------------|------------|
| easy   | Detect SQL injection vulnerability | ⭐         |
| medium | Identify async race condition      | ⭐⭐       |
| hard   | Full FastAPI endpoint review       | ⭐⭐⭐     |

### Reward formula

```
raw_score = criterion_coverage − penalties
score     = clamp(raw_score, 0.01, 0.99)
```

### Run baseline inference

```bash
export GROQ_API_KEY="your_key"
export ENV_BASE_URL="http://localhost:7860"
python inference.py
```

### Docker

```bash
docker build -t synapse-code-auditor .
docker run --rm -p 7860:7860 synapse-code-auditor
```

---

## Validate submission

```bash
python validate_submission.py
```

Checks: OpenEnv manifest, `/health`, `/reset`, `/step`, `/state` endpoints, 3+ tasks with graders, rewards in (0.01, 0.99), structured inference logs.

---

## Tech Stack

| Layer     | Technology                          |
|-----------|-------------------------------------|
| Frontend  | Next.js 16, TypeScript, Bebas Neue  |
| AI Model  | LLaMA 3.3 70B via Groq SDK          |
| Backend   | FastAPI, Python 3.11+               |
| RL Env    | OpenEnv, Pydantic                   |
| Deploy    | Vercel (landing), HuggingFace (RL)  |
| Container | Docker                              |

---

## License

MIT — see [LICENSE](LICENSE)

---

<p align="center">
  Built with LLaMA 3.3 70B + Groq &nbsp;·&nbsp;
  <a href="https://huggingface.co/spaces/coderMayank69/Synapse_Code_Auditor">HuggingFace Space</a>
</p>
