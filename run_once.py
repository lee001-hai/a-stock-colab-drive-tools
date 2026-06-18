from datetime import datetime
from zoneinfo import ZoneInfo
import os

from drive_io import save_json_to_drive, read_json_from_drive
from ths_scraper import scrape_ths_probe


def main():
    drive_dir = os.environ.get(
        "A_STOCK_DRIVE_DIR",
        "/content/drive/MyDrive/a_stock_data"
    )

    now = datetime.now(ZoneInfo("Asia/Shanghai"))

    data = scrape_ths_probe()

    filename = f"ths_scrapling_probe_{now.strftime('%Y%m%d_%H%M%S')}.json"

    saved_path = save_json_to_drive(drive_dir, filename, data)

    loaded = read_json_from_drive(saved_path)

    print("====== 读取验证成功 ======")
    print("保存文件:", saved_path)
    print("抓取状态 ok:", loaded.get("ok"))
    print("HTTP状态:", loaded.get("status"))
    print("页面标题:", loaded.get("title"))
    print("表格行数:", loaded.get("table_rows_count"))
    print("链接样本数:", len(loaded.get("links_sample", [])))

    if loaded.get("error"):
        print("错误:", loaded.get("error"))

    print("====== JSON 已写入 Google Drive ======")


if __name__ == "__main__":
    main()
