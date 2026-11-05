# kun-card-integration 完整能力清单

技能 ID：`kun-card-integration` · 版本以 `SKILL.md` frontmatter 为准（当前整合版 **1.3.0**）。

一套 skill = **新客户对接** + **旧 VCC 迁移** + **多语言可落地代码**。

---

## 1. 能力地图

```text
kun-card-integration
├─ A. 产品选型
├─ B. 新 API 从零接入（商务卡 / 消费卡 / Webhook）
├─ C. 旧 VCC → 新 API 迁移（商务卡；无双轨期）
├─ D. 鉴权与联调
├─ E. 状态 / 异常 / 查单（跨场景强制）
├─ F. 多语言代码生成（对齐 yop-demo）
├─ G. 工具脚本
└─ H. 面客交付模板（C 接入 / M 迁移）
```

---

## 2. A. 产品选型

| 能力 | 说明 | 文档 |
|------|------|------|
| 商务卡 vs 消费卡 | 路径前缀、KYC、卡形态 | `产品决策.md` |
| 预付 vs 共享账户 | `accountMode=1/2` | `产品决策.md` · `商务卡对接.md` |
| 是否接 Webhook | 授权/清算/OTP/卡状态 | `Webhook对接.md` |

---

## 3. B. 新 API 从零接入

| 能力 | 说明 |
|------|------|
| 最小跑通 | cardBins → 持卡人 → openCard → 查单（商务预付） |
| 共享账户链路 | 建户 → 充值/查单 → 开卡挂账 |
| 消费卡 | KYC → apply-card → 查单（caas 前缀） |
| 卡资金 | 充值/转出 + 状态查询 |
| 批量开卡/销卡 | 任务查询至终态 |
| 卡信息/余额/限额/激活 | 运维查询与配置 |
| Webhook 接收 | 验签、`authResult=A\|D`、幂等 |
| 沙箱命令 | `kun_client.py call` |
| 可落多样例 | Python / Java 仓库样例；其他语言同构生成 |

---

## 4. C. 旧 VCC 迁移（已整合，不另开 skill）

| 能力 | 说明 |
|------|------|
| 范围 | **仅商务卡**旧 `/rest/v1.0/vcc/*`；消费卡 caas 另册 |
| 范式切换 | YOP（yop-demo）→ 新 RSA 头签 + `secretKey`/`requestNo` |
| 接口对照 | `迁移/mapping.yaml` + `接口对照表.md` |
| 查询拆分 | 旧 `card-recharge-query` → 充值查单 / 转出查单 |
| 新增查单 | 账户充值/转出状态查询（旧无） |
| 待补接口 | `user-cards`、`card-remark` → `pending_add`（新侧将补） |
| 切换策略 | **无双轨期**：沙箱改完 → 生产切新 |
| 对照 CLI | `scripts/lookup_mapping.py` |

---

## 5. D. 鉴权与联调

| 能力 | 旧（迁移对照） | 新（接入/迁移后） |
|------|----------------|-------------------|
| 签名 | YOP v3 RSA（yop-demo） | SHA256withRSA 请求头 `Sign` |
| Webhook | HMAC-SHA256 v1（yop-demo） | 按 opendocs 新验签 |
| 联调 | yop-demo 菜单调用 | `kun_client.py` / 各语言客户端 |
| 网关 | 客户存量 YOP | `sandbox.kun.global` / `openapi.kun.global` |

---

## 6. E. 状态 / 异常 / 查单（强制）

| 能力 | 要点 |
|------|------|
| 两层结果 | HTTP/`code` vs 业务状态字段 |
| 开卡等 | SUCCESS / FAIL / PENDING |
| 未知 | 超时/5xx/无法解析 → 只查不重开 |
| 幂等 | `requestNo`；Webhook `transactionId` |
| 双通道 | 查询 + 通知，终态不回退 |

---

## 7. F. 多语言（对齐 yop-demo）

| 语言 | 仓库样例 | Agent |
|------|----------|-------|
| Python | ✅ flow + kun_client + webhook | 复用 |
| Java | ✅ `examples/java/` | 复用 |
| Java-Web / Node / TS / Go / PHP / .NET | — | 按同构判态生成 |

---

## 8. G. 工具脚本

| 脚本 | 作用 |
|------|------|
| `scripts/kun_client.py` | 新 API 签名与调用 |
| `scripts/lookup_api.py` | OpenAPI/索引查询 |
| `scripts/lookup_mapping.py` | 旧 path → 新 path |

---

## 9. H. 交付模板

| 模板 | 场景 |
|------|------|
| **C** | 从零接入 |
| **M** | 旧 VCC 迁移（含切换清单，无双轨） |

---

## 10. 明确不在本 skill（或另册）

| 项 | 说明 |
|----|------|
| 消费卡旧 caas 迁移 | 另册，不在当前 mapping |
| 伪造 `pending_add` 的新 path | `user-cards` / `card-remark` 上线前禁止编造 |
| 内部服务实现细节 | 面客禁止 |
| 长期旧新双轨运营 | **不支持**；无双轨期 |

---

## 11. 推荐话术

**新接入：**

```text
请用 kun-card-integration 对接。商务卡预付虚拟卡。沙箱。语言：TypeScript。
要步骤、JSON、kun_client 命令、可落地代码（PENDING/超时只查单）。
```

**迁移：**

```text
请用 kun-card-integration 做旧 VCC 迁移。我用的是 /rest/v1.0/vcc/* 与 yop-demo。
语言：Java。请给鉴权改造 + 接口对照 + 查单/Webhook 必改项 + 切换清单（无双轨）。
```
