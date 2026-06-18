from datetime import datetime
from zoneinfo import ZoneInfo
import os

from drive_io import save_json_to_drive, read_json_from_drive
from ths_scraper import scrape_ths_a_stock_all


def main():
    drive_dir = os.environ.get(
        "A_STOCK_DRIVE_DIR",
        "/content/drive/MyDrive/a_stock_data"
    )

    now = datetime.now(ZoneInfo("Asia/Shanghai"))

    data = scrape_ths_a_stock_all()

    filename = f"ths_a_stock_all_{now.strftime('%Y%m%d_%H%M%S')}.json"

    saved_path = save_json_to_drive(drive_dir, filename, data)

    loaded = read_json_from_drive(saved_path)

    print("====== 读取验证成功 ======")
    print("保存文件:", saved_path)
    print("抓取状态 ok:", loaded.get("ok"))
    print("最大页数:", loaded.get("max_pages"))
    print("实际请求页数:", loaded.get("pages_fetched"))
    print("有数据页数:", loaded.get("pages_with_data"))
    print("股票数量:", loaded.get("count"))
    print("错误数量:", len(loaded.get("errors", [])))

    stocks = loaded.get("stocks", [])
    if stocks:
        print("第一条股票:")
        first = stocks[0]
        print("代码:", first.get("code"))
        print("名称:", first.get("name"))
        print("现价:", first.get("price"))
        print("涨跌幅%:", first.get("change_percent"))
        print("成交额:", first.get("amount"))

        print("最后一条股票:")
        last = stocks[-1]
        print("代码:", last.get("code"))
        print("名称:", last.get("name"))
        print("页码:", last.get("page"))
    else:
        print("没有解析到股票数据")

    print("====== JSON 已写入 Google Drive ======")


if __name__ == "__main__":
    main()
