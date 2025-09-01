from __future__ import annotations

import io
import json
import struct

import numpy as np
import trimesh

DRACO_EXT = "KHR_draco_mesh_compression"
GLB_MAGIC = 0x46546C67  # b"glTF"
CHUNK_JSON = 0x4E4F534A  # b"JSON"


class DracoDetected(Exception):
    """Raised when Draco is present (non-Draco path only)."""


def _extract_glb_json_bytes(data: bytes) -> bytes:
    if len(data) < 12:
        raise ValueError("File too small to be a GLB")
    magic, version, total_len = struct.unpack_from("<III", data, 0)
    if magic != GLB_MAGIC:
        raise ValueError("Not a GLB (bad magic)")
    offset = 12
    while offset + 8 <= len(data):
        chunk_len, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        if offset + chunk_len > len(data):
            raise ValueError("Corrupted GLB (chunk overruns file)")
        chunk_bytes = data[offset : offset + chunk_len]
        offset += chunk_len
        if chunk_type == CHUNK_JSON:
            return chunk_bytes
    raise ValueError("GLB JSON chunk not found")


def detect_draco_from_bytes(data: bytes) -> bool:
    try:
        doc = json.loads(_extract_glb_json_bytes(data).decode("utf-8"))
    except Exception:
        try:
            doc = json.loads(data.decode("utf-8"))  # .gltf JSON
        except Exception:
            return DRACO_EXT.encode("utf-8") in data  # fallback scan
    if DRACO_EXT in (doc.get("extensionsUsed") or []):
        return True
    if DRACO_EXT in (doc.get("extensionsRequired") or []):
        return True
    for mesh in doc.get("meshes") or []:
        for prim in mesh.get("primitives") or []:
            if DRACO_EXT in (prim.get("extensions") or {}):
                return True
    return False


def load_glb_to_mesh(glb_bytes: bytes) -> trimesh.Trimesh:
    if detect_draco_from_bytes(glb_bytes):
        raise DracoDetected(
            "GLB uses Draco (KHR_draco_mesh_compression). Provide uncompressed GLB."
        )
    scene_or_mesh = trimesh.load(io.BytesIO(glb_bytes), file_type="glb")
    mesh = scene_or_mesh.to_mesh() if isinstance(scene_or_mesh, trimesh.Scene) else scene_or_mesh
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("Input did not resolve to a triangle mesh.")
    return mesh


def orient_and_scale(mesh: trimesh.Trimesh, z_up: bool, to_mm: bool) -> None:
    if z_up:
        R = trimesh.transformations.rotation_matrix(np.deg2rad(-90.0), [1.0, 0.0, 0.0])
        mesh.apply_transform(R)
    if to_mm:
        mesh.apply_scale(1000.0)


def quick_repair(mesh: trimesh.Trimesh) -> None:
    mesh.remove_unreferenced_vertices()
    mesh.remove_duplicate_faces()
    mesh.fix_normals()
