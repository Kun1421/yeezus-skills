# API 对接指南（摘要）

来源：[opendocs — API对接指南](https://opendocs.kun.global/docs/api-integration/api-integration-without-sdk)

注意：未特殊说明时编码为 **UTF-8**。

## 1. 构造请求

### 1.1 请求头（必填）

实现时以在线文档表格为准，至少包含鉴权相关头（见 `鉴权认证机制.md`）：

- `App-Key`
- `Api-Version`（卡接口一般为 `2`）
- `Customer-No`
- `Timestamp`（毫秒时间戳）
- `Sign`（Base64 签名）

### 1.2 请求参数

以具体 API 的 OpenAPI / 在线文档为准（卡中心见 `../openapi/卡中心.openapi.json`）。

### 1.3 请求签名

见 `鉴权认证机制.md`。

## 2. 发起请求

| 环境 | 域名 |
|------|------|
| 沙箱 | `https://sandbox.kun.global` |
| 生产 | `https://openapi.kun.global` |

完整路径 = `serverRoot` + `apiUri`。  
例：`https://openapi.kun.global/rest/v2.0/api/common/openCard`

按 API 文档使用 POST/GET；卡中心当前清单均为 POST。

## 3. 响应处理

- HTTP **2xx**：按成功体解析业务字段（通常含业务码与 `data`）。
- HTTP **500**：按失败体解析错误码与信息。
- 响应侧验签：见 `鉴权认证机制.md`「响应验签」。

详细签名验签过程以 [鉴权认证机制](https://opendocs.kun.global/docs/api-integration/authentication-and-authorization-mechanism) 为准。
