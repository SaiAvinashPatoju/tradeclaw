# Tradeclaw Distributed Streaming Setup

This adds a mini-project implementation for:

- PostgreSQL persistence service
- 1 Spark master
- 3 Spark worker (slave) nodes
- Real-time tick ingestion via Kafka
- Spark Structured Streaming analysis
- Signal writes into existing `signals` table

## Added Files
- `docker-compose.yml`
- `backend/data_simulator.py`
- `backend/spark_analyzer.py`
- `scripts/run_spark_pipeline.ps1`
- `scripts/planA_master_start.ps1`
- `scripts/worker_install_and_prepare.ps1`
- `scripts/start_slave_teammate1.ps1`
- `scripts/start_slave_teammate2.ps1`
- `PLAN_A_DISTRIBUTED_DEMO.md`
- `PROJECT_REPORT.md`

## Plan A (Cross-Laptop Distributed Demo)

Use the dedicated runbook:

- `PLAN_A_DISTRIBUTED_DEMO.md`

Quick start:

1. Master laptop:
   - `powershell -ExecutionPolicy Bypass -File scripts/planA_master_start.ps1 -MasterIp <MASTER_LAN_IP>`
2. Teammate 1:
   - `powershell -ExecutionPolicy Bypass -File scripts/start_slave_teammate1.ps1 -MasterIp <MASTER_LAN_IP>`
3. Teammate 2:
   - `powershell -ExecutionPolicy Bypass -File scripts/start_slave_teammate2.ps1 -MasterIp <MASTER_LAN_IP>`

Windows clickable launchers are also available:

- `scripts\\planA_master_start.bat`
- `scripts\\worker_install_and_prepare.bat`
- `scripts\\start_slave_teammate1.bat`
- `scripts\\start_slave_teammate2.bat`
- `scripts\\stop_remote_slaves.bat`

macOS shell equivalents are also available:

- `scripts/worker_install_and_prepare.sh`
- `scripts/start_slave_teammate1.sh`
- `scripts/start_slave_teammate2.sh`
- `scripts/stop_remote_slaves.sh`

If Wi-Fi blocks remote workers, use fallback:

- `powershell -ExecutionPolicy Bypass -File scripts/planA_master_start.ps1 -MasterIp <MASTER_LAN_IP> -UseLocalWorkersFallback`

## Prerequisites
1. Docker Desktop running.
2. PostgreSQL database reachable from Docker network.
3. Root `.env` should contain:
   - `DATABASE_URL=postgresql://user:pass@host:5432/dbname`

## 1) Start Cluster
```powershell
docker-compose up -d
```

Open Spark Master UI:
- http://localhost:8080

Expected:
- Master online
- 3 workers registered (`spark-worker-1`, `spark-worker-2`, `spark-worker-3`)

## 2) Start Tick Simulator (Host Shell)
```powershell
python -m backend.data_simulator
```

Optional envs:
- `KAFKA_BOOTSTRAP_SERVERS` (default `localhost:9092`)
- `KAFKA_TOPIC` (default `tradeclaw_ticks`)
- `TICKS_PER_SYMBOL_PER_SEC` (default `20`)

## 2.5) Initialize Database Schema

Run once after stack startup:

```powershell
$env:PYTHONPATH='.'; c:/Users/Avinash/Desktop/projects/personal/tradeclaw/venv/Scripts/python.exe rebuild_db.py
```

## 3) Submit Spark Analyzer

Use another shell:

```powershell
docker exec -it tradeclaw-spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --conf spark.jars.ivy=/tmp/.ivy --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.7.3 /opt/tradeclaw/backend/spark_analyzer.py
```

Optional envs for analyzer:
- `KAFKA_BOOTSTRAP_SERVERS` (default `kafka:29092` inside containers)
- `KAFKA_TOPIC` (default `tradeclaw_ticks`)
- `SPARK_CHECKPOINT_DIR` (default `/tmp/tradeclaw_checkpoints/spark_analyzer`)

## 4) Validate “Data Blocks on Individual Slaves”
The analyzer prints partition-to-host execution stats per micro-batch:

Example:
```text
[spark] batch=9 partition/host stats: [(0, 'tradeclaw-spark-worker-1', 18), (1, 'tradeclaw-spark-worker-2', 22), (2, 'tradeclaw-spark-worker-3', 17)]
```

This proves data partitions (blocks) are processed across separate worker nodes.

## 5) Real-Time Signal Output
Analyzer writes generated signals to the existing `signals` table using `ON CONFLICT DO NOTHING`.

Verify quickly:
```sql
SELECT id, symbol, score, status, generated_at
FROM signals
ORDER BY created_at DESC
LIMIT 20;
```

## Stop Cluster
```powershell
docker-compose down
```
