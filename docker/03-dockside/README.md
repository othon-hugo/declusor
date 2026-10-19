# Lab 03: Dockside (Difficulty: Hard)

**Dockside** simulates a shared CI/CD build runner and Infrastructure-as-Code (IaC) management workspace. It bridges developer secret management failures with container orchestration attacks.

## Services & Architecture

- **OpenSSH Server:** Port `2203`
- **Mounted Host Docker Socket:** `/var/run/docker.sock`

## Artifacts & Attack Vectors

1. **IaC State Leaks:** `/opt/infra/terraform.tfstate.backup` stores unencrypted resource attributes, including the raw Ed25519 private SSH key for the `devops` administrative account and database credentials.
2. **CI/CD & Cloud Artifacts:**
   - Ansible vault password file (`.vault_pass`) and inventory.
   - GitLab Runner configuration (`config.toml`).
   - Cloud and registry credential files (`~/.aws/credentials`, `~/.docker/config.json`, `~/.npmrc`).
3. **Container Escape Vector:**
   - The `player` account pivots to `devops` using the harvested private key.
   - The `devops` user belongs to the Docker socket group, allowing container breakout via sibling container spawning (`docker run -v /:/host ...`).

## Takeaways

- Never store unencrypted state files (`terraform.tfstate`) locally on build agents; always use remote encrypted backends (e.g., Terraform Cloud, S3 with KMS).
- Mounting `/var/run/docker.sock` into CI containers grants full host root access. Use rootless container builders (like Kaniko or Podman) to eliminate Docker daemon exposure.
