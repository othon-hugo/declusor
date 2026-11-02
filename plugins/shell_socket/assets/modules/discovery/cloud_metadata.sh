#!/bin/bash
# -----------------------------------------------------------------------------
# Queries cloud instance metadata services to retrieve environment details and
# identity tokens.
# -----------------------------------------------------------------------------

METADATA_IP="169.254.169.254"

if probe_tcp "$METADATA_IP" 80 1; then
    # AWS Metadata (IMDSv2 with fallback to IMDSv1)
    AWS_TOKEN="$(fetch_url -X PUT -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" -t 2 "http://$METADATA_IP/latest/api/token")"

    if [ -n "$AWS_TOKEN" ]; then
        AWS_HDR="X-aws-ec2-metadata-token: $AWS_TOKEN"
        fetch_url -H "$AWS_HDR" -t 2 "http://$METADATA_IP/latest/meta-data/" | head -n 15 | label "AWS Instance Metadata"
        (
            fetch_url -H "$AWS_HDR" -t 2 "http://$METADATA_IP/latest/meta-data/iam/security-credentials/" | while IFS= read -r role; do
                [ -n "$role" ] || continue
                printf 'Role: %s\n' "$role"
                fetch_url -H "$AWS_HDR" -t 2 "http://$METADATA_IP/latest/meta-data/iam/security-credentials/$role"
                printf '\n'
            done
        ) | label "AWS IAM Security Credentials"
    else
        fetch_url -t 2 "http://$METADATA_IP/latest/meta-data/" | head -n 15 | label "AWS Instance Metadata"
        (
            fetch_url -t 2 "http://$METADATA_IP/latest/meta-data/iam/security-credentials/" | while IFS= read -r role; do
                [ -n "$role" ] || continue
                printf 'Role: %s\n' "$role"
                fetch_url -t 2 "http://$METADATA_IP/latest/meta-data/iam/security-credentials/$role"
                printf '\n'
            done
        ) | label "AWS IAM Security Credentials"
    fi

    # GCP Metadata
    fetch_url -H "Metadata-Flavor: Google" -t 2 "http://$METADATA_IP/computeMetadata/v1/instance/service-accounts/default/token" | label "GCP Service Account Token"

    # Azure Instance Metadata
    fetch_url -H "Metadata: true" -t 2 "http://$METADATA_IP/metadata/instance?api-version=2021-02-01" | label "Azure Instance Metadata"
fi

# Kubernetes Service Account Artifacts
K8S_SA="/var/run/secrets/kubernetes.io/serviceaccount"
if [ -d "$K8S_SA" ]; then
    (
        [ -r "$K8S_SA/namespace" ] && printf 'Namespace: %s\n' "$(cat "$K8S_SA/namespace" 2>/dev/null)"
        [ -r "$K8S_SA/token" ] && printf 'Token: %s\n' "$(cat "$K8S_SA/token" 2>/dev/null)"
    ) | label "Kubernetes Service Account"
fi
