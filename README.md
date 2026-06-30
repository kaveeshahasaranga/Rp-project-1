# UX Lens — ML-Driven UI/UX Heuristic Evaluation System

> An automated UI/UX expert powered by Computer Vision, Deep Learning, and Mathematical DOM Analysis.

![Architecture](docs/architecture.png)

## Research Context

**Domain**: Human-Computer Interaction (HCI) & Applied Artificial Intelligence  
**Institution**: Year 4 Semester 1 Research Project  
**Goal**: Bridge the gap between subjective human UX evaluation and objective, quantifiable ML-driven analysis.

---

## System Architecture

```
React Dashboard (Port 3000)
       ↓
Express API Gateway (Port 5000) — AHP Scoring Engine
       ↓ Promise.allSettled() — parallel
┌──────────────────────────────────────────┐
│  M1: Cognitive Load   (Port 8001)        │  Flask + OpenCV + PyWavelets
│  M2: Touch Target     (Port 8002)        │  Flask + Playwright
│  M3: Visual Hierarchy (Port 8003)        │  Flask + PyTorch (TranSalNet)
└──────────────────────────────────────────┘
       ↓
MongoDB (Port 27017) + Redis (Port 6379)
```

---

## Microservice Breakdown

### 🧠 M1 — Cognitive Load & Visual Clutter Analyzer
Quantifies "perceptual noise" using three established CV metrics:

| Metric | Algorithm | Weight |
|--------|-----------|--------|
| Feature Congestion | Rosenholtz et al. (visual-clutter library) | 40% |
| Edge Density | OpenCV Canny edge detection | 30% |
| Subband Entropy | PyWavelets DWT + Shannon entropy | 30% |

**Output**: `cognitive_load_score` ∈ [0, 100] (higher = cleaner design)

### 📐 M2 — Touch Target & Responsiveness Evaluator
Algorithmically verifies WCAG compliance and ergonomic layout:

- **WCAG 2.5.8 (AA)**: ≥ 24×24 CSS px minimum
- **WCAG 2.5.5 (AAA)**: ≥ 44×44 CSS px enhanced
- **Fitts's Law**: ID = log₂(2D/W) — Index of Difficulty per element
- **DBSCAN Clustering**: Detects accidental-click risk zones

**Output**: `touch_target_score` ∈ [0, 100] + violation details

### 👁️ M3 — Visual Hierarchy & Attention Predictor
Predicts human visual attention without eye-tracking hardware:

- **Primary model**: TranSalNet-Res (ResNet50 + Transformer, SALICON-trained)
- **CPU fallback**: OpenCV Spectral Residual Saliency
- **Focus Efficiency Score**: `FES = mean_saliency(CTA) / mean_saliency(global) × 100`

**Output**: `focus_efficiency_score` ∈ [0, 100] + saliency heatmap (base64 PNG)

### ⚙️ M4 — MERN Evaluation Engine (Group Leader)
Orchestrates the system and computes the final score:

**AHP Pairwise Comparison Matrix** (Saaty scale):
```
           CL    VH    TT
CL   [ [  1,    2,    3  ],
VH     [0.5,   1,    2  ],
TT     [0.33, 0.5,   1  ] ]

Weights: CL=0.5396, VH=0.2970, TT=0.1634  (CR = 0.009 < 0.10 ✅)
```

**Final Score**:
```
Score = 0.5396 × CognitiveLoad + 0.2970 × VisualHierarchy + 0.1634 × TouchTarget
```

---

## Prerequisites

- **Node.js** 20 LTS
- **Python** 3.9 (for M1 with visual-clutter) / 3.11 (for M2, M3)
- **MongoDB** 7.0
- **Docker** + **Docker Compose** (recommended)
- **NVIDIA GPU** with CUDA (optional — M3 falls back to CPU automatically)

---

## Quick Start (Docker)

```bash
# 1. Clone and enter project
cd "Rp project 1"

# 2. Copy environment file
cp .env.example .env
# Edit .env and set JWT_SECRET to a strong random string

# 3. (Optional) Place TranSalNet weights for GPU saliency
cp /path/to/TranSalNet_Res.pth services/visual-hierarchy/models/weights/

# 4. Build and start all services
docker-compose up --build

# 5. Open dashboard
open http://localhost:3000
```

---

## Manual Setup (Development)

### 1. MongoDB
```bash
mongod --dbpath /data/db
```

### 2. M1 — Cognitive Load (Python 3.9)
```bash
cd services/cognitive-load
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py  # Runs on port 8001
```

### 3. M2 — Touch Target (Python 3.11)
```bash
cd services/touch-target
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python app.py  # Runs on port 8002
```

### 4. M3 — Visual Hierarchy (Python 3.11)
```bash
cd services/visual-hierarchy
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Optional: place TranSalNet_Res.pth in models/weights/
python app.py  # Runs on port 8003
```

### 5. M4 — Express Gateway
```bash
cd server
npm install
cp .env.example .env  # Edit with your values
npm run dev  # Runs on port 5000
```

### 6. React Dashboard
```bash
cd client
npm install
npm run dev  # Runs on port 3000
```

---

## API Reference

### Authentication
```
POST /api/auth/register   { name, email, password }   → { token, user }
POST /api/auth/login      { email, password }          → { token, user }
GET  /api/auth/me         [Bearer token]               → { user }
```

### Analysis
```
POST /api/analyze         [multipart/form-data]
  Fields: url (required), image (optional PNG/JPG)
  Returns: {
    composite_score: 0-100,
    grade: A/B/C/D/F,
    scores: { cognitive_load, visual_hierarchy, touch_target },
    details: { cognitive, saliency, touch },
    errors: [...]  // partial failures surface here
  }
```

### Reports
```
GET    /api/reports        → List all reports for authenticated user
GET    /api/reports/:id    → Single report details
DELETE /api/reports/:id    → Delete report
```

### Microservice Health Checks
```
GET http://localhost:8001/health   → M1 status
GET http://localhost:8002/health   → M2 status
GET http://localhost:8003/health   → M3 status
GET http://localhost:5000/api/health → Gateway status
```

---

## Running Tests

```bash
# M1 — Cognitive Load unit tests
cd services/cognitive-load && python -m pytest tests/ -v

# M2 — Touch Target unit tests
cd services/touch-target && python -m pytest tests/ -v

# M3 — Visual Hierarchy unit tests
cd services/visual-hierarchy && python -m pytest tests/ -v

# M4 — Express integration tests
cd server && npm test

# E2E smoke test (all services must be running)
curl -X POST http://localhost:5000/api/analyze \
  -H "Authorization: Bearer <your-token>" \
  -F "url=https://example.com" | jq .composite_score
```

---

## TranSalNet Weights Download

For GPU-accelerated saliency prediction, download the pre-trained weights:

1. Visit: https://github.com/LJOVO/TranSalNet
2. Follow the Google Drive link in the README for `TranSalNet_Res.pth`
3. Place at: `services/visual-hierarchy/models/weights/TranSalNet_Res.pth`

Without weights, the system uses OpenCV Spectral Residual Saliency automatically.

---

## Scoring Guide

| Score | Grade | Interpretation |
|-------|-------|----------------|
| 90–100 | A | Excellent UX — minimal issues |
| 75–89 | B | Good design — minor improvements needed |
| 55–74 | C | Moderate issues — redesign recommended |
| 35–54 | D | Poor UX — significant problems |
| 0–34 | F | Critical UX failures — immediate attention required |

---

## Research Novelty

1. **Objective Measurement**: Transforms subjective UX evaluation into mathematically quantifiable metrics
2. **Hybrid AI**: Combines deterministic math (M2 WCAG/Fitts) with probabilistic ML (M1 CV, M3 DNN)
3. **Explainability**: AHP weighting provides transparent, auditable scoring rationale
4. **Democratization**: Enterprise-level UX auditing at zero human-consultation cost

---

## Project Structure

```
rp-project-1/
├── docker-compose.yml
├── .env.example
├── README.md
├── client/                    # React + Vite dashboard
├── server/                    # Express API gateway
└── services/
    ├── cognitive-load/        # M1: OpenCV + PyWavelets
    ├── touch-target/          # M2: Playwright DOM
    └── visual-hierarchy/      # M3: TranSalNet CNN
```

---

## License

Academic Research Project — All rights reserved.
