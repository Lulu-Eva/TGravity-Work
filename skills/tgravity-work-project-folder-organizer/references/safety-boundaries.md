# Safety Boundaries

Directory organization is destructive. Default to proposal mode.

## Never Move Automatically

Mark these as `no` in migration lists:

```text
营业执照
公章
身份证
银行卡
合同扫描件
签约扫描件
盖章件
密码
API Key
token
secret
私聊记录
客户隐私
原始视频素材
原始音频素材
历史版本
压缩备份
```

## Manual Review

Mark these as `manual_review`:

```text
合同模板
劳动合同
发票
报销表
客户名单
报价单
商业合作资料
平台后台截图
含个人信息的表格
```

## Usually Safe

Mark these as `yes` only if the target path is clear:

```text
普通 Markdown 说明
草稿文档
公开图片素材
非敏感设计稿
公开资料调研
空文件夹
重复导出的普通中间文件
```

## Required Confirmation

Before moving files, output:

```text
我将只移动迁移清单中 `yes` 的项目，跳过 `manual_review` 和 `no`。确认执行吗？
```

If the user says "全部整理" but the migration list includes sensitive items, treat that as insufficient confirmation. Ask for explicit confirmation on the sensitive group.

## Backup Rule

For more than 10 moves, or any move involving non-Markdown files, require either:

```text
1. 用户确认已有备份
2. 先创建变更清单，不移动文件
```

Do not create backups by copying huge video, image, or archive folders unless the user explicitly asks.
