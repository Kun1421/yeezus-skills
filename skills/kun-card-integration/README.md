# KUN 卡开放 API 统一对接技能

[![版本](https://img.shields.io/badge/version-1.3.4-blue)](./SKILL.md)

> **一套 skill**：新客户接入（商务卡 / 消费卡 / Webhook）+ 旧 VCC（YOP / open.kun）迁移到 opendocs。  
> 技能 ID：`kun-card-integration`  
> **完整能力清单：** [CAPABILITY.md](./CAPABILITY.md)  
> **语言：** 对齐 yop-demo（Python / Java / Node / TS / Go / PHP / .NET…）  
> **迁移：** `references/迁移/vcc/` 与 `references/迁移/caas/` 分开。当前对照和能力差异只属于 VCC。

对外指南：[../../docs/外部机构快速对接指南.md](../../docs/外部机构快速对接指南.md)

## 你能得到什么

| 场景 | 产出 |
|------|------|
| 从零对接 | 选型 → 流程 → 沙箱命令 → 可落地代码（判态/查单/异常） |
| 旧 VCC 迁移 | 只读 `迁移/vcc/`：鉴权切换 → 新旧对照 → 能力差异 → 切换清单 |
| 旧 CAAS 迁移 | 只读 `迁移/caas/`。不使用 VCC 的 mapping 和能力差异 |
| 任意支持语言 | 同构判态；Py/Java 有仓库样例，其余对话生成 |

## 目录

```text
kun-card-integration/
├── SKILL.md                 # Agent 入口
├── CAPABILITY.md            # 完整能力清单
├── README.md
├── examples/                # Py / Java 可落多样例
├── scripts/
│   ├── kun_client.py        # 新 API 联调
│   ├── lookup_api.py
│   └── lookup_mapping.py    # 仅旧 VCC → 新 API
└── references/
    ├── 产品能力/            # 选型、跑通、状态、字段、多语言、商务/消费/Webhook
    ├── 迁移/
    │   ├── README.md        # 先分 VCC / CAAS
    │   ├── vcc/             # 旧 /rest/v1.0/vcc/* ：总览、对照、能力差异、鉴权、mapping.yaml
    │   └── caas/            # 旧 /rest/v1.0/caas/* ：与 VCC 分开，对照未单列
    ├── 平台文档/
    └── openapi/
```

## 安装

```bash
mkdir -p ~/.agents/skills
ln -sfn /path/to/yeezus-skills/skills/kun-card-integration ~/.agents/skills/kun-card-integration
```

## 快速命令

```bash
# 新 API 联调
cd scripts && pip install -r requirements.txt
python kun_client.py call --env sandbox ...

# 查旧接口对应新 path
python lookup_mapping.py card-open
python lookup_mapping.py --list-pending
```

## 示例提问

- 「商务卡预付虚拟卡，Go，沙箱，可落地开卡代码。」  
- 「旧 VCC `/rest/v1.0/vcc/card-open` 迁到新 API，Java，要对照和鉴权改造。」  
- 「开卡 PENDING / 超时能不能重开？」  
- 「授权 webhook 返回 A/D 与幂等（Node.js）。」
