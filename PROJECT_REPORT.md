# TradeClaw Project Report

## 1. Project Title

TradeClaw: Distributed Real-Time Crypto Momentum Signal Delivery System

## 2. Team and Objective

This group project builds a low-latency decision delivery system for short-term crypto momentum alerts.
The objective is to detect probable upward momentum opportunities and deliver clean, actionable signals to an Android app.

## 3. Problem Statement

Retail users often miss short-lived momentum opportunities because market data is noisy and decision time is small.
TradeClaw solves this by combining stream processing, scoring, and push-ready signal delivery in a minimal mobile interface.

## 4. Architecture

Pipeline:
- Data source (simulator or real Binance market scan)
- Kafka topic for tick transport
- Spark Structured Streaming analyzer
- PostgreSQL persistence layer
- FastAPI backend service
- Android mobile client (Expo React Native)

Distributed mode for demo:
- Master laptop runs Spark Master + Kafka + Postgres + API + simulator + analyzer submit.
- Two teammate laptops run Spark workers.

## 5. Major Components

### Backend
- FastAPI service for signals, archive, health, export, and control endpoints.
- Scheduler for recurring scan/evaluation loops.
- Runtime control endpoint to switch data source and algorithm profile without redeploy.

### Signal Intelligence
- Rule engine computes candidate quality from momentum, volume, RSI, spread, persistence, and relative strength.
- Profile-based compute modes:
  - mid (balanced)
  - advanced (stricter thresholds)

### Stream Layer
- Kafka ingests tick data.
- Spark analyzer processes streaming batches and writes signal rows to PostgreSQL.

### Mobile App
- Dashboard tile UI for active signals.
- Settings screen with backend endpoint and engine controls.
- Runtime switch for data source mode and algorithm profile through backend API.

## 6. Data Contract

Each signal includes:
- symbol
- score and confidence
- generated and expiry timestamps
- entry range, target percent, stop-loss percent
- reason text for explainability

## 7. Runtime Control Features Implemented

- Data Source Mode switch:
  - simulator
  - real
- Algorithm Profile switch:
  - mid
  - advanced
- Health endpoint now returns current mode/profile for observability.

## 8. Performance and Reliability Measures

- Readiness checks for Kafka and Postgres before pipeline start.
- Automatic port cleanup before backend launch.
- Spark stale analyzer cleanup before new submit.
- Self-healing backend URL fallback on mobile API client.

## 9. Demonstration Plan Summary

1. Connect all laptops to same lab Wi-Fi.
2. Start master script on primary laptop.
3. Start worker scripts on teammate laptops.
4. Validate worker registration in Spark UI.
5. Open mobile app and show live active signals.
6. Explain runtime switch (simulator/real and mid/advanced).

## 10. Learning Outcomes

- Built a practical event-driven analytics stack.
- Implemented distributed compute behavior with Spark worker scaling.
- Connected backend intelligence to a thin mobile decision interface.
- Improved project operability with runtime controls and scripted startup.

## 11. Future Scope

- Persist runtime mode/profile in DB across backend restarts.
- Add historical benchmarking dashboards.
- Integrate advanced macro sentiment features.
- Add cloud deployment profile for always-on demonstration.
