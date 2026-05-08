#!/usr/bin/env bash
# Build ADAM_Offline_Media from a connected Linux/macOS workstation.
# Produces Windows binaries + image tars that will work on the target Windows host.
set -euo pipefail

OUTPUT="${OUTPUT:-$(dirname "$0")/../ADAM_Offline_Media}"
KUBECTL_VERSION="${KUBECTL_VERSION:-v1.30.0}"
HELM_VERSION="${HELM_VERSION:-v3.14.4}"
K3D_VERSION="${K3D_VERSION:-v5.6.3}"
DOCKER_DESKTOP_URL="${DOCKER_DESKTOP_URL:-https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe}"

BIN="$OUTPUT/binaries"
IMG="$OUTPUT/images"
mkdir -p "$BIN" "$IMG"

echo "==> downloading kubectl $KUBECTL_VERSION"
curl -sSL "https://dl.k8s.io/release/$KUBECTL_VERSION/bin/windows/amd64/kubectl.exe" -o "$BIN/kubectl.exe"

echo "==> downloading helm $HELM_VERSION"
TMP="$(mktemp -d)"
curl -sSL "https://get.helm.sh/helm-$HELM_VERSION-windows-amd64.zip" -o "$TMP/helm.zip"
unzip -q "$TMP/helm.zip" -d "$TMP"
cp "$TMP/windows-amd64/helm.exe" "$BIN/helm.exe"

echo "==> downloading k3d $K3D_VERSION"
curl -sSL "https://github.com/k3d-io/k3d/releases/download/$K3D_VERSION/k3d-windows-amd64.exe" -o "$BIN/k3d.exe"

echo "==> downloading Docker Desktop installer"
curl -sSL "$DOCKER_DESKTOP_URL" -o "$BIN/docker-desktop-installer.exe"

echo "==> saving k3d/k3s base images"
docker pull rancher/k3s:v1.29.5-k3s1
docker pull "ghcr.io/k3d-io/k3d-proxy:$K3D_VERSION"
docker save "rancher/k3s:v1.29.5-k3s1" "ghcr.io/k3d-io/k3d-proxy:$K3D_VERSION" -o "$IMG/k3d-bundle.tar"

PH="$(dirname "$0")/placeholder_images"
mkdir -p "$PH"
cat > "$PH/Dockerfile" <<'EOF'
FROM python:3.12-slim
RUN pip install --no-cache-dir fastapi uvicorn
WORKDIR /app
COPY app.py /app/app.py
ENV PORT=8080
EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
EOF
cat > "$PH/app.py" <<'EOF'
import os
from fastapi import FastAPI
app = FastAPI()
role = os.environ.get("DIRECTOR_ROLE") or os.environ.get("AGENT_ORDINAL") or "generic"

@app.get("/health")
def health():
    return {"ok": True, "role": role}

@app.get("/")
def root():
    return {"service": "adam-placeholder", "role": role}
EOF

for spec in \
  "adam-core-engine:adam/core-engine:0.1" \
  "adam-boss-score:adam/boss-score:0.1" \
  "adam-flight-recorder:adam/flight-recorder:0.1" \
  "adam-constitution-director:adam/director:0.1" \
  "adam-agent:adam/agent:0.1"
do
  filename="${spec%%:*}"
  tag="${spec#*:}"
  echo "==> building $tag"
  docker build -t "$tag" "$PH"
  docker save "$tag" -o "$IMG/$filename.tar"
done

echo "==> writing MANIFEST.json"
python3 - "$OUTPUT" <<'PY'
import hashlib, json, os, pathlib, sys, time
out = pathlib.Path(sys.argv[1])
def describe(d):
    return [{
        "name": p.name,
        "size": p.stat().st_size,
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
    } for p in sorted(d.iterdir()) if p.is_file()]
m = {
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "binaries": describe(out / "binaries"),
    "images": describe(out / "images"),
}
(out / "MANIFEST.json").write_text(json.dumps(m, indent=2))
PY

echo
echo "Offline media ready at: $OUTPUT"
