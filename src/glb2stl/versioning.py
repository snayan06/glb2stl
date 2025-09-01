from importlib.metadata import PackageNotFoundError, version


def get_version() -> str:
    try:
        return version("glb2stl")
    except PackageNotFoundError:
        return "0.0.0.dev0"
