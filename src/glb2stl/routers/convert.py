from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import StreamingResponse, JSONResponse
from ..schemas import PreflightInfo, ErrorResponse
from ..services.glb import detect_draco_from_bytes, load_glb_to_mesh, orient_and_scale, quick_repair, DracoDetected
from ..config import settings
from ..logging_config import get_logger
import io

router = APIRouter(prefix="/convert", tags=["convert"])
log = get_logger(__name__)

@router.post("/preflight", response_model=PreflightInfo, responses={400: {"model": ErrorResponse}})
async def preflight(file: UploadFile = File(...)):
    data = await file.read()
    if len(data) > settings.MAX_BYTES:
        return JSONResponse({"error": f"File too large (> {settings.MAX_BYTES} bytes)."}, status_code=400)

    has_draco = detect_draco_from_bytes(data)
    if has_draco:
        return PreflightInfo(
            filename=file.filename,
            has_draco=True,
            vertices=0,
            triangles=0,
            bounds_m_min=[0,0,0],
            bounds_m_max=[0,0,0],
            watertight=False,
            notes=["GLB uses Draco. Provide uncompressed GLB, or use a Draco-capable path."]
        )

    try:
        mesh = load_glb_to_mesh(data)
    except Exception as e:
        return JSONResponse({"error": f"Failed to parse GLB: {e}"}, status_code=400)

    bbox = mesh.bounds
    return PreflightInfo(
        filename=file.filename,
        has_draco=False,
        vertices=int(mesh.vertices.shape[0]),
        triangles=int(mesh.faces.shape[0]),
        bounds_m_min=bbox[0].tolist(),
        bounds_m_max=bbox[1].tolist(),
        watertight=bool(mesh.is_watertight),
        notes=["glTF units: meters; default export converts to mm, Z-up."]
    )

@router.post("/stl", responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def convert_to_stl(
    file: UploadFile = File(..., description="Upload a .glb file (non-Draco)"),
    z_up: bool = Query(True, description="Rotate Y-up → Z-up"),
    to_mm: bool = Query(True, description="Scale meters → millimeters"),
    repair: bool = Query(True, description="Run light mesh repairs"),
    decimate: float = Query(0.0, ge=0.0, le=0.99, description="Fraction to reduce faces (0.25 = reduce 25%)"),
):
    data = await file.read()
    if len(data) > settings.MAX_BYTES:
        return JSONResponse({"error": f"File too large (> {settings.MAX_BYTES} bytes)."}, status_code=400)

    if detect_draco_from_bytes(data):
        return JSONResponse({"error": "GLB uses Draco; this endpoint requires uncompressed GLB."}, status_code=400)

    try:
        mesh = load_glb_to_mesh(data)
        face_count_before = int(mesh.faces.shape[0])

        if settings.ALLOW_DECIMATE and decimate > 0:
            target = max(1000, int(face_count_before * (1.0 - decimate)))
            mesh = mesh.simplify_quadratic_decimation(target)

        orient_and_scale(mesh, z_up=z_up, to_mm=to_mm)
        if repair:
            quick_repair(mesh)

        buf = io.BytesIO()
        mesh.export(buf, file_type="stl")
        buf.seek(0)
        out_name = file.filename.rsplit(".", 1)[0] + ".stl"

        log.info("converted_to_stl",
                 extra={"triangles_before": face_count_before,
                        "triangles_after": int(mesh.faces.shape[0]),
                        "z_up": z_up, "to_mm": to_mm, "repair": repair, "decimate": decimate})

        return StreamingResponse(
            buf,
            media_type="model/stl",
            headers={"Content-Disposition": f'attachment; filename="{out_name}"'}
        )
    except DracoDetected as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        log.exception("conversion_failed")
        return JSONResponse({"error": f"Conversion failed: {e}"}, status_code=500)
