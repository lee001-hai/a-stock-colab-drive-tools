这是第四版：同花顺 A 股行情分页全量抓取版。

它会：
1. Colab 从 GitHub 拉代码
2. 安装 Scrapling
3. 按页抓取同花顺 A 股行情 ajax 页面
4. 自动解析字段
5. 自动去重
6. 保存 JSON 到 Google Drive

默认配置：
THS_MAX_PAGES = 300
THS_SLEEP_SECONDS = 1.2

输出文件名类似：
ths_a_stock_all_20260618_101500.json

注意：
这个版本是分页全量抓取版，但仍然依赖同花顺公开页面结构。
如果网站限制访问、改页面结构、返回空页，需要继续调整。
