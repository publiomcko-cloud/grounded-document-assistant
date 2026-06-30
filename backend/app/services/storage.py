import shutil
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()
storage_root = Path(settings.file_storage_path).resolve()


def ensure_storage_root() -> Path:
    storage_root.mkdir(parents=True, exist_ok=True)
    return storage_root


def write_private_file(relative_path: Path, content: bytes) -> Path:
    destination = (ensure_storage_root() / relative_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return destination


def read_private_text_file(path_value: str | Path | None) -> str | None:
    if not path_value:
        return None

    target = Path(path_value)
    if not target.exists():
        return None

    return target.read_text(encoding="utf-8", errors="replace")


def remove_directory_if_present(path_value: str | Path | None) -> None:
    if not path_value:
        return

    target = Path(path_value)
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
