from datetime import datetime
from zoneinfo import ZoneInfo
import os

from scrapling.fetchers import Fetcher


DEFAULT_THS_URL = "https://q.10jqka.com.cn/"


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


def _parse_table(page) -> tuple[list[str], list[dict]]:
    rows = page.css("table tr")

    header = []
    records = []

    for row in rows:
        cells = [_cell_text(cell) for cell in row.css("th, td")]
        cells = [x for x in cells if x != ""]

        if not cells:
            continue

        # 第一行通常是表头
        if not header and ("代码" in cells and "名称" in cells):
            header = [_normalize_header(x) for x in cells]
            continue

        # 没拿到表头前，不解析数据
        if not header:
            continue

        # 数据列数量不足，跳过
        if len(cells) < min(5, len(header)):
            continue

        raw_record = {}
        for idx, title in enumerate(header):
            if idx < len(cells):
                raw_record[title] = cells[idx]
            else:
                raw_record[title] = ""

        record = {
            "raw": raw_record
        }

        for cn_key, value in raw_record.items():
            en_key = FIELD_MAP.get(cn_key, cn_key)
            record[en_key] = value

        # 强制保留核心字段
        if record.get("code") and record.get("name"):
            records.append(record)

    return header, records


def scrape_ths_a_stock(url: str | None = None) -> dict:
    target_url = url or os.environ.get("THS_URL") or DEFAULT_THS_URL
    fetched_at = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()

    result = {
        "ok": False,
        "source": "ths_a_stock",
        "url": target_url,
        "fetched_at": fetched_at,
        "status": None,
        "title": "",
        "headers": [],
        "count": 0,
        "stocks": [],
        "error": "",
        "note": "正式结构化版：解析同花顺 A 股行情中心当前页面表格。当前只抓页面直接返回的表格，不包含翻页全量。",
    }

    try:
        page = Fetcher.get(
            target_url,
            impersonate="chrome",
            stealthy_headers=True,
            timeout=30,
            retries=2,
        )
    except Exception as exc:
        result["error"] = f"Fetcher.get failed: {type(exc).__name__}: {exc}"
        return result

    result["status"] = getattr(page, "status", None)

    try:
        title_parts = page.css("title::text").getall()
        result["title"] = _clean_text(" ".join(title_parts))
    except Exception:
        result["title"] = ""

    try:
        headers, stocks = _parse_table(page)
        result["headers"] = headers
        result["stocks"] = stocks
        result["count"] = len(stocks)
    except Exception as exc:
        result["error"] = f"parse table failed: {type(exc).__name__}: {exc}"
        return result

    result["ok"] = bool(result["status"] and int(result["status"]) < 400 and result["count"] > 0)
    return result
