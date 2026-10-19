# ==============================================================================
# Lab 02: Draftsman (Difficulty: Medium)
# Focus: Custom SUID binary abuse through PATH environment hijacking
# ==============================================================================

# --- Stage 1: Build binary ---
FROM alpine:3.20 AS builder

RUN apk add --no-cache gcc musl-dev
COPY healthcheck.c /tmp/healthcheck.c
RUN gcc -O2 -Wall /tmp/healthcheck.c -o /tmp/healthcheck

# --- Stage 2: Final minimal runtime image ---
FROM alpine:3.20

LABEL maintainer="Declusor" \
      description="Lab 02 - Draftsman: SUID Binary PATH Hijacking" \
      level="medium"

RUN apk add --no-cache \
    openssh-server \
    bash \
    procps

# Configure OpenSSH daemon
RUN ssh-keygen -A \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config

# Create default player user
RUN adduser -D -s /bin/bash player \
    && echo "player:declusor" | chpasswd

# Place root-only protected flag
RUN echo "CTF{declusor_02_draftsman_suid_path_hijack}" > /root/flag.txt \
    && chmod 600 /root/flag.txt

# Copy compiled binary from builder and apply SUID bit
COPY --from=builder /tmp/healthcheck /usr/local/bin/healthcheck
RUN chown root:root /usr/local/bin/healthcheck \
    && chmod 4755 /usr/local/bin/healthcheck

COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

WORKDIR /home/player
EXPOSE 22

ENTRYPOINT ["/entrypoint.sh"]