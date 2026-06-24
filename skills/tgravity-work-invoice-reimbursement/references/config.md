# Config

## 本机依赖

必需：

```bash
python3 -m pip install --user openpyxl pdfminer.six
```

检查：

```bash
python3 scripts/invoice_reimbursement.py check
```

## 默认配置

| 配置项 | 默认值 |
|---|---|
| 公司抬头 | `深圳璐途文化科技有限公司` |
| 输出字段 | 6 列固定字段 |
| 报销日期 | 必填，不默认当天 |
| 输出文件名 | `发票填写_YYYY-MM-DD报销.xlsx` |
| 工作表 | `发票汇总` |
| OFD | 不直接解析；同名 PDF 存在时跳过 OFD |
| 跨表查重 | 默认查输出目录和模板目录；可追加 `--cross-check-dir` |

## 隐私边界

- 不把真实发票放进 Skill 仓库。
- 不把公司税号、OCR 密钥、报销表提交到 GitHub。
- 默认本地 PDF 文本解析，只处理可抽取文本的 PDF。
- 扫描件、图片发票和原生 OFD 在第一版不可靠识别，必须列为待处理或识别失败。
- 如果未来接入云端 OCR，必须先确认上传边界和本机密钥配置。
