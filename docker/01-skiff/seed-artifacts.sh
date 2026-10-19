#!/bin/bash
set -euo pipefail

# 1. Configure Nginx staging portal with exposed .env and autoindex on /backups/
mkdir -p /var/www/html/backups /run/nginx

cat << 'EOF' > /etc/nginx/http.d/default.conf
server {
    listen 8081 default_server;
    server_name skiff.declusor.local;
    root /var/www/html;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    # Misconfiguration: Directory listing enabled on backups
    location /backups/ {
        autoindex on;
    }

    # Misconfiguration: Dotfiles (.env, .git) are not blocked
}
EOF

cat << 'EOF' > /var/www/html/index.html
<!DOCTYPE html>
<html>
<head><title>Declusor - Skiff Staging Node</title></head>
<body>
  <h1>Skiff Crew Portal (Staging v0.4)</h1>
  <p>Status: Maintenance mode active. Check local mail spool for cron migration notes.</p>
  <!-- TODO: Remove /.env and /backups/ before switching DNS to production -->
</body>
</html>
EOF

# 2. Application .env Secret
cat << 'EOF' > /var/www/html/.env
APP_ENV=staging
APP_DEBUG=true
DB_HOST=db.internal.declusor.local
DB_USER=skiff_app
DB_PASS=SkiffDB_Prod_2026!
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00DECLUSOR/B01SKIFF/9x8a7b6c5d4e3f2a1b
JWT_SIGNING_SECRET=7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069
EOF
chmod 644 /var/www/html/.env

# 3. Exposed backup note in web directory
cat << 'EOF' > /var/www/html/backups/db_migration_notes.txt
[Ops Note]
Emergency root password was temporarily synced with the maintenance file in /var/backups/.maintenance.txt.
Cron job /opt/backup.sh runs every minute as root to purge /tmp/*.tmp.
EOF

# 4. Leaked credentials in Shell History & Git Credentials
cat << 'EOF' > /home/player/.bash_history
ls -la /var/www/html
cat /var/www/html/.env
git config --global credential.helper store
curl -u admin:SkiffAdminPass2026 http://127.0.0.1:8081/backups/
mysql -h 10.10.20.15 -u root -p'SkiffRootpass!99' -e "SHOW DATABASES;"
sudo -l
EOF

cat << 'EOF' > /home/player/.git-credentials
https://player:ghp_DeclusorPersonalAccessToken9988776655@git.declusor.local
EOF

chown player:player /home/player/.bash_history /home/player/.git-credentials
chmod 600 /home/player/.bash_history /home/player/.git-credentials

# 5. Local Mail Spool Artifact
mkdir -p /var/spool/mail
cat << 'EOF' > /var/spool/mail/player
From: sysadmin@declusor.local
To: player@skiff.declusor.local
Subject: [URGENT] Staging Server Hardening Pending

Hey player,
Before the security audit tomorrow, please fix the following on Skiff:
1. /opt/backup.sh is currently chmod 777 so developers could edit it, but it runs as root in cron!
2. Clean up /var/backups/.maintenance.txt (it still has the root recovery password).
3. Restrict sudoers—right now your account can run find, less, awk, and tar without a password.
EOF
chown player:mail /var/spool/mail/player
chmod 660 /var/spool/mail/player