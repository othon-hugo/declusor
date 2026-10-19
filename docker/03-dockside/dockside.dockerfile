# ==============================================================================
# Lab 03: Dockside (Difficulty: Hard)
# Focus: IaC/CI-CD credential harvesting -> devops pivot -> Docker socket escape
# ==============================================================================
FROM alpine:3.20

LABEL maintainer="Declusor" \
      description="Lab 03 - Dockside: IaC Artifacts & Docker Socket Container Escape" \
      level="hard"

RUN apk add --no-cache \
    openssh-server \
    openssh-client \
    python3 \
    bash \
    jq \
    docker-cli

# Configure OpenSSH daemon (allow PubkeyAuthentication for devops pivot)
RUN ssh-keygen -A \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config

# Create low-privileged player account
RUN adduser -D -s /bin/bash player \
    && echo "player:declusor" | chpasswd

# Seed devops user, Terraform state, Ansible vault pass, AWS/Docker configs
COPY seed-artifacts.sh /tmp/seed-artifacts.sh
RUN chmod +x /tmp/seed-artifacts.sh && /tmp/seed-artifacts.sh && rm /tmp/seed-artifacts.sh

# Intermediate flag inside /home/devops
RUN echo "flag{declusor_03_iac_compromised_now_breakout_via_docker_sock}" > /home/devops/flag_stage1.txt \
    && chown devops:devops /home/devops/flag_stage1.txt \
    && chmod 600 /home/devops/flag_stage1.txt

COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

WORKDIR /home/player
EXPOSE 22

ENTRYPOINT ["/entrypoint.sh"]