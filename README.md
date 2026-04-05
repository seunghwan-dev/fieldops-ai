# FieldOps-AI

[日本語版はこちら](README-ja.md)

![Python](https://img.shields.io/badge/Python-3.11-blue)
![React](https://img.shields.io/badge/React-19-61DAFB)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![Oracle](https://img.shields.io/badge/Oracle-26ai-F80000)
![Tests](https://img.shields.io/badge/Tests-50%20passed-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)

### [▶ Live Demo (GitHub Pages)](https://seunghwan-dev.github.io/fieldops-ai/)

DEMO mode — no Docker required. Toggle ML Only ↔ Fusion to see the difference.

---

## Before / After

<p align="center">
  <img src="docs/images/before-after.svg" alt="Before/After" width="100%"/>
</p>

> ML alone outputs a number — no warning, no evidence. Fusion adds domain knowledge correction with cited sources. Every output requires human approval before action.

---

## Architecture

<p align="center">
  <img src="docs/images/architecture.svg" alt="FieldOps-AI Architecture" width="100%"/>
</p>

> Cloud VLM ingests papers for maximum extraction accuracy. Track A searches the knowledge base; Track B uses ML models trained on experiment data (CSV). All prediction and reasoning runs on local GPU — zero data leaves the building, zero API cost.

---

## Features

<p align="center">
  <img src="docs/images/features.svg" alt="Features" width="100%"/>
</p>

> Three core capabilities: Domain-ML Fusion corrects predictions with evidence, RAG provides instant answers from the knowledge base, and VLM extracts structured data from research PDFs.

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| LLM | Qwen 2.5 7B (Ollama, local) | $0 cost, data sovereignty |
| VLM | GPT-4o Vision (Azure OpenAI) | Best table/figure extraction accuracy |
| Database | Oracle AI Database 26ai | Vector + BM25 hybrid in single DB |
| Embedding | multilingual-e5-large (1024d) | JP/EN/KR multilingual support |
| ML | RandomForest + SHAP | Interpretable prediction + XAI |
| Frontend | React 19 + TypeScript + Tailwind | EN/JA bilingual UI |
| Fusion | LLM Layer + Rule-based Safety | Flexible + Non-negotiable dual layer |

---

## Key Design Decisions

### 1. Equipment A vs B: different ML approaches

<p align="center">
  <img src="docs/images/equipment-a-vs-b.svg" alt="Equipment A vs B" width="100%"/>
</p>

> Equipment A has no physics formula — ML learns directly from experiment reports. Equipment B has Bond's Law, but it deviates outside a specific RPM range — ML corrects the gap.

### 2. Fusion: LLM flexible + Rule non-negotiable

<p align="center">
  <img src="docs/images/fusion-dual-layer.svg" alt="Fusion Dual-Layer" width="100%"/>
</p>

> Layer 1 (LLM) is flexible — it synthesizes evidence and suggests corrections. Layer 2 (Rule) is non-negotiable — hard-coded safety limits override everything. Two layers, zero compromise on safety.

### 3. MDSK-RAG Dual-Source Collection

Based on the [MDSK-RAG pattern (ACS JCIM)](https://pubs.acs.org/doi/10.1021/acs.jcim.5c01941), knowledge is stored in two physically separated tables.

<p align="center">
  <img src="docs/images/mdsk-rag.svg" alt="MDSK-RAG Dual-Source" width="100%"/>
</p>

> A single table mixes text knowledge with numerical data, degrading search precision. Two separate tables — literature and quantitative — allow optimized indexes for each. In production, the same pattern separates confidential from public data.

### 4. Data Sovereignty — $0 Local AI

<p align="center">
  <img src="docs/images/data-sovereignty.svg" alt="Data Sovereignty" width="100%"/>
</p>

> All AI components run on local hardware. The only cloud service (VLM) processes published papers — never customer data. Replaceable with a local model for fully local operation.

---

## Testing

```bash
docker exec -it fieldops-ai-backend-1 pytest tests/ -v --tb=short
```

| Category | Count | Strategy | Speed |
|---------|-------|---------|-------|
| A. Core API | 20 | VLM/LLM mocked, DB/ML real | ~10s |
| B. Integration | 10 | All services real (Docker required) | ~60s |
| C. Edge Cases | 10 | LLM failure injection (timeout, Chinese, invalid JSON) | ~15s |
| D. Equipment Physics | 10 | Bond's Law hybrid validation + SHAP + safety structure | ~5s |
| **Total** | **50** | | |

---

## Hardware

<p align="center">
  <img src="docs/images/hardware.svg" alt="Hardware" width="100%"/>
</p>

---

## Quick Start

```bash
git clone https://github.com/seunghwan-dev/fieldops-ai.git
cd fieldops-ai
cp .env.example .env
docker compose up -d
cd frontend && npm install && npm run dev
```

DEMO mode auto-activates when Docker is down.

---

## License

MIT
