# Workflow

## 输入

用户通常提供：

- 发票下载目录。
- 报销日期，例如 `2026-06-21`。
- Excel 模板路径，可选。
- 输出目录，可选。
- 额外跨表查重目录，可选。
- 公司抬头，可选，默认 `深圳璐途文化科技有限公司`。

如果缺少发票目录，只问一个问题：

```text
请给我这次要整理的发票下载目录路径。
```

如果缺少报销日期，只问一个问题：

```text
请确认这次报销日期，格式例如 2026-06-21。
```

不得默认使用当天日期。

## 标准步骤

1. 递归扫描发票目录。
2. 对同名 PDF/OFD 成对文件，优先 PDF。
3. 对 PDF 先用 `pdfminer.six` 抽文本；无可抽取文本时列入识别失败，不启用 OCR 硬猜。
4. 普通电子发票走普通解析。
5. 铁路电子客票走铁路解析。
6. 过滤购买方不是公司抬头的发票；购买方字段缺失但全文出现公司抬头时，写入低置信待确认。
7. 按发票号码去重。
8. 写入 Excel。
9. 自动执行复查。
10. 输出报销表和复查报告。

## 推荐命令

```bash
python3 scripts/invoice_reimbursement.py run \
  --invoice-dir "<发票下载目录>" \
  --date-label "YYYY-MM-DD" \
  --output-dir "<输出目录>"
```

需要额外检查历史报销表目录时：

```bash
python3 scripts/invoice_reimbursement.py run \
  --invoice-dir "<发票下载目录>" \
  --date-label "YYYY-MM-DD" \
  --output-dir "<输出目录>" \
  --cross-check-dir "<历史报销表目录>"
```

有模板时：

```bash
python3 scripts/invoice_reimbursement.py run \
  --invoice-dir "<发票下载目录>" \
  --date-label "YYYY-MM-DD" \
  --template "<Excel模板路径>"
```

## 失败处理

- 没有找到 PDF：停止并说明目录中没有可处理发票。
- PDF 无可抽取文本：跳过该文件，加入识别失败清单；不要声称已经 OCR。
- 缺少 `pdfminer.six`：提示安装依赖，不要改用低置信 OCR 硬猜。
- 某张发票字段无法识别：跳过写入，加入复查报告。
- 购买方不是默认公司抬头：跳过写入，加入跳过统计。
- 跨表重复：报告用户，不自动删除。
