---
name: tgravity-work-profile
description: TGravity Work 使用者信息卡 Skill。用于第一次使用时确认“我该怎么称呼你”、设置称呼、更新称呼、读取本机员工信息卡、为日报标题和默认决策对象提供 display_name。触发方式：我该怎么称呼你、以后叫我、设置称呼、更新称呼、使用者信息卡、员工信息卡、保存称呼。
---

# TGravity Work Profile

你只负责本机使用者称呼和最低必要信息卡。

## 原则

- 使用者信息卡是本地配置，不是业务资产。
- 不设置 `tgravity_asset: true`，不默认进入资产导出。
- 不追问手机号、身份证、微信、邮箱、私人账号、家庭住址等无关隐私。
- 默认决策对象是 `璐璐`，用户明确指定其他判断人时以用户为准。

## 启动流程

如果当前对话没有称呼，且找不到 `tgravity-work-data/profile/current-user.md`，只问：

```text
我该怎么称呼你？
```

用户回答后，本轮立即使用该称呼。

如果用户没有明确说“保存”“以后都叫我”“确认保存称呼”，不要写入本地。

保存前提示：

```text
我会把这个称呼保存到 `tgravity-work-data/profile/current-user.md`，只用于日报标题、提交人和默认决策对象。确认保存吗？
```

只有用户回复“确认保存”后才写入。

## 保存路径

```text
tgravity-work-data/profile/current-user.md
```

使用模板：

```text
assets/templates/user-profile.md
```

## 字段

最低字段：

```text
display_name:
default_decision_owner: 璐璐
```

可选字段：

```text
role:
department:
notes:
```

缺可选字段时不追问。

## 调用口径

日报标题使用：

```text
# {{display_name}}的工作日报
```

默认决策升级写：

```text
需要璐璐判断
```

不要声称 Agent 程序启动时一定会自动弹出称呼问题。只能在用户第一次触发 TGravity Work 任一入口时执行称呼初始化。
