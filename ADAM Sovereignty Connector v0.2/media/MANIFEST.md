# ADAM_Offline_Media — contents manifest

The connector is air-gap friendly: it never reaches out to the public
internet. Instead it reads every binary and container image from a sibling
folder called `ADAM_Offline_Media/`, which you prepare once on a
connected workstation and carry (USB / internal share) to the target host.

Place this folder next to `adam_sovereignty_connector.exe`:

```
<install-dir>\
 ├── adam_sovereignty_connector.exe
 └── ADAM_Offline_Media\
      ├── MANIFEST.json                        <- builder writes a summary here
      ├── binaries\
      │    ├── docker-desktop-installer.exe    <- Docker Desktop for Windows
      │    ├── kubectl.exe                     <- upstream kubectl 1.29+ (Windows/amd64)
      │    ├── helm.exe                        <- Helm 3.14+ (Windows/amd64)
      │    └── k3d.exe                         <- k3d 5.6+ (Windows/amd64)
      └── images\
           ├── k3d-bundle.tar                  <- k3s + k3d-proxy images (`docker save`)
           ├── adam-core-engine.tar
           ├── adam-boss-score.tar
           ├── adam-flight-recorder.tar
           ├── adam-constitution-director.tar
           └── adam-agent.tar
```

## Building the media folder

Run `scripts/build_offline_media.ps1` (Windows) or `scripts/build_offline_media.sh`
(Linux/macOS) on a connected host. The scripts:

1. Download the binaries at pinned versions.
2. `docker pull` the k3d / k3s images and `docker save` them.
3. Build the five ADAM placeholder images and `docker save` each one.
4. Compute SHA-256 digests and write `MANIFEST.json`.

## Verifying

`adam_sovereignty_connector.exe check` validates every filename in this
manifest and prints which are present or missing.

## Replacing placeholder images

Each `adam-*.tar` is a small FastAPI placeholder that exposes `/health`. Once
you have your real implementations, rebuild those images under the same
names and versions, regenerate the tars, and the connector will pick them up
at the next `import_offline_images` step.
