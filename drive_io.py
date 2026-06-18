import json
from pathlib import Path


def save_json_to_drive(drive_dir: str, filename: str, data: dict) -> str:
    folder = Path(drive_dir)
    folder.mkdir(parents=True, exist_ok=True)

    path = folder / filename
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"已保存到 Google Drive: {path}")
    return str(path)


def read_json_from_drive(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    return json.loads(text)
