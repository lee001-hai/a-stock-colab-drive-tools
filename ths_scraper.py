from datetime import datetime
from zoneinfo import ZoneInfo
import os
from urllib.parse import urljoin

from scrapling.fetchers import Fetcher


DEFAULT_THS_URL = "https://q.10jqka.com.cn/"


def _clean_text(text: str) -> str:
    return " ".join(str(text or "").split())


def _texts(elements) -> list[str]:
    values = []
    for el in elements:
        try:
            txt = _clean_text(el.get_all_text())
        except Exception:
            txt = _clean_text(getattr(el, "text", ""))
        if txt:
            values.append(txt)
    return values


def scrape_ths_probe(url: str | None = None, max_rows: int = 30) -> dict:
    """
    同花顺 Scrapling 探测版。

    目标不是一次性把所有 A 股数据抓全，而是先验证：
    1. Colab 能安装 Scrapling
    2. Colab 能访问同花顺页面
    3. 能解析页面标题、链接、表格
    4. 能把结果保存到 Google Drive

    后面确认页面结构后，再把这里改成正式字段解析。
    """
    target_url = url or os.environ.get("THS_URL") or DEFAULT_THS_URL
    fetched_at = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()

    result = {
        "ok": False,
        "source": "ths_scrapling_probe",
        "url": target_url,
        "fetched_at": fetched_at,
        "status": None,
        "title": "",
        "table_rows_count": 0,
        "table_rows_sample": [],
        "links_sample": [],
        "error": "",
        "note": "这是 Scrapling 探测版；先确认能抓到页面，再做正式 A 股字段解析。",
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

    # 抽取链接样本，帮助我们判断页面里有哪些可继续抓的 A 股入口
    try:
        links = []
        for a in page.css("a")[:50]:
            text = _clean_text(a.get_all_text())
            href = a.attrib.get("href", "") if hasattr(a, "attrib") else ""
            if href:
                links.append({
                    "text": text,
                    "href": urljoin(target_url, href),
                })
        result["links_sample"] = links[:20]
    except Exception as exc:
        result["links_error"] = f"{type(exc).__name__}: {exc}"

    # 抽取 HTML 表格样本。如果这里为空，说明页面可能靠 JS/XHR 加载数据。
    try:
        rows = page.css("table tr")
        result["table_rows_count"] = len(rows)

        samples = []
        for row in rows[:max_rows]:
            cells = []
            for cell in row.css("th, td"):
                txt = _clean_text(cell.get_all_text())
                if txt:
                    cells.append(txt)
            if cells:
                samples.append(cells)

        result["table_rows_sample"] = samples
    except Exception as exc:
        result["table_error"] = f"{type(exc).__name__}: {exc}"

    result["ok"] = bool(result["status"] and int(result["status"]) < 400)
    return result
