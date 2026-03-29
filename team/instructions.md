# Team Setup Entry Point

Use these folders for teammate onboarding:

- Windows: `team/windows`
- macOS: `team/mac`

## Minimum teammate flow

1. Clone repo.
2. Run team setup script once.
3. Run slave script and provide:
   - master laptop IP
   - worker id (1 or 2)

## Windows

- Setup: `team/windows/teamsetup.bat`
- Start worker: `team/windows/run_slave.bat`
- Stop worker: `team/windows/stop_slave.bat`

## macOS

- Setup: `./team/mac/teamsetup.sh`
- Start worker: `./team/mac/run_slave.sh`
- Stop worker: `./team/mac/stop_slave.sh`

Detailed instructions are inside each folder's `instructions.md`.
