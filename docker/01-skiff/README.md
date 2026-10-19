# Lab 01: Skiff (Difficulty: Easy)

**Skiff** simulates a legacy internal developer staging box (`http://localhost:8081`). It introduces beginners to standard Linux enumeration, misconfigured web roots, and classic local privilege escalation vectors.

## Services & Architecture

- **OpenSSH Server:** Port `2201`
- **Nginx Web Server:** Port `8081` (Serving static staging pages and auto-indexed `/backups/`)
- **BusyBox Cron Daemon:** Running `/opt/backup.sh` every minute as `root`

## Artifacts & Attack Vectors

1. **Exposed Web Secrets:** `/var/www/html/.env` contains database passwords and JWT signing secrets.
2. **Exposed Backup Directory:** `/backups/` has Nginx directory indexing enabled, revealing migration notes.
3. **Leaked CLI History:** `/home/player/.bash_history` and `/home/player/.git-credentials` show mistyped administrative commands and personal access tokens.
4. **Local Mail Spool:** `/var/spool/mail/player` contains a sysadmin warning about insecure script permissions.
5. **Privilege Escalation Vectors (Multi-Path):**
   - Overly permissive `sudoers` allowing execution of `find`, `less`, `awk`, and `tar` without a password.
   - SUID bit set on `/bin/cat`.
   - World-writable `/opt/backup.sh` executed by root's cron.
   - World-writable `/etc/passwd`.

## Takeaways

- Never deploy `.env` or version control metadata (`.git/`) to production web roots. Avoid putting passwords into shell histories or Git credential helpers.
- Audit web root permissions regularly and monitor for world-writable scripts scheduled in cron or `sudoers` misconfigurations.
