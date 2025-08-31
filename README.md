# glb2stl

FastAPI service to convert **GLB (non-Draco)** models to **STL**, with optional axis & unit normalization and light mesh repair. Built with a modern Python packaging setup (`pyproject.toml`, `hatchling`), a clean `src/` layout, health checks, and structured logging.

---

## Table of contents

- [Features](#features)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Setup](#setup)

  - [Create venv](#create-venv)
  - [Install (editable)](#install-editable)
  - [Run the API](#run-the-api)

- [Configuration](#configuration)
- [API](#api)

  - [Health](#health)
  - [Preflight](#preflight)
  - [Convert to STL](#convert-to-stl)

- [Examples](#examples)

  - [curl](#curl)
  - [Python client](#python-client)

- [Viewing STL](#viewing-stl)
- [Logging](#logging)
- [Testing, Linting, Typing](#testing-linting-typing)
- [Packaging & Versioning](#packaging--versioning)
- [Docker](#docker)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

- ✅ **GLB → STL** conversion (for **non-Draco** GLB files)
- ✅ **Preflight**: detect **Draco**, report vertices/triangles, bounds, watertightness
- ✅ **Axis normalization**: default **Y‑up → Z‑up**
- ✅ **Units normalization**: default **meters → millimeters**
- ✅ **Light mesh repair**: remove unreferenced vertices/duplicate faces, fix normals
- ✅ Optional **decimation** (quadratic) to reduce triangles
- ✅ **Health** endpoints (liveness/readiness)
- ✅ **Structured logging** (console dev, JSON prod)
- ✅ Modern **src/** layout + `pyproject.toml`

---

## Architecture

```
repo-root/
├─ pyproject.toml             # packaging & tooling config
├─ .env.example               # example env vars
├─ src/
│  └─ glb2stl/
│     ├─ __about__.py         # __version__ = "0.1.0" (hatch reads version here)
│     ├─ __init__.py
│     ├─ __main__.py          # console entrypoint: `glb2stl-api`
│     ├─ app.py               # FastAPI app (mounts routers, middleware)
│     ├─ config.py            # Pydantic settings (env-driven)
│     ├─ logging_config.py    # logging (console/JSON)
│     ├─ versioning.py        # safe version access
│     ├─ schemas.py           # pydantic models
│     ├─ routers/
│     │  ├─ health.py         # /health/liveness, /health/readiness
│     │  └─ convert.py        # /api/v1/convert/preflight, /api/v1/convert/stl
│     └─ services/
│        └─ glb.py            # GLB loader, Draco detect, normalize, repair
└─ tests/
   └─ test_health.py          # minimal sanity tests
```

---

## Requirements

- **Python 3.11+**
- macOS/Linux/Windows
- Optional (macOS viewers): Homebrew for MeshLab/Blender/FreeCAD

---

## Setup

### Create venv

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

> In VS Code, select interpreter: `./.venv/bin/python`.

### Install (editable)

> **zsh users**: **quote** extras or zsh will expand `[]`.

```bash
pip install -e '.[dev]'
```

Sanity import:

```bash
python - <<'PY'
import glb2stl, glb2stl.app, sys
print("OK:", glb2stl.app.app.title)
print("Python:", sys.executable)
PY
```

### Run the API

Option A (module):

```bash
python -m uvicorn glb2stl.app:app --reload --port 8000
```

Option B (console script):

```bash
glb2stl-api
```

Open:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Redoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Configuration

Set via environment variables (or `.env` at repo root):

| Variable                    | Default    | Description                  |
| --------------------------- | ---------- | ---------------------------- |
| `API_PREFIX`                | `/api/v1`  | Base path for API routes     |
| `SERVICE_NAME`              | `glb2stl`  | Name for logs/metadata       |
| `ENV`                       | `dev`      | `dev` or `prod`              |
| `LOG_FORMAT`                | `console`  | `console` or `json`          |
| `LOG_LEVEL`                 | `INFO`     | `DEBUG`/`INFO`/`WARNING`/…   |
| `MAX_BYTES`                 | `52428800` | Max upload size (bytes)      |
| `CORS_ALLOW_ALL`            | `true`     | Allow all origins            |
| `ENFORCE_Z_UP`              | `true`     | Default Y‑up → Z‑up rotation |
| `SCALE_TO_MM`               | `true`     | Default meters → millimeters |
| `ALLOW_DECIMATE`            | `true`     | Enable decimation            |
| `MAX_FACES_BEFORE_DECIMATE` | `2000000`  | Guardrail for huge meshes    |

Copy starter:

```bash
cp .env.example .env
# edit as needed
```

---

## API

### Health

- **GET** `/health/liveness` → `{"status":"alive"}`
- **GET** `/health/readiness` → `{"status":"ready","version":"0.1.0"}`

### Preflight

**POST** `/api/v1/convert/preflight` (multipart)

- form field: `file` (the `.glb` file)
- returns JSON summary and **`has_draco`** flag

Example response:

```json
{
  "filename": "sample.glb",
  "has_draco": false,
  "vertices": 40445,
  "triangles": 50468,
  "bounds_m_min": [-0.48, -0.5, -0.42],
  "bounds_m_max": [0.48, 0.5, 0.41],
  "watertight": false,
  "notes": ["glTF units: meters; default export converts to mm, Z-up."]
}
```

> If `has_draco` is `true`, this service (by design) won’t convert that file.

### Convert to STL

**POST** `/api/v1/convert/stl` (multipart)

Query params:

- `z_up` (bool, default `true`): rotate Y‑up → Z‑up
- `to_mm` (bool, default `true`): meters → millimeters
- `repair` (bool, default `true`): light mesh fixes
- `decimate` (float 0..0.99, default `0.0`): reduce faces (e.g., `0.5` ≈ 50%)

Returns: **`model/stl`** stream (as attachment)

---

## Examples

### curl

```bash
# Preflight
curl -F "file=@/Users/nayanshah/Desktop/FormVerse/assets/sample.glb" \
  http://127.0.0.1:8000/api/v1/convert/preflight

# Convert to STL
curl -F "file=@/Users/nayanshah/Desktop/FormVerse/assets/sample.glb" \
  "http://127.0.0.1:8000/api/v1/convert/stl?z_up=true&to_mm=true&repair=true&decimate=0.0" \
  -o output.stl
```

> If your path has spaces, quote it like `@".../my file.glb"`.

### Python client

```python
import requests, pathlib

glb = pathlib.Path("/Users/nayanshah/Desktop/FormVerse/assets/sample.glb")

# preflight
r = requests.post(
    "http://127.0.0.1:8000/api/v1/convert/preflight",
    files={"file": glb.open("rb")}
)
print("preflight:", r.status_code, r.json())

# convert
r = requests.post(
    "http://127.0.0.1:8000/api/v1/convert/stl",
    params={"z_up": True, "to_mm": True, "repair": True, "decimate": 0.0},
    files={"file": glb.open("rb")}
)
pathlib.Path("output.stl").write_bytes(r.content)
print("wrote output.stl")
```

---

## Viewing STL

- **MeshLab** (free): `brew install --cask meshlab`
- **Blender** (free): `brew install --cask blender` → _File → Import → STL…_
- **FreeCAD** (free): `brew install --cask freecad`
- **Python quick view (Open3D)**:

```bash
pip install open3d
python - <<'PY'
import open3d as o3d
m = o3d.io.read_triangle_mesh("output.stl")
m.compute_vertex_normals()
o3d.visualization.draw_geometries([m])
PY
```

---

## Logging

- Default **console** format; set `LOG_FORMAT=json` for structured JSON logs.
- uvicorn access/error logs unified with app logs.
- Startup/shutdown events log service metadata.

---

## Testing, Linting, Typing

```bash
pytest -q                 # tests
ruff check .              # lint
ruff format .             # format
mypy src/glb2stl          # typing
```

(Optional) pre-commit:

```bash
pre-commit install
pre-commit run --all-files
```

---

## Packaging & Versioning

- Build backend: **hatchling**
- Version source: file-based at `src/glb2stl/__about__.py` (e.g., `__version__ = "0.1.0"`)

Build a wheel (optional):

```bash
pip install build
python -m build
```

---

## Docker

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir -e .[dev]
COPY src ./src
EXPOSE 8000
CMD ["uvicorn", "glb2stl.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build & run:

```bash
docker build -t glb2stl:local .
docker run --rm -p 8000:8000 glb2stl:local
```

---

## Troubleshooting

**`ModuleNotFoundError: glb2stl` when starting uvicorn**

- Ensure you installed the package (editable): `pip install -e '.[dev]'`.
- Make sure the shell uses your venv: `which python` → ends with `/.venv/bin/python`.
- Fallback: `python -m uvicorn --app-dir src glb2stl.app:app --reload`.

**`zsh: no matches found: .[dev]`**

- Quote extras: `pip install -e '.[dev]'`.

**`413 Request Entity Too Large`**

- Increase `MAX_BYTES` in `.env` (e.g., `104857600` for 100MB), restart the app.

**Preflight says `has_draco: true`**

- This service path **doesn’t** decode Draco. Re‑export GLB without Draco, or add a Draco-capable pipeline separately.

**Orientation/units look off in viewer**

- Try toggling query params: `z_up=false` and/or `to_mm=false` during convert.

---

## License

MIT © Nayan Shah
