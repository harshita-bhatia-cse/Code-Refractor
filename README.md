# Code Refactorer (AI-Based)

## Tech Stack
- FastAPI (Backend)
- Vanilla JS + HTML/CSS (Frontend)
- GitHub OAuth
- JWT Authentication

---

## 1️⃣ Clone Repository
```bash
git clone https://github.com/<username>/Code-Refactorer.git
cd Code-Refactorer

Code Refactorer is an AI-driven backend system designed to analyze source code repositories and individual code files, detect:

Programming languages used

Code structure and hierarchy

Metrics (lines, functions, classes, conditionals, libraries)

Multi-language code inside a single file (HTML + CSS + JS)

Python domain classification (ML / DL / NLP / Backend / General)

Architectural patterns and style issues (foundation built)

The project is built as a modular AI-agent system, where each agent is responsible for a specific analysis task.

Frontend (HTML/JS)
        ↓
FastAPI Backend
        ↓
AI Orchestrator Agent
        ↓
Core Analysis Engine
        ↓
Language + Metrics + Domain Agents

backend/
│
├── api/
│   ├── routes/
│   │   ├── analyze.py
│   │   ├── login.py
│   │   ├── files.py
│   │   ├── code.py
│   │   ├── profile.py
│   │   └── repos.py
│   │
│   └── auth/
│       └── jwt_manager.py
│
├── ai_agents/
│   ├── orchestrator.py
│   │
│   ├── core/
│   │   ├── engine.py
│   │   ├── file_scanner.py
│   │   ├── language_detector.py
│   │   ├── language_registry.py
│   │   ├── analysis_context.py
│   │   └── code_segmenter.py
│   │
│   ├── metrics/
│   │   ├── common_metrics.py
│   │   ├── python_metrics.py
│   │   ├── java_metrics.py
│   │   ├── js_metrics.py
│   │   ├── ts_metrics.py
│   │   ├── c_metrics.py
│   │   ├── cpp_metrics.py
│   │   ├── csharp_metrics.py
│   │   ├── go_metrics.py
│   │   ├── php_metrics.py
│   │   ├── rust_metrics.py
│   │   └── metrics_aggregator.py
│   │
│   ├── domain/
│   │   └── python_domain_classifier.py
│   │
│   ├── naming/
│   │   └── naming_agent.py
│   │
│   ├── structure/
│   │   └── structure_agent.py
│   │
│   ├── style/
│   │   ├── common_style.py
│   │   ├── python_style.py
│   │   └── java_style.py
│   │
│   └── __init__.py
│
│
├── main.py
└── requirements.txt

🧩 Detailed File-by-File Explanation
🔹 backend/main.py

Entry point of the FastAPI application

Registers all API routes

Starts the backend server

🔐 Authentication Layer
backend/api/auth/jwt_manager.py

Creates and validates JWT tokens

Used for protecting analysis endpoints

Enables per-user authorization

backend/api/routes/login.py

Simple login endpoint (username → JWT)

Designed for development and MVP usage

Replaces hard-coded tokens

🌐 API Routes
analyze.py

Single-file analysis endpoint

Accepts raw code (from GitHub raw URL)

Returns live AI analysis (no file storage)

repos.py

Handles GitHub repository selection

Used by frontend dashboard

files.py

Fetches file lists from selected repo

code.py

Loads and displays file contents in viewer

profile.py

User profile related APIs

🧠 AI Orchestration Layer
ai_agents/orchestrator.py

The brain of the system

Responsibilities:

Coordinates repo-level and file-level analysis

Invokes core engine

Routes code to correct language & domain analyzers

Aggregates results

⚙️ Core Analysis Engine
engine.py

Iterates through repository files

Calls file scanner + language detection

Passes code to appropriate analyzer

file_scanner.py

Recursively scans repository directories

Reads source files safely

language_detector.py

Detects language from:

File extension

Code syntax (fallback)

Supports multi-language scenarios

language_registry.py

Central registry mapping:

language → metrics analyzer


Makes system extensible

code_segmenter.py

Splits single files with multiple languages

HTML

<style> → CSS

<script> → JavaScript

Tracks start line numbers per language

📊 Metrics System
common_metrics.py

Default metrics for unknown languages

Counts:

Lines

Functions

Classes

Conditionals

Language-Specific Metrics Files

Each file analyzes syntax specific to the language:

File	Language
python_metrics.py	Python
java_metrics.py	Java
js_metrics.py	JavaScript
ts_metrics.py	TypeScript
c_metrics.py	C
cpp_metrics.py	C++
csharp_metrics.py	C#
go_metrics.py	Go
php_metrics.py	PHP
rust_metrics.py	Rust

Metrics include:

Functions

Classes

Loops

Conditionals

Library / import detection

🧠 Python Domain Intelligence
domain/python_domain_classifier.py

Analyzes Python code to determine domain:

Machine Learning

Deep Learning

NLP

Backend / API

General scripting

Uses:

Import pattern analysis

Keyword frequency

Framework detection

🧱 Structural & Style Agents
structure_agent.py

Analyzes project folder hierarchy

Detects architectural patterns

naming_agent.py

Checks naming conventions

Identifies anti-patterns

style/

Language-specific style rule foundation

Ready for lint-level expansion

📦 Output Handling
metrics_aggregator.py

Aggregates repo analysis

Saves structured output to JSON

Excluded from Git intentionally

analysis_output/repo_metrics.json

Runtime-generated

Not committed

Used for future dashboards and exports