# macOS Teammate Setup

## Master Laptop (macOS)

1. Open terminal in repo root.
2. Make scripts executable:
   - `chmod +x team/mac/*.sh`
3. Run:
   - `./team/mac/master_planA.sh <MASTER_IP>`

## Quick Steps

1. Clone this repository.
2. Open terminal in repo root.
3. Make scripts executable:
   - `chmod +x team/mac/*.sh`
4. Run setup once:
   - `./team/mac/teamsetup.sh`
5. Start slave worker:
   - `./team/mac/run_slave.sh <MASTER_IP> <WORKER_ID>`
   - Example: `./team/mac/run_slave.sh 192.168.1.10 2`

## Expected Result

- Container starts as `tradeclaw-remote-worker-1` or `tradeclaw-remote-worker-2`.
- Worker appears in Spark UI on master laptop: `http://<MASTER_IP>:8080`

## Stop Worker

- `./team/mac/stop_slave.sh <WORKER_ID>`

## Notes

- Keep Docker Desktop running.
- All laptops must be on same lab Wi-Fi.
