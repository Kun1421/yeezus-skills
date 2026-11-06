---
name: kun-card-integration
description: >-
  KUN 卡开放 API 统一对接技能：新客户接入（商务卡/消费卡/Webhook）+ 旧 VCC（yeevcc/YOP/open.kun.global）
  迁移到 opendocs。  覆盖选型、沙箱跑通、可落地代码（签名、判态、查单、异常码处理、授权 A/D）、新旧接口对照与鉴权切换。
  语言对齐 yop-demo：Python/Java/Node/TS/Go/PHP/.NET。当用户提到对接卡、开卡、KYC、充值、共享账户、
  webhook、错误码、KLC、旧VCC迁移、yop-demo、opendocs.kun.global、沙箱联调时使用。
version: 1.3.5
---

# KUN 卡开放 API 统一对接技能

**核心目标**：一套 skill 覆盖 **从零接入** 与 **旧 VCC 迁移**，几分钟内给出方案、对照、可跑通调用与可落地代码。

**面客原则**：先场景/是否迁移 → 再流程 → 再参数与代码；场景未定禁止堆字段。  
**语言**：对齐 **yop-demo**（见 `多语言对齐.md`）。  
**无双轨期**（迁移）：改完即切新，不承诺旧新长期并存。  
**保密**：禁止出现内部工程/服务/仓库/实现类名；禁止回显私钥。

---

## 能力总览（Agent 先判意图）

| 意图 | 入口 |
|------|------|
| 从零对接新 API | `产品能力/产品决策.md` → `最小跑通.md` |
| 旧 VCC → 新 API 迁移 | `迁移/vcc/迁移总览.md` → `接口对照表.md` / `mapping.yaml` |
| 旧 CAAS → 新 API 迁移 | `迁移/caas/迁移总览.md`（不要用 VCC 的 mapping） |
| 查旧 path 对应新接口 | `scripts/lookup_mapping.py`（按 `/vcc/` 或 `/caas/` 分目录） |
| 判态 / 查单 / 异常 | `产品能力/状态判断与异常处理.md`（**写代码必读**） |
| **异常码 / KLC / 平台码** | `产品能力/异常码处理.md`（**写代码必读**） |
| 多语言 | `产品能力/多语言对齐.md` |

完整能力清单见 [`CAPABILITY.md`](./CAPABILITY.md)。

---

## 交付标准

### A. 从零接入（模板 C）

| # | 标准 |
|---|------|
| 1 | 方案清晰（商务/消费/Webhook + 预付或共享） |
| 2 | 有序流程含查单与通知 |
| 3 | 沙箱 JSON + `kun_client` 或所选语言可执行示例 |
| 4 | 可落地：requestNo、code、SUCCESS/FAIL/PENDING、超时只查 |
| 5 | 状态专业：不凭 HTTP 200 定终态 |
| 6 | 异常码专业：按 `异常码处理.md` 分支（鉴权不重试写；`KLC9600`/5xx 只查；`KLC0009` 幂等） |

### B. 迁移（模板 M）

| # | 标准 |
|---|------|
| 1 | 旧 path → 新 path（含 split / partial / gap / new_only；含能力差异） |
| 2 | 鉴权：YOP/yop-demo → 新 RSA 头签步骤 |
| 3 | GET→POST、`requestNo`+`secretKey` |
| 4 | 资金查单改造（拆分 + 账户新查单） |
| 5 | Webhook 全量切新 |
| 6 | **切换清单（无双轨）**；标明语言 |

---

## 面客交互

1. 判定：**新接入**、**旧 VCC 迁移**或 **旧 CAAS 迁移**。旧 path 含 `/rest/v1.0/vcc/` 才进 `迁移/vcc/`；含 `/rest/v1.0/caas/` 才进 `迁移/caas/`。禁止把 VCC 对照套到 CAAS。  
2. 收集：环境、语言（yop-demo 矩阵）、凭证是否齐全、是否 Webhook；迁移则收集已用旧 path 清单。  
3. 生产切换须二次确认。

**快速通道（新接入）**：商务卡预付虚拟卡 + `<语言>` + 沙箱 → 直接模板 C。  
**快速通道（VCC 迁移）**：已列出旧 `/rest/v1.0/vcc/*` + 语言 → `迁移/vcc/` 对照 + 鉴权改造 + 模板 M。  
**快速通道（CAAS 迁移）**：已列出旧 `/rest/v1.0/caas/*` → `迁移/caas/`。多数只改版本段；开卡建议迁 V2 并用 `openCardQuery`；Sumsub 按总览另接。不要套 VCC 字段差异。

---

## 业务域路由

| 意图 | 先读 |
|------|------|
| 怎么选产品 | `产品能力/产品决策.md` |
| 几分钟跑通 | `产品能力/最小跑通.md` |
| **旧 VCC 迁移** | `迁移/vcc/迁移总览.md` |
| VCC 新旧对照 | `迁移/vcc/接口对照表.md` · `迁移/vcc/mapping.yaml` |
| VCC 同能力字段 / 缺口 | `迁移/vcc/能力差异.md` |
| VCC 鉴权从 YOP 切换 | `迁移/vcc/鉴权迁移.md` |
| **旧 CAAS 迁移** | `迁移/caas/迁移总览.md` · `接口对照表.md` · `mapping.yaml` |
| 多语言 | `产品能力/多语言对齐.md` |
| 状态/异常/查单 | `产品能力/状态判断与异常处理.md` |
| **异常码处理** | `产品能力/异常码处理.md` |
| 状态枚举 / 字段 | `状态与枚举.md` · `字段要求.md` |
| 商务卡 / 消费卡 / Webhook | 各自对接 md |
| 样例 | `examples/` |
| 签名联调 | `scripts/kun_client.py` |
| 对照查询 | `scripts/lookup_mapping.py` |

---

## 技术执行顺序

### 从零接入

1. 锁定场景 + 易错点 → 2. **状态 + 异常码** + 字段必读 → 3. 鉴权文档 → 4. OpenAPI  
5. 最小跑通 JSON → 6. 按语言生成代码（同构判态与异常码分支）→ 7. 模板 C

### 旧 VCC 迁移

只读 `迁移/vcc/`。

1. `vcc/迁移总览`（无双轨）→ 2. `vcc/鉴权迁移`（yop-demo → 新 RSA）  
3. `lookup_mapping` / `vcc` 对照表替换 path → 按 `vcc/能力差异.md` 改字段语义 → 4. 资金查单与 Webhook  
5. 按语言改客户端 → 6. 沙箱冒烟 → 7. 切换清单 → 模板 M  
8. 判态与异常码挂接 `状态判断与异常处理.md` + `异常码处理.md`

### 旧 CAAS 迁移

只读 `迁移/caas/`。不要执行上面的 VCC 步骤，不要套用 `vcc/能力差异.md`。

1. 确认旧 path 是 `/rest/v1.0/caas/*`  
2. 默认只把版本段改成 `v2.0`，参数不动（`caas/接口对照表.md`）  
3. 开卡：旧 `apply-card` 仍可用；建议改 `openCard`，查单用 `openCardQuery` 的 `originalRequestNo`  
4. 要接 Sumsub 时按 `caas/迁移总览.md` 第 3 节，终态仍走 `kyc-notify`  
5. 判态与异常码仍挂 `状态判断与异常处理.md` + `异常码处理.md`

### 写代码判态与异常码（摘要）

```text
写接口
  ├─ 传输/5xx/无法解析/KLC9600 → UNKNOWN → 原 requestNo 只查单
  ├─ 鉴权/平台 40047 → FIX_CONFIG，不重试写
  ├─ body.code 非成功 → 按异常码处理.md
  │     ├─ KLC0009 → 幂等用原结果
  │     ├─ KLC0002/0003/0004/0008 → 修参 + 新 requestNo
  │     └─ KLC0005/0013/9999 → 先查单
  └─ code 成功 → 业务 SUCCESS / FAIL / PENDING（PENDING 禁止再开）
```

---

## 输出模板

**C（接入）**：场景 → 流程 → 易错点 → 状态 → 异常 → **异常码** → JSON → 代码 → 沙箱 → 上生产 → 风险  

**M（迁移）**：范围 → 鉴权 → 对照 → 行为差异 → 改造步骤 → 查单/Webhook → 异常码 → 沙箱 → **切换清单（无双轨）** → 风险  

---

## 通用技术纪律

- 新网关：沙箱 `https://sandbox.kun.global`；生产 `https://openapi.kun.global`  
- 新签名：RSA SHA256withRSA；头 `App-Key` / `Api-Version` / `Customer-No` / `Timestamp` / `Sign`  
- Body：`secretKey` + 唯一 `requestNo`  
- 终态 = 查询 +（如有）通知  
- 语言不绑死；敏感信息占位符  

---

## 附加资源

- [CAPABILITY.md](./CAPABILITY.md) · [多语言对齐](references/产品能力/多语言对齐.md)  
- [最小跑通](references/产品能力/最小跑通.md) · [迁移分目录](references/迁移/README.md) · [VCC 迁移](references/迁移/vcc/迁移总览.md) · [CAAS 迁移](references/迁移/caas/迁移总览.md)  
- [状态判断与异常处理](references/产品能力/状态判断与异常处理.md) · [异常码处理](references/产品能力/异常码处理.md)  
- [examples](examples/) · [scripts](scripts/)  
- [opendocs](https://opendocs.kun.global/)
