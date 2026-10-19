# Lab 02: Draftsman (Difficulty: Medium)

**Draftsman** simulates an internal vessel telemetry processing node. It introduces intermediate concepts: runtime environment leaks via `/proc`, database credential harvesting, and C binary SUID exploitation through `PATH` variable manipulation.

## Services & Architecture

- **OpenSSH Server:** Port `2202`
- **Python Telemetry API:** Port `8082`
- **Local Redis Instance:** Port `6379` (Unauthenticated local cache)
- **SQLite Database:** `/var/lib/draftsman/vessels.db`

## Artifacts & Attack Vectors

1. **Runtime Leaks (`/proc`):** The Python background daemon runs as user `svc_telemetry`, passing sensitive API keys and environment variables inspectable via `/proc/<PID>/environ` and `/proc/<PID>/cmdline`.
2. **Caching & Database Artifacts:**
   - Unauthenticated local Redis server containing session tokens and configuration keys.
   - SQLite database storing service account hints.
   - Database client helper files (`~/.pgpass`, `~/.my.cnf`) storing plaintext credentials.
3. **Privilege Escalation Vector:**
   - Custom compiled C binary (`/usr/local/bin/healthcheck`) owned by `root:telemetry` with the SUID bit set (`4750`). It invokes `system("uptime")` without an absolute path.
   - Competitors pivot to `svc_telemetry` (using harvested credentials), join group `telemetry`, and execute `PATH` hijacking to escalate to `root`.

## Takeaways

- Understand that environment variables are easily read by anyone on the same system unless `/proc` is mounted with `hidepid=2`. Always use absolute executable paths inside system calls (`/usr/bin/uptime` instead of `uptime`).
- Restrict access to local caching engines (Redis) with proper authentication an
