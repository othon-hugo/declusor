# ==============================================================================
# Lab 01: Skiff (Difficulty: Easy)
# Focus: Web/Dev hygiene, sensitive developer artifacts, and multi-path PrivEsc
# ==============================================================================
FROM alpine:3.20

LABEL maintainer="Declusor" \
      description="Lab 01 - Skiff: Legacy Web Node & Multi-path Local PrivEsc" \
      level="easy"

RUN apk add --no-cache \
    openssh-server \
    nginx \
    sudo \
    bash \
    curl \
    git \
    findutils \
    coreutils \
    less \
    gawk \
    tar

# Configure OpenSSH daemon
RUN ssh-keygen -A \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config

# Create user and root credentials (root has a distinct password discoverable via artifacts)
RUN adduser -D -s /bin/bash player \
    && echo "player:declusor" | chpasswd \
    && echo "root:SkiffRootPass2026!" | chpasswd

# Protected root flag
RUN echo "flag{declusor_01_skiff_multipath_privesc_pwned}" > /root/flag.txt \
    && chmod 600 /root/flag.txt

# [VECTOR 1] Overly permissive sudoers rules (GTFOBins)
RUN echo "player ALL=(ALL) NOPASSWD: /usr/bin/find, /usr/bin/less, /usr/bin/awk, /bin/tar" >> /etc/sudoers

# [VECTOR 2] SUID bit on /bin/cat
RUN chmod 4755 /bin/cat

# [VECTOR 3] World-writable root cron script
RUN mkdir -p /opt \
    && printf '#!/bin/bash\n# Routine cleanup task\nrm -f /tmp/*.tmp 2>/dev/null\n' > /opt/backup.sh \
    && chmod 777 /opt/backup.sh \
    && echo "* * * * * /opt/backup.sh" > /etc/crontabs/root \
    && chmod 600 /etc/crontabs/root

# [VECTOR 4] Leaked root password in hidden backup file
RUN mkdir -p /var/backups \
    && echo "TODO: Rotate contingency root password (current: SkiffRootPass2026!)" > /var/backups/.maintenance.txt \
    && chmod 644 /var/backups/.maintenance.txt

# [VECTOR 5] World-writable /etc/passwd
RUN chmod 666 /etc/passwd

# Seed web service, mail spool, .env, and shell history artifacts
COPY seed-artifacts.sh /tmp/seed-artifacts.sh
RUN chmod +x /tmp/seed-artifacts.sh && /tmp/seed-artifacts.sh && rm /tmp/seed-artifacts.sh

COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

WORKDIR /home/player
EXPOSE 22 8081

ENTRYPOINT ["/entrypoint.sh"]