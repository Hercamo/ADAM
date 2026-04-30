# Air-gap setup

The Connector's `.exe` is tiny (~30 MB). Every large artifact — container
images, installers, binaries — lives in a sibling folder called
`ADAM_Offline_Media/`. You build this folder once on an internet-connected
workstation and then carry it (USB, internal share, signed bundle) to the
air-gapped target.

## One-time build (connected workstation)

### Windows

```powershell
scripts\build_offline_media.ps1
```

### Linux / macOS

```bash
scripts/build_offline_media.sh
```

Both scripts:

1. Download pinned versions of `kubectl.exe`, `helm.exe`, `k3d.exe`,
   and the Docker Desktop installer for Windows.
2. `docker pull` the k3s + k3d-proxy images and `docker save` them into
   `ADAM_Offline_Media/images/k3d-bundle.tar`.
3. Build five placeholder ADAM service images (CORE Engine, BOSS Score,
   Flight Recorder, Director, Agent) from a minimal FastAPI scaffold in
   `scripts/placeholder_images/`, then `docker save` each into a tar.
4. Produce `ADAM_Offline_Media/MANIFEST.json` with SHA-256 digests of every
   file.

Total bundle size: ~4–6 GB, dominated by the Docker Desktop installer and
the k3s image.

## Verify on the target

```cmd
adam_sovereignty_connector.exe check
```

Prints a table of expected files with `yes` / `missing` marks. Every `yes` is
a green light for the next step.

## Replacing placeholder images with your real ADAM services

The five `adam-*.tar` files ship a generic FastAPI stub that exposes
`GET /health`. When you implement the real services (CORE Engine intent
routing, BOSS Score computation, Flight Recorder persistence, Director
arbitration, Agent behaviour), rebuild them under the same image tags
(`adam/core-engine:0.1`, `adam/boss-score:0.1`, …), re-`docker save` into
the matching tar filenames, and copy the new bundle over. The Connector's
`import_offline_images` command will pick them up.

## Signing the bundle (optional)

Teams that need supply-chain assurance can sign `MANIFEST.json` with
`cosign` or a Windows Authenticode cert; the Connector does not verify
signatures today, but `check` will happily surface a signature file if
present (it's logged but not parsed). Adding verification is a small
addition to `core/preflight.py`.

## What the Connector never does

* It never fetches anything from the public internet.
* It never runs `docker pull` against external registries.
* It never writes outside `%PROGRAMFILES%\AdamSovereigntyConnector\`,
  `%PROGRAMDATA%\AdamSovereigntyConnector\`, or the cluster.
* The AI never sees raw shell — only the catalog commands.
