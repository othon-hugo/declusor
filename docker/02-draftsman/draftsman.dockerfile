# ==============================================================================
# Lab 02: Draftsman (Difficulty: Medium)
# Focus: /proc runtime leaks, Redis/SQLite data exposure, and SUID PATH hijack
# ==============================================================================

# --- Stage 1: Compile SUID binary ---
FROM alpine:3.20 AS builder

RUN apk add --no-cache gcc musl-dev
COPY healthcheck.c /tmp/healthcheck.c
RUN gcc -O2 -Wall /tmp/healthcheck.c -o /tmp/healthcheck

# --- Stage 2: Runtime image ---
FROM alpine:3.20

LABEL maintainer="Declusor" \
      description="Lab 02 - Draftsman: Runtime /proc Leaks, Redis & SUID PATH Hijacking" \
      level="medium"

RUN apk add --no-cache \
    openssh-server \
    python3 \
    redis \
    sqlite \
    bash \
    procps

# Configure OpenSSH daemon
RUN ssh-keygen -A \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config

# Create player user and root flag
RUN adduser -D -s /bin/bash player \
    && echo "player:declusor" | chpasswd \
    && echo "flag{declusor_02_draftsman_proc_redis_suid_pwned}" > /root/flag.txt \
    && chmod 600 /root/flag.txt

# Seed svc_telemetry account, SQLite DB, .pgpass, and Python daemon
COPY seed-artifacts.sh /tmp/seed-artifacts.sh
RUN chmod +x /tmp/seed-artifacts.sh && /tmp/seed-artifacts.sh && rm /tmp/seed-artifacts.sh

# Install SUID binary restricted to the 'telemetry' group (chmod 4750)
COPY --from=builder /tmp/healthcheck /usr/local/bin/healthcheck
RUN chown root:telemetry /usr/local/bin/healthcheck \
    && chmod 4750 /usr/local/bin/healthcheck

COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

WORKDIR /home/player
EXPOSE 22 8082

ENTRYPOINT ["/entrypoint.sh"]