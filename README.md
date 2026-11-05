# yeezus-skills

> KUN 卡开放能力 · 面向 Coding Agent 的 Skills 仓库。  
> **外部机构请先读：** [docs/外部机构快速对接指南.md](./docs/外部机构快速对接指南.md)

用 AI 编码工具（如 Cursor）安装技能后，通过自然语言即可：**选型 → 对接流程 → 沙箱跑通 → 可落地代码**（含状态判断与异常处理）。

## 给外部机构：3 步开始

1. **安装技能**（软链到 Agent Skills 目录，见下方或[完整指南](./docs/外部机构快速对接指南.md)）  
2. **新开对话**，发送推荐话术，例如：

```text
请用 kun-card-integration 帮我对接合规卡开放 API。
场景：商务卡、预付模式、虚拟卡。环境：沙箱。语言：TypeScript。
请给出对接步骤、示例 JSON、可执行命令，以及可落地代码（含 PENDING 判态与超时只查单）。
```

语言与 **yop-demo** 对齐：Python / Java / Node.js / TypeScript / Go / PHP / .NET 等均可。

3. **按输出在沙箱执行**；私钥只提供本机文件路径，不要粘贴到聊天。

开放文档：[opendocs.kun.global](https://opendocs.kun.global/)

## Skills 列表

| 技能 ID | 版本 | 说明 |
|---------|------|------|
| [`kun-card-integration`](./skills/kun-card-integration/) | 1.3.1 | **统一对接**：新接入 + 旧 VCC 迁移 + 异常码处理；多语言对齐 yop-demo；见 [CAPABILITY.md](./skills/kun-card-integration/CAPABILITY.md) |

## 安装

```bash
cd /path/to/yeezus-skills

# 个人（本机全局）
mkdir -p ~/.agents/skills
ln -sfn "$(pwd)/skills/kun-card-integration" ~/.agents/skills/kun-card-integration

# 或：仅当前业务项目
# mkdir -p /path/to/your-project/.agents/skills
# ln -sfn "$(pwd)/skills/kun-card-integration" /path/to/your-project/.agents/skills/kun-card-integration

test -f ~/.agents/skills/kun-card-integration/SKILL.md && echo "安装成功"
```

软链须指向 `skills/kun-card-integration/`（含 `SKILL.md` 的目录）。

## 目录

```text
yeezus-skills/
├── README.md
├── CHANGELOG.md
├── docs/
│   └── 外部机构快速对接指南.md    # ← 对外使用说明
└── skills/
    └── kun-card-integration/
        ├── SKILL.md
        ├── examples/              # 可落地样例
        ├── scripts/               # 签名联调
        └── references/            # 方案 / 状态 / 字段 / OpenAPI
```

## 相关链接

| 链接 | 说明 |
|------|------|
| [外部机构快速对接指南](./docs/外部机构快速对接指南.md) | 安装、话术、15 分钟路径、验收清单 |
| [kun-card-integration README](./skills/kun-card-integration/README.md) | 技能包说明 |
| [opendocs.kun.global](https://opendocs.kun.global/) | 平台正式文档 |
| [CHANGELOG.md](./CHANGELOG.md) | 版本记录 |
