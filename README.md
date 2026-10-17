# 9 Project gallery reproducibility package

Use this repository to inspect the frozen gallery implementation and repeat its placement, thumbnail, and navigation checks. The authors selected code, artwork assets, a collection-only SQL snapshot, and machine-readable test results for this release. Manuscripts and editorial files stay outside the repository and release archive.

## Recorded findings

The audit covers 16 primary artworks from 17 database records. Record 35 duplicates the image of record 33 and carries the title `test`.

Across 35 generator scenarios, the identifier, allocation, and image-plane geometry checks pass. The original thumbnail selection fails in 26 scenarios. An isolated index-expression change reduces those failures to zero while preserving the generated scene markup and coordinates. The checks detect 14 output mutations and two source mutations.

The authors ran 42 backend checks against disposable PHP 8.2.34 and MySQL 8.0.46 containers; all passed. Three controlled browser repetitions and a browser-owned pointer-lock run reproduce a stack overflow at sensitivity 1.5. Baseline sensitivity 1 delivers the mouse event. The Linux generator run agrees with the macOS run apart from runtime metadata.

These results come from the authors' execution on 17 October 2026. The authors prepared this source-only release on 18 October 2026 and repeated the deterministic checks during packaging. They did not conduct an external independent reproduction, a participant study, or physical phone/headset testing. The mobile result uses browser emulation. Geometry checks cover image planes and door clearance; they do not establish full visibility, accessibility, security, or performance.

## Contents

- `snapshot/`: original frontend, the isolated thumbnail variant, backend, Dockerfile, and artwork-only SQL.
- `assets/`: images, audio, and frontend dependencies used by the snapshot.
- `scripts/`: audit and experiment runners.
- `results/`: recorded JSON, CSV, and the room-allocation diagram.
- `tools/`: evidence validation and publication gates.

The authors preserve the original frontend in `snapshot/index.html`. Compare it with `snapshot/index_thumbnail_variant.html` to inspect the thumbnail change. `environment.json` records the research execution environment. `requirements.txt` lists the Python package needed by these audit runners.

## Repeat deterministic checks

Use Python 3.12, Pillow 12.3.0, and Node 24. Run from the repository root:

```sh
python -m pip install -r requirements.txt
python scripts/audit.py
node scripts/test_generator.cjs
node scripts/test_extended.cjs
python scripts/figure_rooms.py
python tools/validate_evidence.py
python tools/verify_publication.py
```

The scripts write results in place. A different runtime can change environment metadata; inspect such changes before comparing hashes. The publication verifier enforces the release manifest and will reject modified results until a maintainer reviews and records them for a new release.

## Repeat backend and browser checks

Start Docker and build the isolated backend:

```sh
docker build -t galeri-web:latest -f snapshot/backend.Dockerfile .
docker pull mysql:8.0
python scripts/backend_integration.py
```

The runner creates temporary credentials and disposable containers. It reads `snapshot/collection.sql`, creates test administration data, and removes its resources after execution. It does not read the application's local environment file. The recorded PHP build lacks EXIF support, so its upload tests do not establish EXIF-orientation handling.

For integrated browser checks, set `RUN_BROWSER=1`, `NODE_BINARY` to your Node executable, `PLAYWRIGHT_MODULE` to an installed Playwright module, and `CHROME_PATH` to your Chrome executable before running the backend runner. Use `AUDIT_HEADLESS=0` for the browser-owned pointer-lock experiment. Inspect `scripts/browser_controls.cjs` for the separate fixture-based controls, which inject pointer-lock state. The recorded live browser experiment uses trusted automation input and acquires pointer lock through Chrome.

To repeat the Linux generator comparison:

```sh
docker pull node:24-alpine
python scripts/check_linux.py
```

Docker tags can resolve to newer builds. Compare your image IDs and runtime versions with the recorded results.

## Publication policy

`PUBLICATION_POLICY.json` lists the exact files permitted in this release. `MANIFEST.json` records their SHA-256 hashes. The verifier checks the working tree, Git history, file signatures, and an optional release ZIP. It rejects Office documents, manuscript/editorial filenames, credentials, symlinks, and nested archives. Ignore rules provide an additional local guard.

To create an archive outside the repository:

```sh
python tools/package_release.py /absolute/path/9project-gallery-reproducibility-v1.0.0.zip
python tools/verify_publication.py --archive /absolute/path/9project-gallery-reproducibility-v1.0.0.zip
```

The packager reads only the explicit allowlist. It stops if the content or history fails validation.

## Reuse and citation

The authors license their original code under MIT. Read `RIGHTS.md` for artwork/audio distribution permissions and `licenses/` for third-party notices. Use `CITATION.cff` and identify release `v1.0.0` when citing this package:

https://github.com/adnanzulkarnain/9project-gallery-reproducibility/releases/tag/v1.0.0
