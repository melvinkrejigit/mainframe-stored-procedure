#!/usr/bin/env bash
# Run this INSIDE WSL (Ubuntu-24.04) to prepare it as a self-hosted Azure
# Pipelines agent: installs Python, Node.js 20, and the Zowe CLI once so the
# pipeline no longer installs them on every run.
set -euo pipefail

sudo apt-get update
sudo apt-get install -y git unzip curl jq ca-certificates python3 python3-pip python-is-python3

curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt-get install -y nodejs

sudo npm install --global @zowe/cli

echo "WSL agent host preinstall complete. Next run pipelines/scripts/register-agent.sh."
