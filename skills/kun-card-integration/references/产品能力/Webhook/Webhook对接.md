# Webhook 对接

平台（KUN）**主动调用商户 URL**。文档中的示例 `url` 字段可忽略，**实际回调地址由合作方配置**。

> 类型与状态见 [`状态与枚举.md`](../状态与枚举.md)；授权请求/响应字段见 [`字段要求.md`](../字段要求.md) §5。索引：`webhook`。

## Webhook 清单

| 类型 | path（文档标识） | 方向 | 商户侧要点 |
|------|------------------|------|------------|
| 交易授权决策 | `/rest/v2.0/caas/webhook/transaction` | 同步决策 | **必须快速返回批准/拒绝**；超时可能导致授权失败 |
| 授权释放 | `/rest/v2.0/caas/webhook/auth-release` | 异步通知 | 幂等更新授权状态 |
| 清算 | `/rest/v2.0/caas/webhook/clearing` | 异步通知 | 入账/清算终态 |
| 交易结果 | `/rest/v2.0/caas/transaction/result-nofity` | 异步通知 | 注意 path 历史拼写 `nofity` |
| 3DS OTP | `/rest/v2.0/caas/webhook/otp-3ds` | 异步通知 | 转发给持卡人展示 OTP |
| PIN 设置结果 | `/rest/v2.0/caas/webhook/pin-setup` | 异步通知 | 更新 PIN 状态 |
| 卡状态变更 | `/rest/v2.0/caas/webhook/card-status-update` | 异步通知 | 同步商户卡状态机 |
| 卡片 Token | `/rest/v2.0/caas/webhook/card-token-notify` | 异步通知 | Apple/Google Pay 等 |
| 封锁码新增 | `/rest/v2.0/caas/webhook/add-block-code-notify` | 异步通知 | 风控/客服处理 |
| 预售卡申请结果 | `/rest/v2.0/caas/webhook/presale-card-apply-result` | 异步通知 | 消费卡预售流程 |
| KYC 提交完成 | `/rest/v2.0/caas/customer/kyc-completion-notify` | 异步通知 | SDK 流程 |
| KYC 结果 | `/rest/v2.0/caas/customer/kyc-notify` | 异步通知 | 驱动后续开卡 |

配置验签密钥（商户主动调用，非 webhook）：

- `POST /rest/v2.0/caas/config/webhook-sign-key-config`（body 以 `signKey` 为主）
- 或在商户后台「技术参数」打开签名开关并填写同一把签名密钥

推荐密钥：32 字节随机值的 Base64（256-bit），由商户自生成并自行保管。

## 回调签名（HMAC-SHA256 v1）

平台向商户 URL **出站推送**时，若已开启签名校验且 `signKey` 非空，会在请求头携带：

| Header | 含义 |
|--------|------|
| `X-Webhook-Timestamp` | epoch **秒** |
| `X-Webhook-Signature` | 小写 hex；也可能是 `v1=<hex>` |
| `X-Webhook-Type` | 通知类型（若有） |

### 算法

```text
signing_string = "{timestamp}.{rawBody}"   # 中间一个点号
signature      = lowercase_hex( HMAC_SHA256( UTF8(signKey), UTF8(signing_string) ) )
```

**`rawBody` 必须是 HTTP 请求体原文（UTF-8）**，不要 `JSON.parse` 后再 `stringify`，不要按 key 排序重排。签名与 body 字节不一致是验签失败的最常见原因。

### 商户验签步骤

1. 读取 `X-Webhook-Timestamp`、`X-Webhook-Signature` 与 **原始 body**。  
2. 校验 `|now - timestamp| ≤ 300` 秒（防重放；可按风控加严）。  
3. 用配置的 `signKey` 按上式重算 hex，与头中签名做常量时间比较（支持去掉 `v1=` 前缀）。  
4. 通过后再解析 JSON、改业务态；失败返回 4xx，**不改业务**。

### 可落代码

| 语言 | 文件 |
|------|------|
| Python | `examples/webhook_hmac_v1.py`（`verify_v1_hex` / `verify_from_headers`） |
| Python + Flask | `examples/webhook_auth_handler.py` |
| Java | `examples/java/WebhookHmacV1.java` |

环境变量示例：`KUN_WEBHOOK_SIGN_KEY=<与平台配置相同的签名密钥>`。

未开启签名开关时，平台可能不带上述头；生产一旦开签，接收端应强制验签。

## 商务卡 vs 消费卡场景差异

| 能力 | 商务卡典型 | 消费卡典型 |
|------|------------|------------|
| 交易授权 `transaction` | 常接（广告/差旅实时控额） | 常接 |
| 清算 / 交易结果 | 建议接 | 建议接 |
| 3DS OTP / PIN | 视产品 | 实体卡/消费场景更常见 |
| KYC 通知 | 一般不涉及 | **必接**（若走 KYC） |
| 预售卡结果 | 不涉及 | 预售产品必接 |
| 封锁码 / Token | 按产品 | 按产品 |

同一套 webhook 协议可共用接收服务，用 `webhookType` / path 分流。

## 状态与异常（Webhook）

| 类型 | 成功应答 | 异常 |
|------|----------|------|
| AUTH_WEBHOOK | 快速 JSON：`authResult=A\|D`，建议带 requestNo | 验签失败 → 4xx 且不改业务；超时依赖平台约定；重复 tx 幂等同结果 |
| 异步通知（清算/OTP/卡状态/KYC…） | HTTP 2xx + 内部幂等落库 | 验签失败拒绝；处理慢则先应答再异步；终态不回退 |
| 与查单冲突 | 以再次查询为准并告警 | 见状态判断文档双通道 |

落地样例：`examples/webhook_auth_handler.py` + `examples/webhook_hmac_v1.py`（已实现 HMAC-SHA256 v1）。

## 推荐接入顺序

```text
1. webhook-sign-key-config 配置验签密钥
2. 实现通用接收：验签 → 幂等落库 → 按类型分发
3. 先接异步通知（卡状态、清算、KYC）打通联调
4. 再接同步授权 transaction（压测超时与失败回退）
5. 按产品补 OTP / PIN / Token / 封锁码 / 预售
```

## 授权决策（transaction）要点

`webhookType` 多为 `AUTH_WEBHOOK`。请求含 `transactionId`、`cardId`、`customerId`、`transactionType`、金额币种、MCC、商户名等；Token 交易含 `dpan` / `walletProvider`。

商户同步响应：

| 字段 | 要求 |
|------|------|
| authResult | **`A`**=批准 / **`D`**=拒绝 |
| requestNo / code / message | 建议回传 |
| responseCode / declinedReason | 拒绝时建议填 |

要求：低延迟；同一 `transactionId` 幂等返回一致决策；禁止长时间挂起（超时策略以联调约定为准）。

卡状态推送事件：`ACTIVE` / `FREEZE` / `UNFREEZE` / `CANCEL` / `LOCK` / `UNLOCK` / `PHYSICAL_CARD_ACTIVE`。

## 异步通知要点

- 验签通过后再改业务状态。
- 以业务主键幂等（`transactionId` / 通知内唯一号）。
- 快速返回 HTTP 成功；重活异步化。
- 平台可能重试；商户须可重入。
- 终态仍可用查询类 API 对账（如 `query-transaction`、充值查询）。

## 易错点

- **把文档示例 URL 当成真实回调地址** → 以商户配置的接收地址为准。
- **授权接口当普通通知** → `transaction` 是同步决策，必须返回批准/拒绝。
- **未配 webhook-sign-key / 未开签名开关** → 无签名头，或跳过验签导致伪造风险。
- **验签用错 body**：对 JSON 重排/再序列化 → `signature_mismatch`。必须用原始字节。
- **密钥搞混**：OpenAPI body `secretKey` ≠ Webhook `signKey`（签名密钥）。
- **消费卡漏接 KYC 通知** → 开卡时机错误。
- **拼写**：`result-nofity` 按 path 原样配置路由。

## 排障

| 现象 | 排查 |
|------|------|
| 收不到通知 | 公网可达、TLS、IP 白名单、路径配置、平台重试日志 |
| 验签失败 | 密钥与平台是否同一把；是否用原文 body；时间窗 300s；头名 `X-Webhook-*` |
| `timestamp_out_of_range` | 服务器时钟；容忍秒数是否过严 |
| `signature_mismatch` | body 被中间件改写；密钥含多余空格/换行；误用 RSA 私钥或 `secretKey` |
| 授权大量拒绝/超时 | 商户 RT、依赖超时、幂等锁死 |
| 状态不一致 | 通知 + 主动查询对账 |
