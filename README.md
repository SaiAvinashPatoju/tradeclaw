# TradeClaw 🦅

> A distributed real-time crypto momentum signal delivery system.

TradeClaw detects short-lived upward momentum opportunities in crypto markets and delivers clean, actionable trade signals to an Android app — with minimal latency and no noise.

---

## 🚀 What It Does

Retail traders often miss short-lived momentum windows because market data is noisy and decision time is small. TradeClaw solves this by combining stream processing, rule-based scoring, and push-ready signal delivery in a minimal mobile interface.

Each signal includes:
- **Symbol** and entry price range
- **Score** and confidence level
- **Target %** and **Stop-loss %**
- **Expiry timestamp** (30-minute window)
- **Reason text** for explainability

---

## 🏗️ Architecture

```
Binance API / Simulator
        ↓
    Kafka Topic
        ↓
Spark Structured Streaming
        ↓
   PostgreSQL DB
        ↓
   FastAPI Backend
        ↓
 Android App (Expo React Native)
```

**Distributed demo mode:**
- Master node runs Spark Master + Kafka + PostgreSQL + API + simulator
- Additional nodes run as Spark workers

---

## 🛠️ Tech Stack

| Layer         | Technology                        |
|---------------|-----------------------------------|
| Stream broker | Apache Kafka                      |
| Stream processing | Apache Spark Structured Streaming |
| Database      | PostgreSQL                        |
| Backend API   | FastAPI (Python)                  |
| Mobile client | Expo React Native (Android)       |
| Push notifications | Firebase Cloud Messaging (FCM) |
| Containerization | Docker / Docker Compose        |

---

## 📦 Project Structure

```
tradeclaw/
├── backend/          # FastAPI service, rule engine, Spark analyzer, scheduler
│   ├── main.py
│   ├── rule_engine.py
│   ├── spark_analyzer.py
│   ├── scheduler.py
│   └── routes/
├── mobile/           # Expo React Native Android app
├── scripts/          # Startup and utility scripts
├── docker-compose.yml
└── PROJECT_REPORT.md
```

---

## ⚙️ Signal Rules

A signal is generated when a coin meets all of the following criteria:

- 5-minute price change ≥ +0.8%
- 15-minute price change ≥ +1.5%
- Volume spike ≥ 1.5× average
- RSI between 50–70
- BTC market is stable

---

## 🔧 Runtime Controls

Switch modes without redeployment via the `/control` endpoint:

- **Data source:** `simulator` | `real` (live Binance scan)
- **Algorithm profile:** `mid` (balanced) | `advanced` (stricter thresholds)

---

## 🚦 Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.10+
- Node.js & npm (for mobile)
- Java 11+ (for Spark)

### Run with Docker

```bash
docker-compose up --build
```

### Run backend locally

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Run mobile app

```bash
cd mobile
npm install
npx expo start
```

---

## 📡 API Endpoints

| Method | Endpoint          | Description                        |
|--------|-------------------|------------------------------------|
| GET    | `/signals`        | Fetch active signals               |
| GET    | `/signals/archive`| Fetch historical signals           |
| GET    | `/health`         | Service health + current mode/profile |
| POST   | `/control`        | Switch data source or algorithm profile |
| GET    | `/export/signals` | Export signals as JSON or CSV      |
| GET    | `/export/trades`  | Export trades as JSON or CSV       |

---

## 🔮 Future Scope

- Persist runtime mode/profile across backend restarts
- Historical benchmarking dashboards
- Macro sentiment integration (Glassnode)
- Cloud deployment for always-on operation
- ML-based signal ranking layer
