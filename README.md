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
- Additional nodes run as Spark workers (3 workers included in `docker-compose.yml`)

---

## 🛠️ Tech Stack

| Layer              | Technology                              |
|--------------------|-----------------------------------------|
| Stream broker      | Apache Kafka (Confluent 7.6.1)          |
| Stream processing  | Apache Spark 3.5.1 Structured Streaming |
| Database           | PostgreSQL 15                           |
| Backend API        | FastAPI (Python)                        |
| Mobile client      | Expo React Native (Android)             |
| Push notifications | Firebase Cloud Messaging (FCM)          |
| Containerization   | Docker / Docker Compose                 |

---

## 📦 Project Structure

```
tradeclaw/
├── backend/               # FastAPI service, signal intelligence, scheduler
│   ├── main.py            # App entry point
│   ├── rule_engine.py     # Rule evaluation and algorithm profiles
│   ├── signal_engine.py   # Signal generation pipeline
│   ├── scoring.py         # Composite score computation
│   ├── indicators.py      # Technical indicators (RSI, momentum, volume)
│   ├── features.py        # Feature extraction helpers
│   ├── scanner.py         # Market scanner
│   ├── evaluator.py       # Signal outcome evaluation
│   ├── scheduler.py       # Recurring scan/evaluation loops
│   ├── spark_analyzer.py  # Spark Structured Streaming analyzer
│   ├── runtime_config.py  # In-memory runtime config (mode, profile)
│   ├── models.py          # SQLAlchemy ORM models
│   ├── schemas.py         # Pydantic response schemas
│   ├── database.py        # Async DB session setup
│   ├── fcm.py             # Firebase push notification client
│   ├── data_simulator.py  # Tick data simulator
│   ├── routes/            # FastAPI route modules
│   │   ├── signals.py
│   │   ├── health.py
│   │   ├── export.py
│   │   └── control.py
│   └── tests/             # Unit tests (indicators, scoring, signal engine)
├── mobile/                # Expo React Native Android app
│   └── src/
│       ├── screens/       # Dashboard, Archive, Settings, Stats screens
│       ├── components/
│       └── services/
├── scripts/               # DB init SQL, Spark pipeline scripts, seed helpers
├── docker-compose.yml
└── PROJECT_REPORT.md
```

---

## ⚙️ Signal Rules

A signal is generated when a coin meets all filter criteria. Two algorithm profiles are available:

### `mid` profile (balanced)
- 5-minute momentum ≥ +0.1%
- 15-minute momentum ≥ +0.2%
- Relative volume ≥ 1.1×
- RSI between 40–80
- Target: +1.2% | Stop-loss: −0.6%

### `advanced` profile (stricter)
- 5-minute momentum ≥ +0.2%
- 15-minute momentum ≥ +0.4%
- Relative volume ≥ 1.35×
- RSI between 45–74
- Target: +1.5% | Stop-loss: −0.7%

Both profiles also evaluate body/wick ratio, trend persistence, and relative strength against BTC.

---

## 🔧 Runtime Controls

Switch modes without redeployment via the `/control/engine` endpoint:

- **Data source:** `simulator` | `real` (live Binance scan)
- **Algorithm profile:** `mid` (balanced) | `advanced` (stricter thresholds)

```bash
# Read current config
GET /control/engine

# Update config
PUT /control/engine
{"data_source_mode": "real", "algorithm_profile": "advanced"}
```

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

This starts PostgreSQL, Zookeeper, Kafka, Spark Master, and three Spark workers.

### Run backend locally

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Run tests

```bash
cd backend
pytest tests/
```

### Run mobile app

```bash
cd mobile
npm install
npx expo start
```

---

## 📡 API Endpoints

| Method | Endpoint                      | Description                             |
|--------|-------------------------------|-----------------------------------------|
| GET    | `/signals`                    | Fetch active (non-expired) signals      |
| GET    | `/signals/archive`            | Fetch evaluated signals with outcomes   |
| GET    | `/signals/by-status/{status}` | Filter signals by lifecycle status      |
| GET    | `/health`                     | Service health, mode, and profile       |
| GET    | `/control/engine`             | Get current runtime config              |
| PUT    | `/control/engine`             | Update data source mode or algorithm profile |
| GET    | `/export/signals`             | Export signal history as JSON or CSV    |
| GET    | `/export/market`              | Export market snapshot data as JSON or CSV |
| GET    | `/export/trades`              | Export trade records as JSON or CSV     |

Signal lifecycle statuses: `ACTIVE` → `WIN` | `LOSS` | `INCOMPLETE` | `EXPIRED`

---

## 🔮 Future Scope

- Persist runtime mode/profile across backend restarts
- Historical benchmarking dashboards
- Macro sentiment integration (Glassnode)
- Cloud deployment for always-on operation
- ML-based signal ranking layer
