# 可落地示例代码

语言矩阵与 **yop-demo** 对齐（详见 [`../references/产品能力/多语言对齐.md`](../references/产品能力/多语言对齐.md)）。  
**判态 / 查单 / 异常分类在所有语言中必须同构**；仓库已落盘样例可直接跑，其余由 Agent 按同构模板生成。

| 语言（对齐 yop-demo） | 仓库样例 | 说明 |
|----------------------|----------|------|
| Python (`python-demo`) | `commercial_prepaid_flow.py`、`webhook_auth_handler.py`；联调 `../scripts/kun_client.py` | 最快沙箱联调 |
| Java (`java-demo` / without-sdk) | `java/KunOpenApiClient.java`、`java/CommercialPrepaidFlow.java`、`java/pom.xml` | JDK 11+ |
| Java-Web (`java-web-demo`) | （按需生成） | Spring 等 Web 封装，逻辑同 `CommercialPrepaidFlow` |
| Node.js (`nodejs-demo`) | （按需生成） | 签名客户端 + 开卡/查单流程 |
| TypeScript (`typescript-demo`) | （按需生成） | 同上，TS 类型化 |
| Go (`go-demo`) | （按需生成） | |
| PHP (`php-demo`) | （按需生成） | |
| .NET (`dotNet-demo`) | （按需生成） | |

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

## 其他语言（Node / TS / Go / PHP / .NET / Java-Web）

仓库暂未逐语言落盘完整工程时，对话中说明语言即可；Agent 须：

1. 按 `多语言对齐.md` 生成**等价**签名客户端与开卡流程  
2. **不得**删掉 SUCCESS/FAIL/PENDING/UNKNOWN 分支  
3. 沙箱冒烟仍可用 `scripts/kun_client.py`（与业务语言可分离）

Agent 给客户写代码时：以本目录与判态文档为骨架扩展，**不要**删掉判态与异常分支。
