# Windows Teammate Setup

## Master Laptop (You)

1. Open `team/windows`.
2. Run `master_planA.bat`.
3. Enter your LAN IP when prompted (example `192.168.1.10`).

## Quick Steps

1. Clone this repository.
2. Open `team/windows`.
3. Double-click `teamsetup.bat` (run once).
4. Double-click `run_slave.bat` and enter:
   - Master IP: example `192.168.1.10`
   - Worker ID: `1` or `2`

## Expected Result

- Container starts as `tradeclaw-remote-worker-1` or `tradeclaw-remote-worker-2`.
- Worker appears in Spark UI on master laptop: `http://<MASTER_IP>:8080`

## Stop Worker

- Run `stop_slave.bat` and enter worker ID.

## Notes

- Keep Docker Desktop running.
- All laptops must be on same lab Wi-Fi.
- If worker does not appear in Spark UI, check firewall/network first.
