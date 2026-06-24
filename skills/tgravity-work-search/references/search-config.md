# Search Config

## API Key 边界

TGravity Work Search 使用两个搜索引擎：

- Perplexity：负责综合推理和答案整合。
- Tavily：负责结构化网页来源和链接核验。

两个 API Key 都是本机密钥，不是 Skill 资产。

员工实际使用时可以很简单：第一次使用搜索技能，员工把 Perplexity API Key 和 Tavily API Key 发给当前这台电脑上的 Codex / Agent；Agent 只把它们写入本机配置文件。以后搜索时脚本自动读取，不需要员工重复发送。

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

该文件只保存在员工本机。GitHub 仓库、Skill 安装包、导出包都不包含这个文件。

文件内容形态：

```json
{
  "PERPLEXITY_API_KEY": "员工本机实际 key",
  "TAVILY_API_KEY": "员工本机实际 key"
}
```

不要把真实 key 写入文档示例、README 或命令行参数。

## 初始化流程

先检查状态：

```bash
python3 scripts/dual_search.py --status
```

如果缺少任一 key，向用户索要缺失项：

```text
这台电脑还没有完整配置搜索技能。
请把缺失的 Perplexity API Key 和 / 或 Tavily API Key 发给我。我只会保存到这台电脑的本机配置文件，不会写入 GitHub 仓库。
```

### 推荐：用户把 key 发给 Codex / Agent

如果用户已经在对话中提供 key，不要执行 `--init`，不要把 key 拼进 shell 命令，也不要用 `echo` / `printf` 把 key 写进命令历史。必须把 key 作为 stdin JSON 写给：

```bash
python3 scripts/dual_search.py --init-stdin
```

stdin 内容格式可以使用标准字段名：

```json
{
  "PERPLEXITY_API_KEY": "...",
  "TAVILY_API_KEY": "..."
}
```

也可以使用简写字段名：

```json
{
  "perplexity": "...",
  "tavily": "..."
}
```

写入后再次执行：

```bash
python3 scripts/dual_search.py --status
```

### 备用：用户自己在终端输入

如果用户不想把 key 发给 Agent，或者当前宿主不能安全传 stdin，让用户自己在本机终端执行：

```bash
python3 scripts/dual_search.py --init
```

脚本会要求用户粘贴 key，并写入同一个本机配置文件。完成后再次检查：

```bash
python3 scripts/dual_search.py --status
```

## 依赖检查

`/tgravity-search-status` 和初始化不依赖第三方库；真实搜索需要 Python `requests`。

如果执行搜索时提示：

```text
missing dependency: requests
```

先说明这是本机 Python 依赖缺失，不是 Perplexity 或 Tavily 搜索失败。得到用户确认后再安装：

```bash
python3 -m pip install --user requests
```

如果无法安装，停止搜索并说明“搜索技能因本机缺少 requests 依赖暂不可用”。

## 临时环境变量

如果用户不想保存 key，也可以让用户在当前 shell 设置：

```bash
export PERPLEXITY_API_KEY="..."
export TAVILY_API_KEY="..."
```

环境变量优先级高于本机配置文件。

## 失败处理

搜索时两个引擎并行运行。

| 情况 | 处理 |
|---|---|
| `--status` 返回 `configured` | 直接双引擎搜索 |
| `--status` 返回 `partial` | 退出码仍为 0；说明缺失项，但允许用已配置引擎继续搜索 |
| `--status` 返回 `missing` | 停止搜索，要求初始化 |
| Perplexity 失败、Tavily 成功 | 自动使用 Tavily 结果继续，并说明 Perplexity 失败原因 |
| Tavily 失败、Perplexity 成功 | 自动使用 Perplexity 结果继续，并说明 Tavily 失败原因 |
| 缺少 `requests` 依赖 | 说明本机依赖缺失，按“依赖检查”处理；不要说成 API Key、积分或网络问题 |
| 两个都失败，原因明确 | 如实说明是缺少 key、key 无效、额度/积分/账单不足、限流、网络超时或服务端错误 |
| 两个都失败，原因无法判断 | 只说“搜索失败”，不要编造原因 |

常见可判断原因：

- `missing_key`：没有配置对应 API Key。
- `auth`：key 无效、过期或权限不足。
- `billing`：可能没有余额、积分或账单额度。
- `rate_limit`：触发限流或额度限制。
- `timeout` / `network`：网络问题。
- `provider`：搜索服务端错误。
- `dependency`：本机缺少搜索脚本依赖。
- `unknown`：无法判断原因，只说搜索失败。

## 常用参数

| 需求 | 参数 |
|---|---|
| 检查配置 | `--status` |
| 初始化配置 | `--init` |
| stdin 安全初始化 | `--init-stdin` |
| 只看近期 | `--recency day/week/month/year` |
| 控制 Tavily 深度 | `--search-depth basic/advanced` |
| 控制 Tavily 来源数量 | `--max-results 5` |
| 指定 Perplexity 模型 | `--model sonar-pro` |

## 多维搜索拆分

单一事实查询只提交一个查询词。复杂研究不要压成一个泛查询。

如果用户的问题同时包含多个维度，例如“怎么样、适合谁、价格、竞品、渠道、风险、近期动态”，先拆成最多 4 个子查询。

每个子查询必须具备：

- 用途：这个子查询解决哪个判断。
- 时间范围：是否需要近期信息。
- 来源要求：官方、媒体、平台公开页面、评测、社区、财报或政策。

输出时先列出子查询，再合并结论。不要把不同来源维度混在同一段里。

## 搜索结果保存

默认只输出结果，不保存。

用户明确要求保存时，保存到运行项目：

```text
tgravity-work-search-data/
```

不要保存到 Skill 仓库本体。
