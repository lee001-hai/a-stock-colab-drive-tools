from datetime import datetime
from zoneinfo import ZoneInfo
import os

from drive_io import save_json_to_drive, read_json_from_drive


def main():
    drive_dir = os.environ.get(
        "A_STOCK_DRIVE_DIR",
        "/content/drive/MyDrive/a_stock_data"
    )

    now = datetime.now(ZoneInfo("Asia/Shanghai"))

    data = {
        "source": "colab",
        "storage": "google_drive",
        "project": "a_stock_drive_pipeline",
        "status": "ok",
        "message": "Colab 运行 GitHub 代码，并成功把 JSON 保存到 Google Drive",
        "created_at": now.isoformat(),
        "items": [
            {"name": "涨停统计", "value": 123},
            {"name": "跌停统计", "value": 8},
            {"name": "炸板统计", "value": 21}
        ]
    }

    filename = f"colab_drive_test_{now.strftime('%Y%m%d_%H%M%S')}.json"

    saved_path = save_json_to_drive(drive_dir, filename, data)

    loaded = read_json_from_drive(saved_path)

    print("====== 读取验证成功 ======")
    print(loaded)


if __name__ == "__main__":
    main()
