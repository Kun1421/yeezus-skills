# 变更历史

最新条目置顶；技能版本以各自 `SKILL.md` frontmatter 为准。

## kun-card-integration 1.3.5 - 2026-11-06

按对照表 caas sheet 写好 `references/迁移/caas/`：多数接口只把 `/rest/v1.0/caas/` 换成 `/rest/v2.0/caas/`，参数不变。旧开卡仍可用，建议迁到 `openCard`，并用 `openCardQuery` 按 `originalRequestNo` 查状态。V2 新增 Sumsub 共享 KYC（`kyc-sumsub-shareToken`，终态走 `kyc-notify`）。

## kun-card-integration 1.3.4 - 2026-11-06

迁移拆成两个目录：`references/迁移/vcc/`（现有商务卡旧 VCC 对照与能力差异）和 `references/迁移/caas/`（消费卡旧 CAAS，明确禁止套用 VCC mapping）。`lookup_mapping.py` 只查 VCC。

## kun-card-integration 1.3.3 - 2026-11-06

旧 VCC 迁移补充对外能力差异：新增 `references/迁移/能力差异.md`（身份、卡定位、产品码、账户模式、同能力字段、缺口与新增查询）。`mapping.yaml` 增加冻结/解冻、销卡、MCC、对账文件、Webhook 密钥，以及 `user-info`/`clear-record`/`card-swap` 的 partial/gap。

## kun-card-integration 1.3.2 - 2026-11-05

补齐旧 VCC `user-cards` / `card-remark` 对照：`POST /rest/v2.0/api/common/userCards`、`POST /rest/v2.0/api/common/updateCardRemark`；纳入 mapping、字段要求、商务卡对接、api-index 与本地 OpenAPI 片段。

## kun-card-integration 1.3.1 - 2026-11-05

新增 [`异常码处理.md`](./skills/kun-card-integration/references/产品能力/异常码处理.md)：HTTP / 平台公共码 / `body.code`（KLC*）分层、处理动作表与决策树；SKILL/CAPABILITY/排障交叉引用。

## kun-card-integration 1.3.0 - 2026-11-05

**整合统一对接 skill**：新接入 + 旧 VCC 迁移合入同一 `kun-card-integration`（不另开迁移 skill）。新增 `CAPABILITY.md` 完整能力清单、`references/迁移/`（总览/对照表/鉴权/mapping.yaml）、`scripts/lookup_mapping.py`。约定无双轨期；`user-cards`/`card-remark` 标 `pending_add`。

## kun-card-integration 1.2.0 - 2026-11-05

**多语言对齐 yop-demo**：Skill / README / 最小跑通 / 外部指南明确支持 Python、Java、Java-Web、Node.js、TypeScript、Go、PHP、.NET；新增 `references/产品能力/多语言对齐.md`；仓库已落盘 Py/Java 样例，其余语言按同构判态由 Agent 生成。

## kun-card-integration 1.1.0 - 2026-11-04

强化商户交付：**几分钟跑通 + 可落地代码**。新增 `状态判断与异常处理.md`、`examples/`、`scripts/kun_client.py`；SKILL 验收标准含判态/异常/查单补偿。技能仓库迁至独立目录 `yeezus-skills`。

新增对外文档 [`docs/外部机构快速对接指南.md`](./docs/外部机构快速对接指南.md)：安装、对话话术、15 分钟路径与验收清单。

## kun-card-integration 1.0.0 - 2026-11-04

新增 **`kun-card-integration`**：KUN 卡开放 API 接入技能（商务卡 / 消费卡 / Webhook）。
