# ==============================================================================
# Lab 04: Leviathan (Difficulty: Expert)
# Focus: Linux Capabilities, Core Dump Forensics, K8s Secrets & Privileged Escape
# ==============================================================================
FROM alpine:3.20

LABEL maintainer="Declusor" \
      description="Lab 04 - Leviathan: Capabilities, Crash Dumps & Privileged Breakout" \
      level="Expert"

RUN apk add --no-cache \
    openssh-server \
    openssh-client \
    python3 \
    bash \
    procps \
    util-linux \
    coreutils \
    binutils \
    tar \
    libcap

# Configure OpenSSH daemon (allow root SSH only via localhost/key after internal privesc)
RUN ssh-keygen -A \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PermitRootLogin.*/PermitRootLogin without-password/' /etc/ssh/sshd_config

# Create player account and set complex container root password
RUN adduser -D -s /bin/bash player \
    && echo "player:declusor" | chpasswd \
    && echo "root:Leviathan_Edge_Root_2026!" | chpasswd

# Stage 1 flag inside container /root
RUN echo "flag{declusor_04_container_root_achieved_now_escape_privileged}" > /root/flag_stage1.txt \
    && chmod 600 /root/flag_stage1.txt

# Seed K8s tokens, WireGuard config, core dump, and /usr/bin/tar capability
COPY seed-artifacts.sh /tmp/seed-artifacts.sh
RUN chmod +x /tmp/seed-artifacts.sh && /tmp/seed-artifacts.sh && rm /tmp/seed-artifacts.sh

COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

WORKDIR /home/player
EXPOSE 22

ENTRYPOINT ["/entrypoint.sh"]