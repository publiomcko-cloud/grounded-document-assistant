from pathlib import Path


_PACKAGE_DIR = Path(__file__).resolve().parent
_BACKEND_APP_DIR = _PACKAGE_DIR.parent / "backend" / "app"

if _BACKEND_APP_DIR.is_dir():
    __path__.append(str(_BACKEND_APP_DIR))
