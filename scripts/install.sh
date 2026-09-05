#!/usr/bin/env bash
set -Eeuo pipefail

PREFIX="${PREFIX:-/usr/local}"
APP_DIR="${PREFIX}/share/linuxops-sentinel"
BIN_DIR="${PREFIX}/bin"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

install -d "${APP_DIR}" "${BIN_DIR}"
rm -rf "${APP_DIR}/src" "${APP_DIR}/config"
cp -R "${PROJECT_DIR}/src" "${APP_DIR}/src"
cp -R "${PROJECT_DIR}/config" "${APP_DIR}/config"
install -m 0755 "${PROJECT_DIR}/bin/linuxops-sentinel" "${BIN_DIR}/linuxops-sentinel"

if [[ -d /run/systemd/system ]]; then
  install -m 0644 "${PROJECT_DIR}/systemd/linuxops-sentinel.service" /etc/systemd/system/
  install -m 0644 "${PROJECT_DIR}/systemd/linuxops-sentinel.timer" /etc/systemd/system/
  install -d -m 0750 /var/log/linuxops-sentinel
  systemctl daemon-reload
fi

printf 'Installed LinuxOps Sentinel to %s\n' "${BIN_DIR}/linuxops-sentinel"