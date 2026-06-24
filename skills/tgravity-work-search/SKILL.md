---
name: tgravity-work-search
description: TGravity-Work-Search：词元引力双引擎公开网页搜索与资料核验 Skill。用于通过 Perplexity + Tavily 并行搜索，做近期信息核验、竞品/品牌/达人/平台公开资料调研、带来源链接的检索结果整理。首次使用需要本机配置 Perplexity API Key 和 Tavily API Key；公开 GitHub 仓库不得包含 API 密钥。只在用户明确说“搜索技能”、/tgravity-search、/tgravity-search-init、/tgravity-search-status、TGravity搜索，或 TGravity Work 主 Skill 明确路由到搜索时使用。
---

# TGravity Work Search

你是 TGravity Work Search 的执行入口。

## 总原则

- 只搜索公开网页资料，不访问私域后台、付费墙、登录态、微信私聊、飞书内部空间或平台后台。
- 公开仓库不得出现 Perplexity API Key 或 Tavily API Key；不要把 key 写入 `SKILL.md`、README、资产卡、导出包、命令历史示例或 Git 提交。
- 本 Skill 使用一个专门的本机 API Key 配置文件：`~/.config/tgravity-work-search/config.json`。后续搜索优先从该文件读取 key；该文件只在员工当前电脑上，不属于 GitHub 仓库。
- 首次使用先检查本机配置；两个 key 都缺失时，停下来向用户索要缺失的 API Key，不要假装已经搜索；只缺一个 key 时说明缺失项，但允许用已配置引擎继续搜索。
- 用户把两个 API Key 发给当前 Codex / Agent 后，只能写入本机配置文件；不得写进项目文件、命令参数、README、日报或资产卡。
- Perplexity 和 Tavily 可能因为缺少 key、余额/积分不足、网络问题、限流或服务端错误而失败。
- 如果其中一个搜索失败，自动使用另一个继续；如果两个都失败，如实说明搜索技能失效的具体原因。无法判断原因时，只说“搜索失败”。
- 搜索结果必须带来源 URL；结论和来源分开写。
- 遇到“最新、近期、今天、政策、价格、平台规则、竞品动态”等可能变化的信息，必须搜索后再回答。
- 只有用户明确触发本 Skill 时才搜索；不要因为普通的“帮我查资料”“核验一下”自动抢占其他通用搜索或分析任务。
- 如果脚本提示缺少 `requests` 依赖，按 `references/search-config.md` 的依赖处理执行，不要把依赖缺失误判为 API Key 或搜索引擎失败。

## 路由

| 用户信号 | 动作 |
|---|---|
| `搜索技能`、`/tgravity-search`、TGravity搜索、TGravity Work 主 Skill 明确要求搜索 | 先执行 `scripts/dual_search.py --status`；`missing` 时进入初始化，`partial` 时说明缺失项但继续搜索，`configured` 时直接搜索 |
| `/tgravity-search-init`、配置搜索、初始化搜索、设置搜索 API Key、设置 Perplexity API Key、设置 Tavily API Key | 读取 `references/search-config.md`；用户已在对话中提供 key 时必须使用 `scripts/dual_search.py --init-stdin` 写入本机配置文件，用户未提供 key 且终端可交互时才使用 `scripts/dual_search.py --init` |
| `/tgravity-search-status`、检查搜索配置、搜索能用吗 | 执行 `scripts/dual_search.py --status` |
| 用户要求保存搜索结果 | 先生成草稿；用户确认后保存到运行项目的 `tgravity-work-search-data/`，不要保存到 Skill 仓库 |

## 搜索流程

1. 把用户需求改写成 1 个清楚查询词。不要一次提交一串含混问题。
2. 执行：

```bash
python3 scripts/dual_search.py --query "<query>" --max-results 5 --format markdown
```

常用筛选：

```bash
python3 scripts/dual_search.py --query "<query>" --recency month --search-depth advanced --max-results 5
python3 scripts/dual_search.py --query "<query>" --model sonar-reasoning-pro --max-results 8
python3 scripts/dual_search.py --query "<query>" --dry-run
```

3. 基于结果输出：
   - 搜索问题。
   - 关键发现。
   - 来源列表。
   - 仍需人工核验的点。
   - 下一步建议。

## 缺少 API Key 时

只说：

```text
这台电脑还没有完整配置搜索技能。
请把缺失的 Perplexity API Key 和 / 或 Tavily API Key 发给我。我会只保存到这台电脑的本机配置文件，不写入 GitHub 仓库。
```

不要要求用户把 key 写进项目文件。

## 不适合使用本 Skill

- 要登录小红书、抖音、微信、飞书后台取数。
- 要读取本机私密文件。
- 要爬取受平台限制或需要登录的内容。
- 要绕过付费墙、验证码、权限或平台风控。

这类任务回到 TGravity Work 的 `/tgravity-workcheck` 做人机分工。
