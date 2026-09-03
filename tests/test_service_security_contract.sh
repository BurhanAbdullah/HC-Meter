#!/usr/bin/env bash
set -euo pipefail

bash -n install.sh

# Validate the source installer contract.
grep -q '^User=\$SERVICE_USER$' install.sh
grep -q '^Group=\$SERVICE_GROUP$' install.sh
grep -q '^Environment=SYSWATCH_STATE_DIR=\$STATE_DIR$' install.sh
grep -q '^UMask=0077$' install.sh
grep -q '^NoNewPrivileges=true$' install.sh
grep -q '^PrivateTmp=true$' install.sh
grep -q '^PrivateDevices=true$' install.sh
grep -q '^ProtectSystem=strict$' install.sh
grep -q '^ProtectHome=read-only$' install.sh
grep -q '^ProtectKernelTunables=true$' install.sh
grep -q '^ProtectKernelModules=true$' install.sh
grep -q '^ProtectControlGroups=true$' install.sh
grep -q '^RestrictSUIDSGID=true$' install.sh
grep -q '^CapabilityBoundingSet=$' install.sh
grep -q '^AmbientCapabilities=$' install.sh
grep -q '^ReadWritePaths=\$STATE_DIR$' install.sh

grep -q 'useradd --system' install.sh
grep -q 'shell /usr/sbin/nologin' install.sh
grep -q 'install -d -m 0750 -o "\$SERVICE_USER" -g "\$SERVICE_GROUP" "\$STATE_DIR"' install.sh
grep -q 'chown -R root:root "\$PREFIX"' install.sh

grep -q 'SYSWATCH_STATE_DIR' syswatch/agent/causal_engine.py

# Validate the shared Debian builder directly. The release workflow delegates
# package/service construction to this file, so its contract must be tested
# from the same repository checkout rather than assuming it exists on main.
bash -n packaging/build_deb.sh
builder_service="$(mktemp)"
trap 'rm -f "$builder_service"' EXIT
awk '/^cat > \"\$ROOT\/DEBIAN\/postinst\"/{inside=1; next} inside && /^EOF$/{exit} inside{print}' packaging/build_deb.sh > "$builder_service"
for contract in \
  '^User=syswatch$' \
  '^Group=syswatch$' \
  '^Environment=SYSWATCH_STATE_DIR=/var/lib/syswatch$' \
  '^NoNewPrivileges=true$' \
  '^ProtectSystem=strict$' \
  '^CapabilityBoundingSet=$' \
  '^AmbientCapabilities=$' \
  '^StateDirectoryMode=0750$'; do
  grep -q "$contract" "$builder_service"
done

echo 'Least-privilege service security contract checks passed.'
