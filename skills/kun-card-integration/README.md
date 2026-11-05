# KUN 卡开放 API 接入技能

[![版本](https://img.shields.io/badge/version-1.1.0-blue)](./SKILL.md)

> 面向商户 / 外部机构开发者：几分钟选型与沙箱跑通，并输出**可落地**的对接代码（判态、查单、异常、Webhook）。  
> 技能 ID：`kun-card-integration`

**外部机构请优先阅读仓库文档：** [../../docs/外部机构快速对接指南.md](../../docs/外部机构快速对接指南.md)（安装、推荐话术、15 分钟路径、验收清单）。

## 能帮你做什么

1. 选商务卡 / 消费卡 / Webhook 方案  
2. 给出有序对接流程与必填示例 JSON  
3. 用 `scripts/kun_client.py` 在沙箱发出已签名请求  
4. 基于 `examples/` 生成可落地代码（状态机、PENDING 轮询、异常分类、授权 A/D）  
5. 按专业矩阵解释状态与异常，避免「HTTP 200 当成功」

## 目录

```text
kun-card-integration/
├── SKILL.md
├── README.md
├── examples/                         # 可落地样例
│   ├── commercial_prepaid_flow.py
│   └── webhook_auth_handler.py
├── scripts/
│   ├── kun_client.py                 # 签名 + 调用
│   └── lookup_api.py
└── references/
    ├── 产品能力/
    │   ├── 产品决策.md
    │   ├── 最小跑通.md
    │   ├── 状态判断与异常处理.md     # 落地必读
    │   ├── 状态与枚举.md
    │   ├── 字段要求.md
    │   ├── 商务卡/ 消费卡/ Webhook/
    │   └── api-index.yaml
    ├── 平台文档/
    ├── openapi/卡中心.openapi.json
    └── troubleshooting.md
```

## 安装

**个人技能：**

```bash
mkdir -p ~/.agents/skills
ln -sfn /path/to/yeezus-skills/skills/kun-card-integration ~/.agents/skills/kun-card-integration
```

**项目技能：**

```bash
mkdir -p .agents/skills
ln -sfn /path/to/yeezus-skills/skills/kun-card-integration .agents/skills/kun-card-integration
```

## 沙箱 3 分钟试跑

```bash
cd scripts
pip install -r requirements.txt
python kun_client.py gen-key --out-dir ./keys
# 公钥配到开放平台后：
python kun_client.py call --env sandbox \
  --app-key YOUR_APP_KEY --customer-no YOUR_CUSTOMER_NO \
  --private-key ./keys/merchant_private.pem \
  --path /rest/v2.0/api/common/cardBins \
  --body '{"requestNo":"r1","secretKey":"YOUR_SECRET_KEY","ip":"127.0.0.1"}'
```

完整开卡流程见 `examples/commercial_prepaid_flow.py`；状态规范见 `references/产品能力/状态判断与异常处理.md`。

## 示例提问

- 「商务卡预付虚拟卡，Python 沙箱，给我能跑通且能上线改的代码。」  
- 「开卡返回 PENDING 怎么处理？超时了能不能重开？」  
- 「授权 webhook 怎么返回批准，怎么做幂等？」
