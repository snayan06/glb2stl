from fastapi import APIRouter

from ..versioning import get_version

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/liveness")
def liveness():
    return {"status": "alive"}


@router.get("/readiness")
def readiness():
    try:
        import trimesh  # noqa: F401
    except Exception as e:
        return {"status": "not_ready", "reason": f"trimesh import failed: {e}"}
    return {"status": "ready", "version": get_version()}
