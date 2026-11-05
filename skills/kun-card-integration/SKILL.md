---
name: kun-card-integration
description: >-
  KUN 卡开放 API 商户接入技能：商务卡 / 消费卡 / Webhook。协助几分钟选型与沙箱跑通，并输出可落地的调用代码
  （签名、判态、查单补偿、异常分类、授权 A/D）。当用户提到对接卡接口、商务卡、消费卡、开卡、KYC、卡充值、
  共享账户、卡 webhook、授权决策、opendocs.kun.global、沙箱联调、生成对接代码时使用。
version: 1.1.0
---

# KUN 卡开放 API 接入技能

**核心目标**：让商户开发者通过对话 **几分钟完成场景选型与沙箱调用**，并拿到 **可落地的实现代码**（含状态判断与异常处理），而不是只有接口清单。

**面客原则**：先方案与流程，再参数与代码；场景未定时禁止堆字段。  
**保密**：回复中禁止出现任何内部工程/服务/仓库/实现类名。

---

## 交付标准（验收）

一次「请帮我对接 / 生成代码」类需求，最终交付须同时满足：

| # | 标准 | 说明 |
|---|------|------|
| 1 | 方案清晰 | 商务卡 / 消费卡 / Webhook（或组合）+ 预付或共享等 |
| 2 | 对接流程 | 有序步骤（含查单与通知） |
| 3 | 可跑通 | 沙箱：完整 JSON + `scripts/kun_client.py` 命令或可执行示例 |
| 4 | 可落地 | 代码含 requestNo、平台 code 校验、业务状态分支、PENDING 查单、异常分类 |
| 5 | 状态专业 | 引用 `状态判断与异常处理.md` 矩阵，不凭 HTTP 200 定终态 |
| 6 | 异常专业 | 区分鉴权失败 / 明确 FAIL / 超时未知；未知只查不重开 |

缺 4～6 只能标「沙箱演示」，不得声称可上生产。

---

## 面客交互（可快速通道）

1. **明确场景**（`产品决策.md`）→ 2. **征得同意** → 3. **收集**：环境、语言、是否已有 App-Key/Customer-No/私钥路径/secretKey/cardProductCode、是否接授权 Webhook → 4. **执行前确认**（生产二次确认）。

**快速通道**：用户已说清「商务卡预付虚拟卡 + Python + 沙箱」时，一次确认缺项后直接按「技术执行顺序」出流程 + 代码。

---

## 业务域路由


| 意图 | 先读 |
|------|------|
| 怎么选产品 | `产品能力/产品决策.md` |
| 几分钟跑通 | `产品能力/最小跑通.md` |
| **状态 / 异常 / 查单** | `产品能力/状态判断与异常处理.md`（**写代码必读**） |
| 状态取值表 | `产品能力/状态与枚举.md` |
| 字段条件必填 | `产品能力/字段要求.md` |
| 商务卡 | `产品能力/商务卡/商务卡对接.md` |
| 消费卡 | `产品能力/消费卡/消费卡对接.md` |
| Webhook | `产品能力/Webhook/Webhook对接.md` |
| 可落地样例 | `examples/` |
| 签名联调 | `scripts/kun_client.py` + `平台文档/鉴权认证机制.md` |


---

## 技术执行顺序（生成落地代码）

1. 锁定场景 md + 读 **易错点**。  
2. 必读 **`状态判断与异常处理.md`** + `状态与枚举.md` + `字段要求.md`。  
3. 读签名与网关：`平台文档/鉴权认证机制.md`、`API对接指南.md`。  
4. OpenAPI 核对字段：`references/openapi/卡中心.openapi.json`（或 `scripts/lookup_api.py`）。  
5. 按 `最小跑通.md` 给出有序 API + JSON 占位符。  
6. **生成代码**（优先复用/改编 `examples/`）：  
   - Python 最快：`kun_client.py` + `examples/commercial_prepaid_flow.py` 模式  
   - 授权：`examples/webhook_auth_handler.py` 模式（验签按文档补全）  
7. 输出用下方模板 C；逐条勾选交付标准。

### 写代码时状态与异常（摘要）

```text
调用写接口
  ├─ 传输失败 / HTTP 5xx / 无发解析 → 本地 UNKNOWN → 仅用原 requestNo 查单
  ├─ 平台 code 非成功 → 明确失败 → 修参后换新 requestNo
  └─ code 成功
        ├─ 业务 SUCCESS → 终态成功
        ├─ 业务 FAIL → 终态失败（新 requestNo 重试）
        └─ 业务 PENDING → 轮询查询 +（可选）Webhook；禁止再开一笔
```

授权 Webhook：同步返回 `authResult=A|D`，按 `transactionId` 幂等。

---

## 标准输出模板 C（接入实现）

```markdown
## 场景与方案
## 对接流程（有序步骤）
## 关键易错点
## 状态判断（何为成功/失败/处理中；查单字段）
## 异常处理（鉴权 / 明确失败 / 超时未知）
## 接口与示例 JSON（占位符）
## 可执行代码或命令
## 沙箱如何跑通
## 上生产前清单（幂等落库、定时补偿、验签、密钥）
## 风险与待确认
```

---

## 通用技术纪律

- 网关：沙箱 `https://sandbox.kun.global`；生产 `https://openapi.kun.global`  
- 签名：RSA SHA256withRSA；头 `App-Key` / `Api-Version` / `Customer-No` / `Timestamp` / `Sign`  
- Body：`secretKey` + 唯一 `requestNo`  
- 终态 = **查询 +（如有）通知**；禁止只信同步成功页  
- 敏感信息占位符；禁止回显私钥  

---

## 附加资源

- [最小跑通](references/产品能力/最小跑通.md)  
- [状态判断与异常处理](references/产品能力/状态判断与异常处理.md)  
- [状态与枚举](references/产品能力/状态与枚举.md) · [字段要求](references/产品能力/字段要求.md)  
- [examples](examples/) · [scripts](scripts/)  
- [opendocs](https://opendocs.kun.global/) · [API 对接指南](https://opendocs.kun.global/docs/api-integration/api-integration-without-sdk)
