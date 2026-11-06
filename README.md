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

## 从旧接口迁移

已经在调用旧接口时，先看 path 前缀，再进对应文档。两条线不能混用。没有旧代码、从零对接的，不要走迁移。

| 旧接口 | 产品 | 怎么迁 |
|--------|------|--------|
| `/rest/v1.0/vcc/*` | 商务卡（YOP / yeevcc / open.kun.global） | 鉴权改为新 RSA 头签，按对照表换 path 和字段。沙箱改完再切生产，不承诺新旧长期并存 |
| `/rest/v1.0/caas/*` | 消费卡 | 多数只把 `v1.0` 换成 `v2.0`，参数不变。开卡旧接口仍可用，建议改到开卡 V2，并用请求号查状态。Sumsub 共享 KYC 是新增流程 |

详细说明：

- [迁移怎么选目录](./skills/kun-card-integration/references/迁移/README.md)
- [VCC 迁移总览](./skills/kun-card-integration/references/迁移/vcc/迁移总览.md)
- [CAAS 迁移总览](./skills/kun-card-integration/references/迁移/caas/迁移总览.md)

推荐话术：

```text
请用 kun-card-integration 做旧 VCC 迁移。
我用的是 /rest/v1.0/vcc/* 和 yop-demo。语言：Java。
请给鉴权改造、接口对照、能力差异和切换清单。
```

```text
请用 kun-card-integration 做旧 CAAS 迁移。
我用的是 /rest/v1.0/caas/*。语言：Java。
多数接口只改版本段。开卡请按建议迁到 V2，并说明 Sumsub 要不要接。
```

## Skills 列表

| 技能 ID | 版本 | 说明 |
|---------|------|------|
| [`kun-card-integration`](./skills/kun-card-integration/) | 1.3.5 | **统一对接**：VCC 迁移与 CAAS 迁移分目录；CAAS 多数只改路径，开卡建议 V2；见 [CAPABILITY.md](./skills/kun-card-integration/CAPABILITY.md) |

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
        └── references/            # 方案 / 状态 / 字段 / OpenAPI / 迁移
```

## 相关链接

| 链接 | 说明 |
|------|------|
| [外部机构快速对接指南](./docs/外部机构快速对接指南.md) | 安装、话术、15 分钟路径、验收清单 |
| [迁移说明](./skills/kun-card-integration/references/迁移/README.md) | 旧 VCC 与旧 CAAS 分开迁移 |
| [kun-card-integration README](./skills/kun-card-integration/README.md) | 技能包说明 |
| [opendocs.kun.global](https://opendocs.kun.global/) | 平台正式文档 |
| [CHANGELOG.md](./CHANGELOG.md) | 版本记录 |
