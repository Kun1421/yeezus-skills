# 可落地示例代码

| 文件 | 说明 |
|------|------|
| `commercial_prepaid_flow.py` | 商务卡预付虚拟卡（Python）：拉产品 → 持卡人 → 开卡 → **判态/查单** |
| `webhook_auth_handler.py` | 授权 Webhook：验签骨架 + `A`/`D` 幂等响应 |
| `java/KunOpenApiClient.java` | Java 签名客户端（RSA SHA256withRSA） |
| `java/CommercialPrepaidFlow.java` | 商务卡预付虚拟卡（Java）：与 Python 同构判态/查单/异常分类 |
| `java/pom.xml` | 最小 Maven 依赖（Jackson + exec 插件） |

## Python

1. `pip install -r ../scripts/requirements.txt`
2. 配置环境变量或改文件顶部 `Config`（勿提交真实密钥）
3. 沙箱先跑通；生产前按 `状态判断与异常处理.md` 补齐 DB 幂等与定时查单

## Java（沙箱）

```bash
cd java
export KUN_ENV=sandbox
export KUN_APP_KEY=YOUR_APP_KEY
export KUN_CUSTOMER_NO=YOUR_CUSTOMER_NO
export KUN_SECRET_KEY=YOUR_SECRET_KEY
export KUN_PRIVATE_KEY=/path/to/merchant_private.pem
# export KUN_CARD_PRODUCT_CODE=YOUR_CODE   # 可选；不设则先 cardBins
mvn -q exec:java
```

要求：JDK 11+。生产前补齐 DB 幂等、`requestNo` 唯一约束、定时查单补偿与响应验签。

Agent 给客户写代码时：以本目录为骨架扩展，**不要**删掉判态与异常分支。
