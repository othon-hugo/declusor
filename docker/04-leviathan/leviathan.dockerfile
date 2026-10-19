# ==============================================================================
# Lab 04: Leviathan (Difficulty: Expert)
# Focus: Full container breakout via privileged capabilities and host device access
# ==============================================================================
FROM alpine:3.20

LABEL maintainer="Declusor" \
      description="Lab 04 - Leviathan: Privileged Container Escape" \
      level="expert"

RUN apk add --no-cache \
    openssh-server \
    bash \
    procps \
    sudo \
    util-linux \
    coreutils \
    libcap

# Configure OpenSSH daemon
RUN ssh-keygen -A \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config

# Grant internal passwordless sudo so player can focus on host escape
RUN adduser -D -s /bin/bash player \
    && echo "player:declusor" | chpasswd \
    && echo "player ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

WORKDIR /home/player
EXPOSE 22

ENTRYPOINT ["/entrypoint.sh"]