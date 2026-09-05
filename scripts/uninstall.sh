#!/usr/bin/env bash
set -Eeuo pipefail

PREFIX="${PREFIX:-/usr/local}"
if [[ -d /run/systemd/system ]]; then
  systemctl disable --now linuxops-sentinel.timer 2>/dev/null || true
  rm -f /etc/systemd/system/linuxops-sentinel.service /etc/systemd/system/linuxops-sentinel.timer
  systemctl daemon-reload
fi
rm -f "${PREFIX}/bin/linuxops-sentinel"
rm -rf "${PREFIX}/share/linuxops-sentinel"
printf 'Removed LinuxOps Sentinel from %s\n' "${PREFIX}"