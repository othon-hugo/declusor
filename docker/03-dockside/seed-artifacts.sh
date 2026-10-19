#!/bin/bash
set -euo pipefail

# 1. Create 'devops' user (the account that will hold docker socket privileges)
adduser -D -s /bin/bash devops
echo "devops:DevOps_Master_2026!" | chpasswd

# 2. Generate SSH keypair for 'devops' so player can pivot via SSH key found in tfstate
mkdir -p /home/devops/.ssh
ssh-keygen -t ed25519 -f /home/devops/.ssh/id_ed25519 -N "" -C "devops@dockside.declusor.local"
cp /home/devops/.ssh/id_ed25519.pub /home/devops/.ssh/authorized_keys
chown -R devops:devops /home/devops/.ssh
chmod 700 /home/devops/.ssh
chmod 600 /home/devops/.ssh/authorized_keys /home/devops/.ssh/id_ed25519

PRIV_KEY_ESCAPED=$(awk '{printf "%s\\n", $0}' /home/devops/.ssh/id_ed25519)

# 3. Seed Terraform State Backup containing the raw private SSH key and AWS credentials
mkdir -p /opt/infra/ansible /etc/gitlab-runner
cat << EOF > /opt/infra/terraform.tfstate.backup
{
  "version": 4,
  "terraform_version": "1.9.5",
  "serial": 14,
  "lineage": "c9a1d2e3-4f5b-6c7d-8e9f-0a1b2c3d4e5f",
  "resources": [
    {
      "mode": "managed",
      "type": "tls_private_key",
      "name": "devops_runner_ssh_key",
      "provider": "provider[\"registry.terraform.io/hashicorp/tls\"]",
      "instances": [
        {
          "schema_version": 1,
          "attributes": {
            "algorithm": "ED25519",
            "user": "devops",
            "private_key_openssh": "${PRIV_KEY_ESCAPED}"
          }
        }
      ]
    },
    {
      "mode": "managed",
      "type": "aws_db_instance",
      "name": "logistics_rds",
      "instances": [
        {
          "attributes": {
            "username": "rds_master",
            "password": "DevOps_Master_2026!",
            "endpoint": "rds.internal.declusor.local:5432"
          }
        }
      ]
    }
  ]
}
EOF
chmod 644 /opt/infra/terraform.tfstate.backup

# 4. Seed Ansible Inventory & Forgotten Vault Password File
cat << 'EOF' > /opt/infra/ansible/inventory.ini
[ci_runners]
dockside.declusor.local ansible_user=devops

[production_hosts]
172.17.0.1 ansible_user=root
EOF

echo "DevOps_Master_2026!" > /opt/infra/ansible/.vault_pass
chmod 644 /opt/infra/ansible/inventory.ini /opt/infra/ansible/.vault_pass

# 5. Seed GitLab Runner Configuration
cat << 'EOF' > /etc/gitlab-runner/config.toml
concurrent = 4
check_interval = 0

[[runners]]
  name = "dockside-docker-runner"
  url = "https://git.declusor.local/"
  token = "glrt-DeclusorRunnerRegistrationToken991122"
  executor = "docker"
  [runners.docker]
    image = "alpine:3.20"
    volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/cache"]
EOF
chmod 644 /etc/gitlab-runner/config.toml

# 6. Seed Cloud & Package Manager Secrets inside /home/devops
mkdir -p /home/devops/.aws /home/devops/.docker

cat << 'EOF' > /home/devops/.aws/credentials
[default]
aws_access_key_id = AKIAIOSFODNN7DECLUSOR
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYDECLUSORKEY
region = us-east-1
EOF

cat << 'EOF' > /home/devops/.docker/config.json
{
  "auths": {
    "registry.declusor.local:5000": {
      "auth": "ZGV2b3BzOkRldk9wc19NYXN0ZXJfMjAyNiE="
    }
  }
}
EOF

cat << 'EOF' > /home/devops/.npmrc
//npm.declusor.local/:_authToken=npm_DeclusorPublishToken123456789
EOF

chown -R devops:devops /home/devops/.aws /home/devops/.docker /home/devops/.npmrc
chmod 600 /home/devops/.aws/credentials /home/devops/.docker/config.json /home/devops/.npmrc