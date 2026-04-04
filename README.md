# TradeClaw 🦀

> Real-time crypto momentum signal engine with distributed stream processing and mobile push delivery.

TradeClaw continuously scans Binance spot markets, applies a multi-factor momentum scoring algorithm, and delivers actionable trade signals — including entry range, target, stop-loss, and a live countdown — to a React Native mobile app via Firebase Cloud Messaging.

---

## Overview

Retail traders consistently miss short-lived momentum windows due to market noise and signal latency. TradeClaw addresses this by:

- Scanning the **top 80 liquid USDT spot pairs** on Binance every 60 seconds
- Computing **9-factor composite scores** (momentum, volume, RSI, relative strength, trend persistence, body/wick ratio, spread)
- Emitting at most **3 signals per scan cycle** with full lifecycle tracking: `ACTIVE → EXPIRED → WIN / LOSS / INCOMPLETE`
- Delivering push notifications via **Firebase Cloud Messaging** within seconds of signal generation
- Providing a **Spark Structured Streaming** pipeline for high-frequency tick-level analysis over Kafka

---

## Architecture

```mermaid
graph TD
    A[Binance REST API] -->|klines + 24h tickers| B[Scanner]
    K[Kafka Topic: tradeclaw_ticks] -->|high-freq ticks| S[Spark Streaming Analyzer]
    DS[Data Simulator] -->|synthetic ticks| K

    B --> F[Feature Engineering]
    F --> R[Rule Engine + Scoring]
    R --> SE[Signal Engine]
    SE -->|signals + rejections| DB[(PostgreSQL)]
    SE --> FCM[Firebase Cloud Messaging]
    S -->|JDBC APPEND| DB

    DB --> API[FastAPI Backend]
    API --> MOB[React Native Mobile App]
    FCM --> MOB

    SCHED[APScheduler] -->|every 60s| B
    SCHED -->|every 5min| EVAL[Signal Evaluator]
    EVAL -->|Binance historical klines| DB
```

### Component Summary

| Component | Role |
|---|---|
| **Scanner** | Fetches 5m / 15m / 1h klines for top-80 USDT pairs from Binance REST API |
| **Feature Engineering** | Computes momentum, RSI, relative volume, body/wick ratio, trend persistence, spread, and cross-sectional relative strength |
| **Rule Engine** | Two-stage filter (pre-filter → core rules) with configurable `mid` and `advanced` algorithm profiles |
| **Signal Engine** | Per-symbol cooldown (15 min), dedup, top-K cut (max 3/cycle), lifecycle field computation |
| **Evaluator** | Runs every 5 min; fetches historical klines to determine WIN / LOSS / INCOMPLETE for expired signals |
| **Spark Analyzer** | PySpark Structured Streaming job reads ticks from Kafka, applies 5-second windows, writes signals via JDBC |
| **Data Simulator** | Publishes synthetic high-frequency ticks to Kafka for local development without Binance credentials |
| **FastAPI Backend** | REST API for signals, archive, export, health, and runtime engine control |
| **FCM Module** | Firebase Admin SDK push notifications delivered per signal to `signals` topic or individual device token |
| **Mobile App** | React Native (Expo) — Dashboard, Archive, Stats, Settings screens with glassmorphism UI |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend language** | Python 3.11+ |
| **API framework** | FastAPI 0.115 + Uvicorn |
| **ORM / DB driver** | SQLAlchemy 2.0 (async) + asyncpg |
| **Database** | PostgreSQL 15 |
| **Task scheduling** | APScheduler 3.10 (AsyncIOScheduler) |
| **Stream processing** | Apache Spark 3.5.1 (PySpark Structured Streaming) |
| **Message broker** | Apache Kafka 7.6 (Confluent) + Zookeeper |
| **Market data** | python-binance 1.0.19 (Binance REST API) |
| **Push notifications** | Firebase Admin SDK 6.5 (FCM) |
| **Data / ML libs** | NumPy, Pandas, pandas-ta |
| **Mobile framework** | React Native 0.81.5, Expo SDK 54 |
| **Navigation** | React Navigation 7 (bottom tabs) |
| **Mobile notifications** | expo-notifications |
| **Containerisation** | Docker Compose |
| **Testing** | pytest 8.3 + pytest-asyncio 0.24 |

---

## Features

- **Live signal dashboard** — scrollable list of ACTIVE signals with 20-minute entry countdown, confidence tier badge, entry range, TP/SL levels, and one-tap deep-link to Binance
- **Multi-factor composite scoring** — 9-dimensional normalized score (0–100) across momentum, volume, RSI, relative strength, trend persistence, body/wick ratio, spread, and breakout rank
- **Dual algorithm profiles** — `mid` (default, broader filter) and `advanced` (stricter thresholds, higher TP/SL targets); switchable at runtime via API
- **Signal lifecycle management** — automatic ACTIVE → EXPIRED → WIN / LOSS / INCOMPLETE transitions with P&L recording
- **Signal archive** — paginated history of evaluated signals with actual max/min price and evaluated profit %
- **Push notifications** — FCM alerts within seconds of signal generation, confidence-tiered emoji headers
- **Data export** — signals, market snapshots, and trade outcomes as JSON or CSV with timestamp range filtering
- **Runtime engine control** — switch `data_source_mode` (`simulator` / `real`) and `algorithm_profile` live without restart
- **Spark streaming pipeline** — high-frequency 5-second window aggregation over Kafka for tick-level signal generation
- **Health endpoint** — backend status, last scan timestamp, signals-today count, active data mode and algorithm profile
- **Simulator mode** — Kafka-backed synthetic tick generator for full local development without Binance API keys
- **Signal rejection logging** — every rejected candidate is persisted with reason code and feature vector for analysis

---

## Project Structure

```
tradeclaw/
├── backend/                    # FastAPI Python backend
│   ├── main.py                 # App factory, lifespan, CORS, router registration
│   ├── config.py               # Environment variable loading and validation
│   ├── database.py             # Async SQLAlchemy engine, session factory, Base
│   ├── models.py               # ORM models: Signal, MarketSnapshot, SignalRejection, TradeOutcome
│   ├── schemas.py              # Pydantic response schemas (HealthResponse)
│   ├── scanner.py              # Binance kline fetcher, universe selection (top-80 USDT pairs)
│   ├── features.py             # Feature engineering: momentum, RSI, volume, spread, rel. strength
│   ├── indicators.py           # Pure-function technical indicators (RSI, VWAP, BTC regime)
│   ├── rule_engine.py          # Pre-filters, core rules, composite scoring, algorithm profiles
│   ├── signal_engine.py        # Cooldown/dedup logic, signal construction, lifecycle fields
│   ├── evaluator.py            # Historical kline-based WIN/LOSS/INCOMPLETE evaluator
│   ├── scheduler.py            # APScheduler: scan_job (60s), evaluate_job (5min)
│   ├── runtime_config.py       # In-memory runtime config (data mode, algorithm profile)
│   ├── fcm.py                  # Firebase Admin SDK push notification module
│   ├── scoring.py              # Standalone composite scoring engine (used in tests)
│   ├── spark_analyzer.py       # PySpark Structured Streaming job (Kafka → PostgreSQL)
│   ├── data_simulator.py       # Synthetic tick generator publishing to Kafka
│   ├── routes/
│   │   ├── signals.py          # GET /signals, GET /signals/archive, GET /signals/by-status/{s}, POST /signals
│   │   ├── health.py           # GET /health
│   │   ├── export.py           # GET /export/signals|market|trades (JSON + CSV)
│   │   └── control.py          # GET|PUT /control/engine
│   ├── tests/
│   │   ├── test_signal_engine.py
│   │   ├── test_scoring.py
│   │   └── test_indicators.py
│   └── requirements.txt
│
├── mobile/                     # React Native (Expo) mobile app
│   ├── App.js                  # Root component, navigation stack, notification registration
│   ├── index.js                # Expo entry point
│   ├── src/
│   │   ├── screens/
│   │   │   ├── DashboardScreen.js   # Live signal list, 15s polling, haptic feedback
│   │   │   ├── ArchiveScreen.js     # Evaluated signals with modal trade detail view
│   │   │   ├── StatsScreen.js       # Health metrics, signal counts, scan status
│   │   │   └── SettingsScreen.js    # Backend URL, engine config, confidence filter
│   │   ├── components/
│   │   │   ├── SignalTile.js        # Glassmorphism card with animated entry and countdown
│   │   │   ├── CountdownTimer.js    # Live expiry countdown ticker
│   │   │   ├── StatusBar.js         # Backend connection status indicator
│   │   │   └── EmptyState.js        # Empty list placeholder
│   │   ├── services/
│   │   │   ├── api.js              # REST client with URL fallback and self-healing
│   │   │   ├── notifications.js     # FCM token registration, exit-reminder scheduling
│   │   │   └── storage.js          # AsyncStorage wrappers (backend URL, user settings)
│   │   ├── theme.js                # Design system: colors, fonts, spacing, shadows
│   │   └── utils/                  # formatting.js, deeplink.js
│   ├── app.json                # Expo project config (bundle IDs, permissions)
│   ├── eas.json                # EAS Build profile config
│   └── package.json
│
├── scripts/
│   ├── init_db.sql             # Manual DDL for initial schema setup
│   ├── migrate_fix_numeric.sql # Numeric column migration patch
│   ├── seed_test_signal.py     # Utility to seed a test signal
│   └── run_spark_pipeline.ps1  # PowerShell launcher for Spark submit
│
├── docker-compose.yml          # PostgreSQL 15, Kafka, Zookeeper, Spark (1 master + 3 workers)
├── rebuild_db.py               # Drop-and-recreate all tables utility
├── analyze.py                  # Standalone analysis script
├── .env                        # ⚠️ Environment variables — see Security section
└── firebase-service-account.json  # ⚠️ Firebase credentials — must not be committed
```

---

## Getting Started

### Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| Docker + Docker Compose | v2+ |
| Expo CLI | Latest (`npm install -g expo-cli`) |
| EAS CLI (for device builds) | Latest (`npm install -g eas-cli`) |

### Installation

#### 1. Clone and configure environment

```bash
git clone https://github.com/SaiAvinashPatoju/tradeclaw.git
cd tradeclaw
```

Create a `.env` file in the project root with the variables listed in the [Environment Variables](#environment-variables) table below. **Never commit real secrets to version control.**

#### 2. Start infrastructure

```bash
docker compose up -d postgres kafka zookeeper
```

#### 3. Backend setup

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 4. Mobile setup

```bash
cd mobile
npm install
```

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `BINANCE_API_KEY` | ✅ (real mode) | — | Binance API key (read-only permissions sufficient) |
| `BINANCE_API_SECRET` | ✅ (real mode) | — | Binance API secret |
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string (`postgresql://user:pass@host:5432/db`) |
| `FCM_PROJECT_ID` | ✅ | — | Firebase project ID for push notifications |
| `TRADECLAW_DATA_SOURCE_MODE` | ❌ | `simulator` | `simulator` or `real` — controls whether Binance API is called |
| `TRADECLAW_ALGORITHM_PROFILE` | ❌ | `mid` | `mid` or `advanced` — sets scoring thresholds at startup |
| `KAFKA_BOOTSTRAP_SERVERS` | ❌ | `localhost:9092` | Kafka broker address (used by simulator and Spark) |
| `KAFKA_TOPIC` | ❌ | `tradeclaw_ticks` | Kafka topic name for tick stream |
| `SPARK_CHECKPOINT_DIR` | ❌ | `/tmp/tradeclaw_checkpoints_v2` | Spark streaming checkpoint path |

### Running the Project

#### Backend (development)

```bash
# From project root, with virtual environment active:
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

API docs available at: `http://localhost:8001/docs`

#### Backend (production)

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --workers 1
```

> ⚠️ Use `--workers 1` — the in-memory cooldown tracker and APScheduler are not process-safe across multiple workers.

#### Mobile app (Expo Go)

```bash
cd mobile
npx expo start
```

Scan the QR code with Expo Go (Android/iOS). Configure the backend URL in the Settings screen.

#### Simulator mode (no Binance API required)

```bash
# Terminal 1 — Start infrastructure
docker compose up -d postgres kafka zookeeper

# Terminal 2 — Run data simulator (publishes synthetic ticks to Kafka)
python -m backend.data_simulator

# Terminal 3 — Start backend in simulator mode
TRADECLAW_DATA_SOURCE_MODE=simulator uvicorn backend.main:app --port 8001 --reload
```

#### Full distributed stack (Spark pipeline)

```bash
docker compose up -d
# Run Spark job inside spark-master container:
docker exec tradeclaw-spark-master spark-submit \
  --master spark://spark-master:7077 \
  /opt/tradeclaw/backend/spark_analyzer.py
```

---

## API Documentation

All endpoints return JSON. Interactive docs at `/docs` (Swagger UI) and `/redoc`.

### Signals

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/signals` | Active, non-expired signals ordered by score descending |
| `GET` | `/signals/archive` | Evaluated signals (WIN / LOSS / INCOMPLETE) with pagination |
| `GET` | `/signals/by-status/{status}` | Filter signals by any lifecycle status |
| `POST` | `/signals` | Manually insert a signal (development only) |

**Signal object fields:**

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `{SYMBOL}_{YYYYMMDD}_{HHMMSS}` or `SPARK_{SYMBOL}_{hex}` |
| `symbol` | `string` | e.g. `ETHUSDT` |
| `score` | `float` | Composite score 0–100 |
| `confidence` | `string` | `LOW` / `MEDIUM` / `HIGH` / `SNIPER` |
| `reason` | `string` | Human-readable signal summary |
| `generated_at` | `int` | Unix epoch (seconds) |
| `expiry_at` | `int` | Entry window close (generated_at + 20 min) |
| `evaluation_at` | `int` | Outcome check time (expiry_at + 4h hold) |
| `entry_low` | `float` | Lower bound of entry range (price × 0.999) |
| `entry_high` | `float` | Upper bound of entry range (price × 1.001) |
| `target_price` | `float` | Absolute take-profit price |
| `stop_price` | `float` | Absolute stop-loss price |
| `target_pct` | `float` | TP % (1.2% mid / 1.5% advanced) |
| `stop_loss_pct` | `float` | SL % (0.6% mid / 0.7% advanced) |
| `status` | `string` | `ACTIVE` / `EXPIRED` / `WIN` / `LOSS` / `INCOMPLETE` |
| `evaluated_profit_pct` | `float?` | Actual outcome P&L % (post-evaluation) |
| `max_price_reached` | `float?` | Highest price during hold window |
| `min_price_reached` | `float?` | Lowest price during hold window |

### Health

```
GET /health
```

```json
{
  "status": "ok",
  "last_scan": 1712180400,
  "signals_today": 7,
  "data_source_mode": "real",
  "algorithm_profile": "mid"
}
```

### Export

| Method | Endpoint | Query Params | Description |
|---|---|---|---|
| `GET` | `/export/signals` | `from`, `to` (epoch), `format` (json/csv) | Signal history export |
| `GET` | `/export/market` | `symbol`, `from`, `to`, `format` | Market snapshot export |
| `GET` | `/export/trades` | `from`, `to`, `format` | Trade outcome export |

### Runtime Engine Control

```
GET  /control/engine          # Returns current config + available options
PUT  /control/engine          # Update data_source_mode and/or algorithm_profile
```

**PUT request body:**

```json
{
  "data_source_mode": "real",
  "algorithm_profile": "advanced"
}
```

---

## Signal Lifecycle

```
ACTIVE      → Entry window is open (20 minutes). Signal visible on dashboard.
EXPIRED     → Entry window closed; hold period is running (4 hours).
WIN         → Target price hit during hold period before stop-loss.
LOSS        → Stop-loss hit during hold period before target.
INCOMPLETE  → Neither TP nor SL reached during hold period.
```

Evaluation fetches 5-minute Binance historical klines over the hold window and walks candles chronologically. If both TP and SL are hit in the same candle, the outcome is conservatively recorded as **LOSS**.

---

## Algorithm Profiles

| Parameter | `mid` (default) | `advanced` |
|---|---|---|
| 5m momentum min | 0.1% | 0.2% |
| 15m momentum min | 0.2% | 0.4% |
| Relative volume min | 1.1× | 1.35× |
| RSI range | 40–80 | 45–74 |
| Body/wick ratio min | 0.20 | 0.30 |
| Trend persistence min | 0.33 (1/3 candles) | 0.66 (2/3 candles) |
| Target % | 1.2% | 1.5% |
| Stop-loss % | 0.6% | 0.7% |

Switch profiles at runtime without restart:

```bash
curl -X PUT http://localhost:8001/control/engine \
  -H "Content-Type: application/json" \
  -d '{"algorithm_profile": "advanced"}'
```

---

## Deployment

### Docker Compose (local / single-host)

```bash
docker compose up -d
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --workers 1
```

The `docker-compose.yml` provisions:

| Service | Image | Port |
|---|---|---|
| `postgres` | postgres:15 | 5432 |
| `zookeeper` | confluentinc/cp-zookeeper:7.6.1 | 2181 |
| `kafka` | confluentinc/cp-kafka:7.6.1 | 9092 |
| `spark-master` | apache/spark:3.5.1 | 7077, 8080 |
| `spark-worker-1/2/3` | apache/spark:3.5.1 | 8081–8083 |

### Mobile (EAS Build)

```bash
cd mobile
eas build --platform android --profile preview   # APK for direct install
eas build --platform android --profile production # AAB for Play Store
eas build --platform ios --profile production     # IPA for App Store
```

### ⚠️ Production Checklist

- [ ] Rotate Binance API keys — do not use keys committed to the repository
- [ ] Remove or gitignore `firebase-service-account.json` — it contains private credentials
- [ ] Replace CORS `allow_origins=["*"]` with an explicit allowlist
- [ ] Set `TRADECLAW_DATA_SOURCE_MODE=real` in the production environment
- [ ] Use Alembic for schema migrations (currently `create_all` is used at startup)
- [ ] Add a reverse proxy (nginx / Caddy) with TLS in front of Uvicorn
- [ ] Run behind a process supervisor (systemd, supervisord, or container orchestrator)
- [ ] Configure APScheduler persistence or use Celery Beat for crash-safe scheduling

---

## Testing

```bash
# From project root, with virtual environment active:
pytest backend/tests/ -v
```

| Test file | Coverage area |
|---|---|
| `test_signal_engine.py` | BTC crash guard, per-symbol cooldown, dedup, max-3 limit, entry range formatting, reason string |
| `test_scoring.py` | Each sub-scorer independently, composite score calculation, confidence tier boundaries |
| `test_indicators.py` | RSI (Wilder's smoothing), VWAP, BTC regime detection |

---

## Observability

| Aspect | Implementation |
|---|---|
| **Logging** | Python `logging` module; structured `%(asctime)s \| %(name)s \| %(levelname)s \| %(message)s` format |
| **Log namespaces** | `tradeclaw`, `tradeclaw.scanner`, `tradeclaw.signal_engine`, `tradeclaw.scheduler`, `tradeclaw.evaluator`, `tradeclaw.fcm` |
| **Health endpoint** | `GET /health` — last scan timestamp, signals today, active mode/profile |
| **Rejection log** | All filtered-out candidates persisted to `signal_rejections` table with reason code and feature vector |
| **Scan cycle summary** | Each 60s cycle logs: symbols scanned, signals emitted, rejections, elapsed time |
| **Spark logs** | Per-batch partition/host distribution stats logged to stdout |

> No external metrics sink (Prometheus, Datadog, etc.) is configured in this codebase. Application-level health data must be scraped from the `/health` endpoint or a log aggregator pointed at the structured log output.

---

## Security

| Area | Current State |
|---|---|
| **API authentication** | ❌ None — all endpoints are unauthenticated. Add API key middleware or JWT for production. |
| **CORS** | ⚠️ `allow_origins=["*"]` — permissive. Restrict to known origins in production. |
| **Binance API keys** | ⚠️ Committed to `.env` in repository. Rotate immediately and use secrets management (AWS Secrets Manager, Vault, etc.). |
| **Firebase credentials** | ⚠️ `firebase-service-account.json` referenced at project root. Must be excluded from version control. |
| **Database credentials** | ⚠️ Hardcoded defaults (`tradeclaw:tradeclaw`) in `docker-compose.yml`. Use strong credentials in production. |
| **Input validation** | ✅ Pydantic models validate all API request bodies. |
| **SQL injection** | ✅ SQLAlchemy ORM with parameterised queries throughout. |
| **TLS / HTTPS** | ❌ Not configured — Uvicorn is exposed directly. Use a TLS-terminating reverse proxy (nginx, Caddy) in production. |
| **Binance API scope** | ✅ Only market data endpoints used — read-only keys are sufficient. |

---

## Contributing

1. Fork the repository and create a feature branch from `main`.
2. Install backend dependencies: `pip install -r backend/requirements.txt`
3. Run existing tests before making changes: `pytest backend/tests/ -v`
4. Keep new backend logic consistent with the async SQLAlchemy pattern in `database.py`.
5. New algorithm profiles must be added to `PROFILE_PRESETS` in `rule_engine.py` and declared in `ALGORITHM_PROFILES`.
6. All signal status transitions must follow the lifecycle defined in `models.py`.
7. Open a pull request with a clear description of the problem solved.

---

## Roadmap

- [ ] Alembic database migrations (replace `create_all`)
- [ ] API authentication (JWT or API key middleware)
- [ ] Multi-worker-safe cooldown tracker (Redis or DB-backed)
- [ ] Prometheus metrics endpoint + Grafana dashboard
- [ ] iOS push notification support (APNs via FCM)
- [ ] Backtesting module against historical Binance klines
- [ ] `SNIPER` confidence tier in rule engine (score ≥ 80 threshold already exists in scoring.py)
- [ ] Per-user device token management (currently broadcasts to `signals` FCM topic)
- [ ] WebSocket endpoint for real-time signal streaming
- [ ] Configurable hold period and TP/SL per signal (currently fixed at runtime profile values)
- [ ] Admin dashboard (web) for signal rejection analysis and algorithm tuning
- [ ] CI/CD pipeline (GitHub Actions) for backend tests and EAS builds

---

## License

❗ No license file is present in this repository. All rights reserved until a license is explicitly added.
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
