#!/usr/bin/env bash
set -euo pipefail

bash -n install.sh

grep -q 'SYSWATCH_REF' install.sh
grep -q 'git check-ref-format' install.sh
grep -q 'BACKUP=' install.sh
grep -q 'rollback()' install.sh
grep -q 'SWAPPED=1' install.sh
grep -q 'systemctl disable --now' install.sh
grep -q 'systemctl enable --now' install.sh
grep -q '127.0.0.1:8080' install.sh

grep -q 'rm -rf "$PREFIX"' install.sh
if grep -n 'rm -rf "$PREFIX"' install.sh | grep -qv 'rollback'; then
  # The only active-tree removal must occur inside the explicit rollback path.
  line="$(grep -n 'rm -rf "$PREFIX"' install.sh | head -n1 | cut -d: -f1)"
  if [[ "$line" -lt "$(grep -n '^rollback()' install.sh | cut -d: -f1)" ]]; then
    echo 'Installer must not remove the active tree before staging/backup.' >&2
    exit 1
  fi
fi

echo 'Installer lifecycle contract checks passed.'
