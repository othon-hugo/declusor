# Lab 04: Leviathan (Difficulty: Expert)

**Leviathan** simulates a hardened production edge gateway running in a hybrid Kubernetes/WireGuard network topology with `--privileged` container flags enabled.

## Services & Architecture

- **OpenSSH Server:** Port `2204`
- **Privileged Container Runtime:** `--privileged` with full capabilities (`CAP_SYS_ADMIN`)
- **Simulated Mesh & Orchestration Mounts:** Kubernetes ServiceAccounts, WireGuard VPN configs, and process core dumps.

## Artifacts & Attack Vectors

1. **Orchestration & Network Secrets:**
   - Kubernetes ServiceAccount token (`/var/run/secrets/kubernetes.io/serviceaccount/token`).
   - WireGuard private key and network topology (`/etc/wireguard/wg0.conf`).
2. **Forensic & Capability Vectors:**
   - **Core Dump Analysis:** `/var/crash/edge-auth.core` contains in-memory plaintext strings, including container root authentication tokens.
   - **File Capabilities:** `/usr/bin/tar` has `cap_dac_read_search+ep` assigned, allowing arbitrary file reading (`/root/.ssh/id_rsa`).
3. **Host Breakout Vector:**
   - Once container root is achieved, competitors identify `CAP_SYS_ADMIN` and exploit `cgroups` (`release_agent`) or direct host device mounting to escape the container and compromise the underlying Linux host.

## Takeaways

- Avoid running workloads in `--privileged` mode or granting unnecessary Linux capabilities (`CAP_SYS_ADMIN`, `CAP_DAC_READ_SEARCH`).
- Disable core dumps in production environments (`ulimit -c 0` or systemd-coredump restrictions) to prevent memory harvesting attacks. Implement runtime detection tools like Falco to catch `release_agent` modifications instantly.
