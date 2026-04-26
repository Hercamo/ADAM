#!/usr/bin/env bash
# ============================================================
# ADAM Rego Preflight Validator (Bash / Linux / WSL)
# ============================================================
# Runs `opa parse` and `opa check --v1-compatible` against every
# .rego file under the supplied root BEFORE the bootstrap script
# applies the bundle to a live OPA service.
#
# Origin: ADAM v1.7 / Sovereignty Connector 1.2 / audit log 0210.
# The NetStreamX initial deployment took 7 OPA-restart iterations
# to clear a sequence of grammar booby-traps that this validator
# catches in one shot.
#
# Usage:
#   ./validate-rego.sh <policy-root> [opa-image] [flight-recorder-path]
#
# Exits 0 on clean validation, non-zero on any failure. Suitable
# for use as a CI gate or pre-bootstrap check.
# ============================================================
set -euo pipefail

POLICY_ROOT="${1:-}"
OPA_IMAGE="${2:-openpolicyagent/opa:0.64.1}"
FR_PATH="${3:-}"

if [[ -z "$POLICY_ROOT" ]]; then
  echo "Usage: $0 <policy-root> [opa-image] [flight-recorder-path]" >&2
  exit 1
fi

POLICY_ROOT="$(cd "$POLICY_ROOT" && pwd)"

bar() { printf '%s\n' "======================================================================"; }
section() { echo; bar; echo " $1"; bar; }

emit_fr() {
  local event_type="$1"
  local summary="$2"
  if [[ -z "$FR_PATH" || ! -f "$FR_PATH" ]]; then
    return
  fi
  local payload
  payload=$(printf '{"validator":"scripts/preflight/validate-rego.sh","adam_version":"1.7","opa_image":"%s","v1_compatible":true,"summary":"%s"}' \
    "$OPA_IMAGE" "$summary")
  python3 "$FR_PATH" append \
    --event-type "$event_type" \
    --agent-id meta-integrity \
    --payload "$payload" >/dev/null
}

section "ADAM Rego Preflight Validator"
echo "Policy root : $POLICY_ROOT"
echo "OPA image   : $OPA_IMAGE"
echo "v1 mode     : enabled (--v1-compatible)"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is not on PATH. The validator requires Docker to run the OPA image." >&2
  emit_fr preflight_failed "Docker unavailable"
  exit 4
fi

mapfile -t REGO_FILES < <(find "$POLICY_ROOT" -type f -name "*.rego" | sort)
if [[ ${#REGO_FILES[@]} -eq 0 ]]; then
  echo "WARNING: no .rego files found under $POLICY_ROOT" >&2
  emit_fr preflight_failed "No rego files found"
  exit 3
fi

echo "Found ${#REGO_FILES[@]} .rego file(s) to validate:"
for f in "${REGO_FILES[@]}"; do
  echo "  - $f"
done

section "Stage 1 — opa parse (per file)"
PARSE_FAILED=0
for f in "${REGO_FILES[@]}"; do
  rel="${f#$POLICY_ROOT/}"
  echo -n "  [parse] $rel ... "
  if docker run --rm -v "$POLICY_ROOT:/p:ro" "$OPA_IMAGE" parse "/p/$rel" >/tmp/opa-parse.$$ 2>&1; then
    echo "OK"
  else
    echo "FAIL"
    cat /tmp/opa-parse.$$
    PARSE_FAILED=1
  fi
  rm -f /tmp/opa-parse.$$
done

if [[ $PARSE_FAILED -ne 0 ]]; then
  section "PREFLIGHT FAILED at parse stage"
  emit_fr preflight_failed "Rego parse stage failed"
  exit 10
fi

section "Stage 2 — opa check --v1-compatible (whole bundle)"
if docker run --rm -v "$POLICY_ROOT:/p:ro" "$OPA_IMAGE" check --v1-compatible /p >/tmp/opa-check.$$ 2>&1; then
  echo "  [check] bundle ... OK"
  rm -f /tmp/opa-check.$$
else
  echo "  [check] bundle ... FAIL"
  cat /tmp/opa-check.$$
  rm -f /tmp/opa-check.$$
  emit_fr preflight_failed "Rego check stage failed"
  exit 11
fi

section "PREFLIGHT PASSED"
echo "All ${#REGO_FILES[@]} rego file(s) parse cleanly under v1-compatible mode."
echo "Bundle is safe to load into a live OPA service invoked with --v1-compatible."
emit_fr preflight_passed "All rego files validated"
exit 0
