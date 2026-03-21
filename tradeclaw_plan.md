# For GitHub
git add .
git commit -m "Your commit message"
git push

# For Expo (from the mobile directory)
eas update --branch main --message "Your update message"

# mobile apk
eas build --profile preview --platform android

===========================================================================================
tradeclaw_beta
---

# 1) Agent Mission 

Build an Android APK (React Native or Flutter) for a crypto momentum alert system.

Constraints:

* No login / no user accounts
* Low latency notifications (Firebase Cloud Messaging)
* App acts as a thin client (all scanning happens on backend)
* User manually executes trades on Binance

Core goal:

* Display high-quality trade alerts (short-term momentum)
* Each alert includes entry, target (+5%), stop-loss (−1%), and expiry (30 min)
* Allow user to set a manual reminder to exit trade
* Provide quick action to open Binance app

Do NOT include:

* Portfolio tracking
* Charts inside app
* Complex UI
* Authentication

Focus:

* Speed
* Reliability
* Minimal UI

---

# 2) System Architecture (strict)

```text
Backend (FastAPI)
    ↓
Rule Engine (Binance API scan)
    ↓
Signal JSON
    ↓
Firebase Push
    ↓
APK receives + displays tiles
```

---

# 3) Data contract (VERY IMPORTANT)

Every signal sent to app:

```json
{
  "id": "BTC_17001",
  "coin": "BTC/USDT",
  "entry_range": "64200-64400",
  "target_pct": 5,
  "stop_loss_pct": 1,
  "created_at": 1700000000,
  "expiry_at": 1700001800,
  "timeframe": "5m-15m",
  "confidence": "HIGH",
  "reason": "Momentum + volume spike"
}
```

---

# 4) Mobile App UI (your dashboard)

## 🔲 Dashboard Layout

Simple vertical list of **tiles**

---

## 🔳 Each Tile (exact spec)

```
[ COIN NAME ]         [ ⏱ Expiry Countdown ]

Entry: 64200–64400
Target: +5%
Stop Loss: −1%
Timeframe: 5m–15m

[ Set Exit Alert ]   [ Open Binance ]
```

---

## 🔥 Required behaviors

### 1. Expiry countdown

* Real-time countdown (30 min)
* When expired → auto remove tile

---

### 2. Set Exit Alert button

When clicked:

* Ask: “Set reminder in how many minutes?”
* Options: 5 / 10 / 15 / custom

Then:

* Schedule local notification:

  ```
  "Check BTC trade exit now"
  ```

---

### 3. Binance button

Deep link:

```text
binance://trade/BTC_USDT
```

Fallback:

* Open Binance website

---

# 5) Notification system

## 🔔 Incoming signal

Push notification:

```
🚀 BTC/USDT Momentum
Target: +5% | SL: −1%
Valid: 30 min
```

---

## Behavior:

* Tap → opens app → scroll to tile

---

# 6) Backend (minimal spec for agent)

## Endpoints

```text
GET /signals
POST /signals (internal use)
```

---

## Scheduler

* Runs every 1–2 minutes
* Calls Binance API
* Applies rule engine
* Emits top signals

---

## Rule Engine (must implement)

```text
- 5m change ≥ +0.8%
- 15m change ≥ +1.5%
- Volume spike ≥ 1.5x
- RSI 50–70
- BTC stable
```

---

# 7) Storage (simple)

Use:

* Local device storage (SQLite or AsyncStorage)

Store:

* Active signals
* Expiry timestamps

---

# 8) Performance constraints

Agent must ensure:

* App launch < 1 second
* Notification delivery < 2 sec (FCM)
* No background heavy processing

---

Build a DATA LAYER module for a crypto momentum trading system.

Purpose:

* Collect, store, and structure trading data
* Enable future model training and performance analysis
* NOT used for real-time decision making (separate from signal engine)

Constraints:

* Must be lightweight, fast, and append-only
* Must not block signal generation or notifications
* Must support export for ML training

---

## 1. DATA SOURCES

Integrate:

1. Binance API

   * Price (OHLCV)
   * Volume
   * Trade data (optional)

2. Internal Signal Engine

   * Generated signals
   * Rule scores
   * Rejection reasons

3. Trade Lifecycle (manual user input)

   * Entry time
   * Exit time
   * Outcome (profit/loss)

---

## 2. DATA SCHEMA

Create structured records:

### Market Snapshot

{
"timestamp": int,
"symbol": "BTCUSDT",
"price": float,
"volume": float,
"price_change_5m": float,
"price_change_15m": float,
"rsi": float,
"btc_trend": "UP | DOWN | NEUTRAL"
}

---

### Signal Record

{
"signal_id": string,
"symbol": "BTCUSDT",
"generated_at": int,
"score": int,
"entry_range": [low, high],
"target_pct": 5,
"stop_loss_pct": 1,
"expiry_at": int,
"reason": string,
"status": "TRIGGERED | EXPIRED | SKIPPED"
}

---

### Trade Record (user-driven)

{
"trade_id": string,
"signal_id": string,
"symbol": "BTCUSDT",
"entry_price": float,
"exit_price": float,
"entry_time": int,
"exit_time": int,
"profit_pct": float,
"hit_target": bool,
"hit_stop_loss": bool,
"manual_exit": bool
}

---

## 3. STORAGE DESIGN

Use:

* Local DB: SQLite (mobile) OR
* Backend DB: PostgreSQL (preferred)

Rules:

* Append-only writes
* No overwriting historical data
* Indexed by timestamp and symbol

---

## 4. DATA PIPELINE

Flow:

[Binance API] → [Market Snapshot Logger]
[Rule Engine] → [Signal Logger]
[User Action] → [Trade Logger]

All logs must be:

* Asynchronous
* Non-blocking

---

## 5. PERFORMANCE REQUIREMENTS

* Logging latency < 50ms
* No impact on signal generation speed
* Batch writes if needed

---

## 6. EXPORT SYSTEM

Provide export endpoints:

* /export/signals
* /export/trades
* /export/market

Formats:

* JSON
* CSV

---

## 7. FUTURE MODEL TRAINING SUPPORT

Ensure dataset supports:

* Feature extraction (momentum, volume, RSI)
* Label generation (profit vs loss)
* Sequence modeling (time-series)

---

## 8. OPTIONAL (ADVANCED)

Add:

* Glassnode macro data (daily level only)
  Example:
  {
  "btc_exchange_flow": float,
  "long_term_holder_supply": float,
  "market_sentiment": "BULLISH | BEARISH"
  }

Store separately and join by timestamp.

---

## 9. DO NOT IMPLEMENT

* No AI inference inside data layer
* No decision logic here
* No UI coupling

---

Goal:
Build a clean, scalable data foundation for future quant trading and model training.



-----------------------------------------------------------------------------------------




###future upgrade wait for my command to implement

# 9) Optional (Phase 2 – advanced)

## Glassnode integration

Backend only:

* Add macro flag:

  * BULLISH / NEUTRAL / BEARISH

Send with signal:

```json
"macro": "BULLISH"
```

---

## Local AI (your RTX 3070 Ti)

Use only for:

* Ranking signals (backend)
* Not mobile

---

# 10) Build priority (tell Claude)

1. Backend signal generator
2. FCM integration
3. Basic APK (tiles + notifications)
4. Exit alert feature
5. Binance deep link

---

# 11) What NOT to build

* Login/auth
* Charts
* Wallet integration
* Over-engineered UI
* AI inside app

---

# Final principle

> This is not a trading app
> This is a **decision delivery system**

---
