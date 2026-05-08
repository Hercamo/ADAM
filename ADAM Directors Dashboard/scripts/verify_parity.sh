#!/usr/bin/env bash
# verify_parity.sh
# md5-compares an installed Directors Dashboard copy against this spec dir.
#
# Usage:
#   bash scripts/verify_parity.sh <installed_static_dashboard_dir> [<installed_app_dir>]
#
# Examples:
#   # Verify just the SPA layer:
#   bash scripts/verify_parity.sh \
#     "D:/ADAM/deployment/NetStreamX/netstreamx_app/static/dashboard"
#
#   # Verify SPA + Flask blueprints:
#   bash scripts/verify_parity.sh \
#     "D:/ADAM/deployment/NetStreamX/netstreamx_app/static/dashboard" \
#     "D:/ADAM/deployment/NetStreamX/netstreamx_app"
#
# Exits 0 on full parity, non-zero on any mismatch.

set -u

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <installed_static_dashboard_dir> [<installed_app_dir>]" >&2
  exit 2
fi

INSTALLED_SPA="$1"
INSTALLED_APP="${2:-}"

# Resolve the spec dir as the parent of this script's directory.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SPEC="$(cd -- "$SCRIPT_DIR/.." && pwd)"

echo "Spec:        $SPEC"
echo "Installed:   $INSTALLED_SPA"
[ -n "$INSTALLED_APP" ] && echo "App:         $INSTALLED_APP"
echo "------------------------------------------------------------"

ok=0
fail=0

compare() {
  local rel="$1"
  local left="$2"
  local right="$3"

  if [ ! -f "$left" ]; then
    printf "MISS  spec missing:    %s\n" "$rel"
    fail=$((fail + 1))
    return
  fi
  if [ ! -f "$right" ]; then
    printf "MISS  installed missing: %s\n" "$rel"
    fail=$((fail + 1))
    return
  fi

  local a b
  a=$(md5sum "$left"  | awk '{print $1}')
  b=$(md5sum "$right" | awk '{print $1}')

  if [ "$a" = "$b" ]; then
    printf "OK    %s  %s\n" "$rel" "$a"
    ok=$((ok + 1))
  else
    printf "FAIL  %s\n      spec=%s\n      live=%s\n" "$rel" "$a" "$b"
    fail=$((fail + 1))
  fi
}

# --- SPA layer ----------------------------------------------------
SPA_FILES=(
  "index.html"
  "assets/app.js"
  "assets/styles.css"
  "assets/banner.svg"
  "assets/demo/demo_overlays.css"
  "assets/demo/demo_overlays.js"
  "assets/views/directors_views.css"
  "assets/views/directors_views.js"
  "data/demo-data.js"
)

for rel in "${SPA_FILES[@]}"; do
  compare "$rel" "$SPEC/$rel" "$INSTALLED_SPA/$rel"
done

# --- Flask blueprints (only if app dir was given) -----------------
if [ -n "$INSTALLED_APP" ]; then
  SERVER_FILES=(
    "dashboard_api.py"
    "dashboard_views.py"
    "demo_addons.py"
  )
  for f in "${SERVER_FILES[@]}"; do
    compare "server/$f" "$SPEC/server/$f" "$INSTALLED_APP/$f"
  done
fi

echo "------------------------------------------------------------"
echo "Parity:  ${ok} OK, ${fail} FAIL"

if [ "$fail" -ne 0 ]; then
  exit 1
fi
exit 0
