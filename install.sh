#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

agy plugin install "${SCRIPT_DIR}"
agy plugin list | grep -q 'auto-approver'
printf 'Plugin installed. Check README.md for permissions and trust requirements.\n'
