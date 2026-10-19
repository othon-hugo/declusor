# ==============================================================================
# Lab 03: Dockside (Difficulty: Hard)
# Focus: Container escape via exposed host Docker daemon socket
# ==============================================================================
FROM alpine:3.20

LABEL maintainer="Declusor" \
      description="Lab 03 - Dockside: Docker Socket Container Escape" \
      level="hard"

RUN apk add --no-cache \
    openssh-server \
    bash \
    docker-cli

# Configure OpenSSH daemon
RUN ssh-keygen -A \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config

# Create default player user
RUN adduser -D -s /bin/bash player \
    && echo "player:declusor" | chpasswd

# Intermediate flag informing player to breakout to the host
RUN echo "CTF{declusor_03_internal_reached_now_escape_to_host}" > /root/flag_internal.txt \
    && chmod 644 /root/flag_internal.txt

COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

WORKDIR /home/player
EXPOSE 22

ENTRYPOINT ["/entrypoint.sh"]