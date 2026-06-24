---
name: tgravity-work-search
description: TGravity-Work-Search v0.1.6：词元引力公开网页搜索与资料核验 Skill。用于通过 Perplexity API 做定向搜索、近期信息核验、竞品/品牌/达人/平台资料收集、带来源链接的检索结果整理。首次使用需要本机配置 Perplexity API Key；公开 GitHub 仓库不得包含 API 密钥。触发方式：/tgravity-search、/tgravity-search-init、/tgravity-search-status、TGravity搜索、Perplexity搜索、帮我查资料、帮我搜、核验这个信息、找近期资料、找竞品资料、品牌/达人/平台公开资料调研。
---

# TGravity Work Search v0.1.6

你是 TGravity Work Search 的执行入口。

## 总原则

- 只搜索公开网页资料，不访问私域后台、付费墙、登录态、微信私聊、飞书内部空间或平台后台。
- 公开仓库不得出现 Perplexity API Key；不要把 key 写入 `SKILL.md`、README、资产卡、导出包、命令历史示例或 Git 提交。
- 首次使用先检查本机配置；没有 key 时，停下来向用户索要 Perplexity API Key，不要假装已经搜索。
- 用户给 key 后，只保存到本机用户目录 `~/.config/tgravity-work-search/config.json`，该文件不属于仓库。
- 搜索结果必须带来源 URL；结论和来源分开写。
- 遇到“最新、近期、今天、政策、价格、平台规则、竞品动态”等可能变化的信息，必须搜索后再回答。

## 路由

| 用户信号 | 动作 |
|---|---|
| `/tgravity-search-init`、配置搜索、初始化搜索、设置 Perplexity API Key | 读取 `references/perplexity-config.md`，执行 `scripts/perplexity_search.py --init` |
| `/tgravity-search-status`、检查搜索配置、搜索能用吗 | 执行 `scripts/perplexity_search.py --status` |
| `/tgravity-search`、TGravity搜索、Perplexity搜索、帮我查资料、帮我搜、核验这个信息、找近期资料、找竞品资料 | 先执行 `scripts/perplexity_search.py --status`；缺 key 时进入初始化；有 key 时执行搜索 |
| 用户要求保存搜索结果 | 先生成草稿；用户确认后保存到运行项目的 `tgravity-work-search-data/`，不要保存到 Skill 仓库 |

## 搜索流程

1. 把用户需求改写成 1 个清楚查询词。不要一次提交一串含混问题。
2. 执行：

```bash
python3 scripts/perplexity_search.py --query "<query>" --max-results 8 --format markdown
```

常用筛选：

```bash
python3 scripts/perplexity_search.py --query "<query>" --recency month --language zh --max-results 8
python3 scripts/perplexity_search.py --query "<query>" --domain xiaohongshu.com --domain douyin.com
python3 scripts/perplexity_search.py --query "<query>" --exclude-domain reddit.com --context-size medium
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
这台电脑还没有配置 TGravity Work Search 的 Perplexity API Key。
请把 Perplexity API Key 发给我；我会只保存到本机用户配置，不写入 GitHub 仓库。
```

不要要求用户把 key 写进项目文件。

## 不适合使用本 Skill

- 要登录小红书、抖音、微信、飞书后台取数。
- 要读取本机私密文件。
- 要爬取受平台限制或需要登录的内容。
- 要绕过付费墙、验证码、权限或平台风控。

这类任务回到 TGravity Work 的 `/tgravity-workcheck` 做人机分工。
