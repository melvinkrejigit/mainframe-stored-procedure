#!/usr/bin/env bash
# Run this INSIDE WSL (after pipelines/scripts/setup-wsl-agent-host.sh) to
# register it as a self-hosted Azure Pipelines agent. Requires a PAT with
# "Agent Pools (Read & manage)" scope, created in Azure DevOps under
# User settings > Personal access tokens.
set -euo pipefail

AZP_URL="https://dev.azure.com/melvinrejiuk01"
AZP_POOL="SelfHosted-Mainframe"
AZP_AGENT_NAME="wsl-ubuntu-agent"
AGENT_VERSION="3.243.0"

read -rsp "Enter your Azure DevOps PAT: " AZP_TOKEN
echo

sudo mkdir -p /opt/azp-agent
sudo chown "$USER":"$USER" /opt/azp-agent
cd /opt/azp-agent

curl -o agent.tar.gz -L \
  "https://download.agent.dev.azure.com/agent/${AGENT_VERSION}/vsts-agent-linux-x64-${AGENT_VERSION}.tar.gz"
tar zxvf agent.tar.gz

# installdependencies.sh doesn't recognize Ubuntu 24.04 and tries to install
# retired libicu52/55 packages; skip it since 24.04 already ships compatible
# libicu74/libssl3/libkrb5/zlib1g that the agent's .NET runtime needs.

./config.sh --unattended \
  --url "$AZP_URL" \
  --auth pat \
  --token "$AZP_TOKEN" \
  --pool "$AZP_POOL" \
  --agent "$AZP_AGENT_NAME" \
  --acceptTeeEula

# svc.sh needs systemd, which WSL only provides if /etc/wsl.conf has
# [boot]\nsystemd=true (Ubuntu 24.04 on WSL enables this by default).
# If svc.sh fails, run the agent in the foreground instead: ./run.sh
sudo ./svc.sh install
sudo ./svc.sh start
sudo ./svc.sh status
