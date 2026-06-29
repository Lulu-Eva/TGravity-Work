# Folder Type Templates

Use these templates only after auditing the folder. Do not force an unknown project into a template.

## business

Use for company, client, commercial, partnership, or operating folders.

```text
00-系统管理
01-战略与定位
02-业务资料
03-客户与合作
04-合同与合规
05-交付与复盘
06-资产与工具
99-归档
```

## content

Use for articles, short videos, social media, courses, podcasts, newsletters, or creator content.

```text
00-系统管理
01-选题与定位
02-素材库
03-草稿
04-发布稿
05-数据反馈
99-归档
```

## software_or_skill

Use for code repositories, agent skills, plugins, automation scripts, or software products.

```text
00-系统管理
01-产品设计
02-开发文档
03-测试验证
04-发布材料
05-用户反馈
99-归档
```

For installable Skill repositories, keep the installable package separate from development docs.

```text
project-root/
├── skill-or-plugin-package/
└── 开发文档/
```

## event_or_delivery

Use for workshops, offline events, client delivery, training, filming, or post-event material.

```text
00-系统管理
01-策划方案
02-嘉宾与客户
03-执行物料
04-现场素材
05-交付成果
06-复盘
99-归档
```

## personal_learning

Use for personal study, research notes, reading, courses, or long-term learning tracks.

```text
00-系统管理
01-学习目标
02-资料与课程
03-笔记
04-输出作品
05-复盘
99-归档
```

## mixed

Use when the folder combines business, content, software, and delivery. Do not over-split immediately.

Start with:

```text
00-系统管理
01-核心判断
02-工作资料
03-交付成果
04-敏感与合规
99-归档
```

Then propose a second-pass split only after the user confirms the project boundary.

## unknown

Use no template. Output:

```text
当前无法判断项目类型。
已观察到的文件聚类：
需要用户确认的问题：
建议先不移动文件。
```
