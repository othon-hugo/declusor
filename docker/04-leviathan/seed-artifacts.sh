#!/bin/bash
set -euo pipefail

# 1. Configure container root SSH key for local root pivot (if read via cap_dac_read_search)
mkdir -p /root/.ssh
ssh-keygen -t rsa -b 2048 -f /root/.ssh/id_rsa -N "" -C "root@leviathan.declusor.local"
cp /root/.ssh/id_rsa.pub /root/.ssh/authorized_keys
chmod 700 /root/.ssh
chmod 600 /root/.ssh/id_rsa /root/.ssh/authorized_keys

# 2. Seed Kubernetes ServiceAccount Mounts & Docker Swarm Secrets
K8S_DIR="/var/run/secrets/kubernetes.io/serviceaccount"
mkdir -p "$K8S_DIR" /run/secrets

echo "declusor-production" > "$K8S_DIR/namespace"
cat << 'EOF' > "$K8S_DIR/token"
eyJhbGciOiJSUzI1NiIsImtpZCI6ImRlY2x1c29yLWs4cy1rZXkifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWNsdXNvci1wcm9kdWN0aW9uIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImJyZWFrd2F0ZXItc2EtdG9rZW4iLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6ZGVjbHVzb3ItcHJvZHVjdGlvbjpicmVha3dhdGVyLWVkZ2UifQ.declusor_sig
EOF
chmod 644 "$K8S_DIR/namespace" "$K8S_DIR/token"

cat << 'EOF' > /run/secrets/vault_unseal_key
UNSEAL_SHARD_1=8f9d2a1b4c6e7f0a3b5c8d9e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a
EOF
chmod 640 /run/secrets/vault_unseal_key

# 3. Seed WireGuard VPN Configuration
mkdir -p /etc/wireguard
cat << 'EOF' > /etc/wireguard/wg0.conf
[Interface]
Address = 10.200.0.1/24
PrivateKey = YnJlYWt3YXRlcl93aXJlZ3VhcmRfcHJpdmF0ZV9rZXlfMjAyNl9kZWNsdXNvcg==
ListenPort = 51820

# Internal Control Plane Peer
[Peer]
PublicKey = cHVibGljX2tleV9kZWNsdXNvcl9jb3JlX3JvdXRlcl8wMQ==
AllowedIPs = 10.200.0.0/16, 172.16.0.0/12
Endpoint = 10.10.0.1:51820
EOF
chmod 640 /etc/wireguard/wg0.conf

# 4. Seed Simulated Process Core Dump in /var/crash containing in-memory root secret
mkdir -p /var/crash
python3 - << 'EOF'
with open("/var/crash/edge-auth.core", "wb") as f:
    f.write(b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 64)
    f.write(b"CORE_DUMP_PROCESS=edge-auth-daemon\x00")
    f.write(b"MEM_HEAP_ALLOC_0x7fff810020\x00")
    f.write(b"AUTH_PROVIDER=pam_unix\x00")
    f.write(b"CACHED_ROOT_AUTH_TOKEN=Leviathan_Edge_Root_2026!\x00")
    f.write(b"SSH_PRIVATE_KEY_PATH=/root/.ssh/id_rsa\x00")
    f.write(b"\x00" * 128)
EOF
chmod 644 /var/crash/edge-auth.core

# 5. Assign CAP_DAC_READ_SEARCH to /usr/bin/tar (allows bypassing file read permissions)
setcap cap_dac_read_search+ep /usr/bin/tar