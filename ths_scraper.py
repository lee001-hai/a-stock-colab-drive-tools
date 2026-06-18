from datetime import datetime
from zoneinfo import ZoneInfo
import os
import time

from scrapling.fetchers import Fetcher


BASE_URL = "https://q.10jqka.com.cn/index/index/board/all/field/zdf/order/desc/page/{page}/ajax/1/"

DEFAULT_HEADERS = [
    "序号",
    "代码",
    "名称",
    "现价",
    "涨跌幅(%)",
    "涨跌",
    "涨速(%)",
    "换手(%)",
    "量比",
    "振幅(%)",
    "成交额",
    "流通股",
    "流通市值",
    "市盈率",
]

FIELD_MAP = {
    "序号": "rank",
    "代码": "code",
    "名称": "name",
    "现价": "price",
    "涨跌幅(%)": "change_percent",
    "涨跌幅（%）": "change_percent",
    "涨跌": "change_amount",
    "涨速(%)": "speed_percent",
    "涨速（%）": "speed_percent",
    "换手(%)": "turnover_percent",
    "换手（%）": "turnover_percent",
    "量比": "volume_ratio",
    "振幅(%)": "amplitude_percent",
    "振幅（%）": "amplitude_percent",
    "成交额": "amount",
    "流通股": "float_shares",
    "流通市值": "float_market_cap",
    "市盈率": "pe",
}


def _clean_text(text: str) -> str:
    return " ".join(str(text or "").replace("\xa0", " ").split())


def _cell_text(cell) -> str:
    try:
        return _clean_text(cell.get_all_text())
    except Exception:
        return _clean_text(getattr(cell, "text", ""))


def _normalize_header(value: str) -> str:
    return _clean_text(value).replace(" ", "")


def _looks_like_stock_row(cells: list[str]) -> bool:
    if len(cells) < 5:
        return False
    if not cells[0].isdigit():
        return False
    code = cells[1].strip()
    if not code.isdigit():
        return False
    return 5 <= len(code) <= 6


def _parse_page_table(page_obj) -> tuple[list[str], list[dict]]:
    rows = page_obj.css("table tr")
    headers = []
    records = []

    for row in rows:
        cells = [_cell_text(cell) for cell in row.css("th, td")]
        cells = [x for x in cells if x != ""]

        if not cells:
            continue

        if ("代码" in cells and "名称" in cells):
            headers = [_normalize_header(x) for x in cells]
            continue

        if not _looks_like_stock_row(cells):
            continue

        if not headers:
            headers = DEFAULT_HEADERS

        raw_record = {}
        for idx, title in enumerate(headers):
            raw_record[title] = cells[idx] if idx < len(cells) else ""

        record = {"raw": raw_record}
        for cn_key, value in raw_record.items():
            en_key = FIELD_MAP.get(cn_key, cn_key)
            record[en_key] = value

        if record.get("code") and record.get("name"):
            records.append(record)

    return headers or DEFAULT_HEADERS, records


def scrape_ths_a_stock_all(
    max_pages: int | None = None,
    sleep_seconds: float | None = None,
    stop_empty_pages: int = 3,
) -> dict:
    """
    同花顺 A 股行情中心分页抓取版。

    默认从 page/1/ajax/1/ 开始抓，按页递增。
    连续 stop_empty_pages 页没有股票数据就停止。
    """
    max_pages = int(max_pages or os.environ.get("THS_MAX_PAGES", "300"))
    sleep_seconds = float(sleep_seconds or os.environ.get("THS_SLEEP_SECONDS", "1.2"))

    fetched_at = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()

    result = {
        "ok": False,
        "source": "ths_a_stock_all_pages",
        "url_template": BASE_URL,
        "fetched_at": fetched_at,
        "max_pages": max_pages,
        "sleep_seconds": sleep_seconds,
        "pages_fetched": 0,
        "pages_with_data": 0,
        "headers": DEFAULT_HEADERS,
        "count": 0,
        "stocks": [],
        "errors": [],
        "note": "分页版：按同花顺 A 股行情中心 ajax 页码抓取。会自动去重，连续空页后停止。",
    }

    seen_codes = set()
    empty_streak = 0

    for page_no in range(1, max_pages + 1):
        url = BASE_URL.format(page=page_no)

        try:
            page_obj = Fetcher.get(
                url,
                impersonate="chrome",
                stealthy_headers=True,
                timeout=30,
                retries=2,
            )
        except Exception as exc:
            result["errors"].append({
                "page": page_no,
                "url": url,
                "error": f"{type(exc).__name__}: {exc}",
            })
            empty_streak += 1
            print(f"第 {page_no} 页失败: {type(exc).__name__}: {exc}")
            if empty_streak >= stop_empty_pages:
                break
            time.sleep(sleep_seconds)
            continue

        status = getattr(page_obj, "status", None)
        result["pages_fetched"] += 1

        if not status or int(status) >= 400:
            result["errors"].append({
                "page": page_no,
                "url": url,
                "status": status,
                "error": "bad http status",
            })
            empty_streak += 1
            print(f"第 {page_no} 页 HTTP异常: {status}")
            if empty_streak >= stop_empty_pages:
                break
            time.sleep(sleep_seconds)
            continue

        try:
            headers, records = _parse_page_table(page_obj)
            if headers:
                result["headers"] = headers
        except Exception as exc:
            result["errors"].append({
                "page": page_no,
                "url": url,
                "status": status,
                "error": f"parse failed: {type(exc).__name__}: {exc}",
            })
            records = []

        new_records = []
        for item in records:
            code = item.get("code")
            if not code or code in seen_codes:
                continue
            seen_codes.add(code)
            item["page"] = page_no
            new_records.append(item)

        if new_records:
            result["stocks"].extend(new_records)
            result["pages_with_data"] += 1
            empty_streak = 0
            print(f"第 {page_no} 页：新增 {len(new_records)} 条，累计 {len(result['stocks'])} 条")
        else:
            empty_streak += 1
            print(f"第 {page_no} 页：无新增数据，连续空页 {empty_streak}")

        if empty_streak >= stop_empty_pages:
            print(f"连续 {stop_empty_pages} 页无数据，停止。")
            break

        time.sleep(sleep_seconds)

    result["count"] = len(result["stocks"])
    result["ok"] = result["count"] > 0 and result["pages_with_data"] > 0
    return result
