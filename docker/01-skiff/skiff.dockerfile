# ==============================================================================
# Lab 01: Skiff (Difficulty: Easy)
# Focus: Multiple classic Linux Local Privilege Escalation vectors
# ==============================================================================
FROM alpine:3.20

LABEL maintainer="Declusor" \
      description="Lab 01 - Skiff: Multi-path Linux Local Privilege Escalation" \
      level="easy"

# Install base packages and binaries required across exploitation paths
RUN apk add --no-cache \
    openssh-server \
    sudo \
    bash \
    findutils \
    coreutils \
    less \
    gawk \
    tar

# Configure SSH daemon securely (disables direct root SSH login)
RUN ssh-keygen -A \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config

# Create default user and set passwords
RUN adduser -D -s /bin/bash player \
    && echo "player:declusor" | chpasswd \
    && echo "root:declusor" | chpasswd

# Place root-only protected flag
RUN echo "CTF{declusor_01_skiff_multipath_privesc_pwned}" > /root/flag.txt \
    && chmod 600 /root/flag.txt

# [VECTOR 1] Overly permissive sudoers configuration with GTFOBins binaries
RUN echo "player ALL=(ALL) NOPASSWD: /usr/bin/find, /usr/bin/less, /usr/bin/awk, /bin/tar" >> /etc/sudoers

# [VECTOR 2] SUID bit set on GNU core utility /bin/cat (arbitrary file read)
RUN chmod 4755 /bin/cat

# [VECTOR 3] World-writable maintenance script executed via cron by root
RUN mkdir -p /opt \
    && printf '#!/bin/bash\n# Routine cleanup task\nrm -f /tmp/*.tmp 2>/dev/null\n' > /opt/backup.sh \
    && chmod 777 /opt/backup.sh \
    && echo "* * * * * /opt/backup.sh" > /etc/crontabs/root \
    && chmod 600 /etc/crontabs/root

# [VECTOR 4] Hardcoded contingency credential leaked in a hidden backup file
RUN mkdir -p /var/backups \
    && echo "TODO: Rotate contingency root password (current: declusor)" > /var/backups/.maintenance.txt \
    && chmod 644 /var/backups/.maintenance.txt

# [VECTOR 5] World-writable permissions on /etc/passwd
RUN chmod 666 /etc/passwd

# Container entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

WORKDIR /home/player
EXPOSE 22

ENTRYPOINT ["/entrypoint.sh"]