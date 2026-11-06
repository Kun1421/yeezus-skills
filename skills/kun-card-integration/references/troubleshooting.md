# 排障速查

先确认：**环境（沙箱/生产）**、**接口 path**、**完整错误码/报错原文**（HTTP + 平台码 + `body.code`/`message`）、**商务卡还是消费卡**。

错误码怎么处理（KLC* / 平台 400xx / 只查不重开）：见 [`产品能力/异常码处理.md`](产品能力/异常码处理.md)。

## 1. 签名 / 验签失败

1. 核对头：`App-Key`、`Api-Version`、`Customer-No`、`Timestamp`、`Sign`。
2. 待签字符串是否包含 body 全部顶级字段 + `customerNo` + `timestamp`。
3. key 是否转小写后 ASCII 排序；是否误加入 `Sign`。
4. 时间戳是否在 5 分钟内；RSA 私钥是否匹配该应用。
5. 重读 `平台文档/鉴权认证机制.md`。

## 2. 开卡失败

| 检查项 | 商务卡 | 消费卡 |
|--------|--------|--------|
| 持卡人 / KYC | 已添加持卡人，customerId 正确 | KYC 已通过，同一 customerId |
| path | `/api/common/openCard` | `/caas/card/apply-card` |
| cardType | 产品支持的类型（多为 V） | V/P 按产品 |
| accountMode | 共享须先有账户并传 accountNo | 按产品 |
| 产品码 | cardBins / 已开通产品 | 同左 |

仍失败：查开卡状态查询接口；对照 `状态与枚举.md`、`异常码处理.md`、`POST /rest/v2.0/caas/response-code-list`。

## 3. 充值 / 转账无终态

- 预付卡：充值状态查询
- 共享账户：账户充值/转出状态查询
- 勿仅依赖同步返回；非 `SUCCESS`/`FAIL` 继续轮询

## 4. Webhook 收不到 / 验签失败

1. 接收 URL 公网 HTTPS、证书有效。
2. 已配置 webhook 签名密钥。
3. 防火墙 / 路径是否配错。
4. 授权类接口是否因超时被记失败。

## 5. KYC 卡住（消费卡）

- 调 KYC 结果查询 + 是否收到 `KYC_RESULT` 通知
- 影像 fileId 是否有效；Level1 字段是否齐全
- SDK 流程是否收到提交完成通知
