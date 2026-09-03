#!/usr/bin/env bash
set -euo pipefail

bash -n install.sh packaging/build_deb.sh

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

# The Debian release workflow delegates service construction to the shared
# package builder. Keep the security contract anchored to that single source
# of truth rather than duplicating service assertions in release.yml.
grep -q '^User=syswatch$' <(sed -n '/^cat > \"\$ROOT\/DEBIAN\/postinst\"/,/^EOF$/p' packaging/build_deb.sh)
grep -q '^Group=syswatch$' <(sed -n '/^cat > \"\$ROOT\/DEBIAN\/postinst\"/,/^EOF$/p' packaging/build_deb.sh)
grep -q '^Environment=SYSWATCH_STATE_DIR=/var/lib/syswatch$' <(sed -n '/^cat > \"\$ROOT\/DEBIAN\/postinst\"/,/^EOF$/p' packaging/build_deb.sh)
grep -q '^NoNewPrivileges=true$' <(sed -n '/^cat > \"\$ROOT\/DEBIAN\/postinst\"/,/^EOF$/p' packaging/build_deb.sh)
grep -q '^ProtectSystem=strict$' <(sed -n '/^cat > \"\$ROOT\/DEBIAN\/postinst\"/,/^EOF$/p' packaging/build_deb.sh)
grep -q '^CapabilityBoundingSet=$' <(sed -n '/^cat > \"\$ROOT\/DEBIAN\/postinst\"/,/^EOF$/p' packaging/build_deb.sh)
grep -q '^AmbientCapabilities=$' <(sed -n '/^cat > \"\$ROOT\/DEBIAN\/postinst\"/,/^EOF$/p' packaging/build_deb.sh)
grep -q '^StateDirectoryMode=0750$' <(sed -n '/^cat > \"\$ROOT\/DEBIAN\/postinst\"/,/^EOF$/p' packaging/build_deb.sh)

echo 'Least-privilege service security contract checks passed.'
