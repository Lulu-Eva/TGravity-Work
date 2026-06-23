# Perplexity Config

## API Key 边界

Perplexity API Key 是本机密钥，不是 Skill 资产。

不得写入：

- GitHub 仓库。
- `SKILL.md`。
- README。
- 资产卡。
- 导出包。
- 示例命令。

默认保存位置：

```text
~/.config/tgravity-work-search/config.json
```

该文件只保存在员工本机。

## 初始化流程

1. 先执行：

```bash
python3 scripts/perplexity_search.py --status
```

2. 如果没有 key，向用户索要 Perplexity API Key。
3. 用户提供后执行：

```bash
python3 scripts/perplexity_search.py --init
```

4. 初始化完成后再次执行 `--status`。

## 临时环境变量

如果用户不想保存 key，也可以让用户在当前 shell 设置：

```bash
export PERPLEXITY_API_KEY="..."
```

环境变量优先级高于本机配置文件。

## 失败处理

| 情况 | 处理 |
|---|---|
| 401 / 403 | 说明 key 无效、过期或权限不足，请用户重新提供 |
| 429 | 说明触发限流或额度不足，停止重试 |
| 网络超时 | 提醒稍后重试，不要编造搜索结果 |
| 返回结果很少 | 调整查询词，不要强行下结论 |

## 常用参数

| 需求 | 参数 |
|---|---|
| 只看近期 | `--recency day/week/month/year` |
| 限定域名 | `--domain example.com` |
| 排除域名 | `--exclude-domain reddit.com` |
| 限定语言 | `--language zh` |
| 限定国家 | `--country CN` |
| 控制正文抽取量 | `--context-size low/medium/high` |

## 搜索结果保存

默认只输出结果，不保存。

用户明确要求保存时，保存到运行项目：

```text
tgravity-work-search-data/
```

不要保存到 Skill 仓库本体。
