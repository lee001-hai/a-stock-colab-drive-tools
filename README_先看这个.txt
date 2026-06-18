这是第三版：同花顺 A 股行情正式结构化解析版。

它会：
1. Colab 从 GitHub 拉代码
2. 安装 Scrapling
3. 抓取 https://q.10jqka.com.cn/
4. 解析 A 股表格字段
5. 保存 JSON 到 Google Drive

输出文件名类似：
ths_a_stock_20260618_100000.json

注意：
当前版本只解析同花顺页面直接返回的第一页表格。
不是全市场全量分页版。
跑通后再做分页全量。
