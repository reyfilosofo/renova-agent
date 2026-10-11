# MONEY Ω · CODEX research runtime · 2026-10-11

Python 3.11 or newer runs this stdlib service without installing packages.
From `money-codex/`:

```sh
python3 run.py scan --state-dir ../.local-data/resources --config config/resource_sources.json
python3 run.py status --state-dir ../.local-data/resources
python3 run.py export --state-dir ../.local-data/resources --output ../.local-data/resources/latest-packet.json
python3 run.py serve --state-dir ../.local-data/resources --host 127.0.0.1 --port 8787
```

`serve` starts the loopback dashboard and scheduler. `worker` runs the same scheduler without HTTP. State survives restarts in SQLite with WAL; active jobs use expiring leases and a per-claim fencing token. Job completion and its evidence writes commit together. Failed source reads produce source failures and bounded retries, not invented opportunities. Blocked and rate-limited sources receive a cooldown.

A process lock prevents two schedulers from owning one state directory. SQLite supports a separate manual scan while the scheduler runs, without duplicate active jobs for a source. Stop the process to stop future scans. A Codex task or transient workspace cannot promise 24/7 uptime by itself.

Install `money-resources.service` into a user systemd directory after reviewing the paths. The service restarts after failures and uses the existing local state directory. Installation must happen on the actual persistent host; the template alone is not deployment evidence. AppDeploy's market cron is independent and remains its only automatic market writer.

Optional container (Linux):

```sh
docker build -f deploy/Dockerfile -t money-resources .
docker run --network host --mount type=bind,src=/absolute/path/to/private-state,dst=/state money-resources
```

The container retains loopback binding; it does not publish the dashboard on the internet. Keep state volumes private. The package accepts no financial routes, secrets, wallet signatures, claims, paid purchases or survey submissions. Research packets may be exported or imported offline; checksum/TTL validation does not authenticate another model or establish an agent connection.
