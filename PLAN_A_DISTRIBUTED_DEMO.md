# TradeClaw Plan A Distributed Demo Runbook

This runbook is for the professor demo where one laptop is Spark master and two teammate laptops are Spark workers.

## 1. Roles

- Master laptop (you): Kafka, Postgres, Spark Master, backend API, simulator, Spark analyzer submit.
- Teammate 1 laptop: Spark worker 1.
- Teammate 2 laptop: Spark worker 2.
- Mobile phone: app demo UI and live signals.

## 2. Network Rules

- All three laptops must be on the same lab Wi-Fi.
- Confirm teammates can ping the master laptop IP.
- Use the master LAN IP throughout this runbook.

## 3. One-Time Prep (Before Demo Day)

1. On each teammate laptop, clone repository.
2. On each teammate laptop, run:
   - Windows: `team\\windows\\teamsetup.bat`
   - macOS: `./team/mac/teamsetup.sh`
3. On master laptop, ensure Docker Desktop is running and venv exists.

### Clickable scripts by OS

- Windows (double-click friendly): use `.bat` files in `team/windows`.
- macOS (Terminal): run `.sh` scripts in `team/mac` after `chmod +x team/mac/*.sh`.

## 4. Demo Day Start Sequence

### Step A: Master starts core stack

On master laptop:

team\\windows\\master_planA.bat <MASTER_LAN_IP>

macOS alternative:

./team/mac/master_planA.sh <MASTER_LAN_IP>

What this script does:
- Starts postgres, zookeeper, kafka, spark-master.
- Waits for Kafka and Postgres readiness.
- Rebuilds DB schema.
- Starts simulator and backend API in separate windows.
- Waits for remote workers to join Spark UI.
- Submits Spark analyzer with fixed driver ports for remote executors.

### Step B: Teammate 1 starts worker

On teammate 1 laptop:

team\\windows\\run_slave.bat <MASTER_LAN_IP> 1

macOS alternative:

./team/mac/run_slave.sh <MASTER_LAN_IP> 1

### Step C: Teammate 2 starts worker

On teammate 2 laptop:

team\\windows\\run_slave.bat <MASTER_LAN_IP> 2

macOS alternative:

./team/mac/run_slave.sh <MASTER_LAN_IP> 2

### Step D: Validate cluster

On master Spark UI:

http://localhost:8080

Expected:
- Spark master up.
- Worker entries for remote-worker-1 and remote-worker-2.

## 5. Mobile Demo Sequence

1. Open app on phone.
2. In settings, set backend URL to:
   http://<MASTER_LAN_IP>:8001
3. Set Data Source mode:
   simulator (guaranteed live movement)
4. Set Algorithm Profile:
   mid
5. Open dashboard and verify incoming active signals.

## 6. Professor Talking Points

- Distributed processing: Spark master-worker architecture across three laptops.
- Event ingestion: Kafka tick stream.
- Real-time analytics: Spark Structured Streaming.
- Decision delivery: FastAPI + mobile signal tiles + alerts.
- Runtime controls: simulator/real switch and mid/advanced algorithm profile.

## 7. Fallback (If Lab Wi-Fi blocks worker connectivity)

On master laptop only:

run_tradeclaw_distributed.bat

This keeps demo alive with local workers.

## 8. Teardown

Master laptop:

docker-compose down

Teammates:

team\\windows\\stop_slave.bat 1
team\\windows\\stop_slave.bat 2

macOS alternative:

./team/mac/stop_slave.sh 1
./team/mac/stop_slave.sh 2
