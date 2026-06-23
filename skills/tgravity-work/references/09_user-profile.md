# TGravity User Profile

## 目标

建立当前使用者的本地称呼，让入门训练、日报标题、提交人字段和决策升级默认对象保持一致。

使用者信息卡是本地运行配置，不是业务资产。不得写入 `tgravity_asset: true`，不得默认进入 `/tgravity-export` 资产包。

## 什么时候读取

- 用户第一次触发 `/tgravity-onboarding`。
- 用户第一次触发 `/tgravity-daily`。
- 用户说“我该怎么称呼你”“以后叫我”“更新称呼”“员工信息卡”。
- 日报需要填写提交人，但当前对话没有明确姓名，也找不到 `tgravity-work-data/profile/current-user.md`。

## 核心规则

如果没有称呼，只问一个问题：

```text
我该怎么称呼你？
```

不要第一屏追问岗位、手机号、身份证、微信、邮箱或其他隐私字段。

用户回答称呼后，本轮立即使用该称呼；如果用户没有明确要求保存，只在本轮使用，不写入本地。

如果用户说“确认保存称呼”“保存这个称呼”“以后都叫我张三”，才保存到：

```text
tgravity-work-data/profile/current-user.md
```

保存前不需要生成资产卡；使用 `assets/templates/user-profile.md`。

## 信息卡字段

最低只需要：

```text
display_name：用户希望被称呼的名字
default_decision_owner：璐璐
```

可选字段：

```text
role：
department：
notes：
```

缺可选字段时不要追问。

## 日报调用

生成日报前按顺序取提交人：

1. 当前用户本轮刚回答的称呼。
2. `tgravity-work-data/profile/current-user.md` 的 `display_name`。
3. 用户输入中明确出现的“我是张三 / 我叫张三”。
4. 都没有时，先问“我该怎么称呼你？”。

日报标题必须使用：

```text
# {{display_name}}的工作日报
```

提交人字段必须使用同一个 `display_name`。

不要输出岗位限定日报标题，除非用户明确要求使用某个岗位称呼。

## 默认决策对象

默认写：

```text
需要璐璐判断
```

如果用户明确指定其他判断人，以用户输入为准。

## 保存提示

用户给出称呼后，如果当前入口是入门或日报，继续原流程，不要把保存称呼变成主任务。

可以简短提示：

```text
我先按“张三”称呼你。需要以后自动带入的话，可以说“确认保存称呼”。
```

## 启动边界

Skill 没有可靠的“Agent 程序启动钩子”。不要声称打开 Agent 时一定会自动弹出称呼问题。

正确做法：在用户第一次触发 TGravity Work 任一入口时执行称呼初始化。
