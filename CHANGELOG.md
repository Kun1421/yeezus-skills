# 变更历史

最新条目置顶；技能版本以各自 `SKILL.md` frontmatter 为准。

## kun-card-integration 1.3.0 - 2026-11-05

**整合统一对接 skill**：新接入 + 旧 VCC 迁移合入同一 `kun-card-integration`（不另开迁移 skill）。新增 `CAPABILITY.md` 完整能力清单、`references/迁移/`（总览/对照表/鉴权/mapping.yaml）、`scripts/lookup_mapping.py`。约定无双轨期；`user-cards`/`card-remark` 标 `pending_add`。

## kun-card-integration 1.2.0 - 2026-11-05

**多语言对齐 yop-demo**：Skill / README / 最小跑通 / 外部指南明确支持 Python、Java、Java-Web、Node.js、TypeScript、Go、PHP、.NET；新增 `references/产品能力/多语言对齐.md`；仓库已落盘 Py/Java 样例，其余语言按同构判态由 Agent 生成。

## kun-card-integration 1.1.0 - 2026-11-04

强化商户交付：**几分钟跑通 + 可落地代码**。新增 `状态判断与异常处理.md`、`examples/`、`scripts/kun_client.py`；SKILL 验收标准含判态/异常/查单补偿。技能仓库迁至独立目录 `yeezus-skills`。

新增对外文档 [`docs/外部机构快速对接指南.md`](./docs/外部机构快速对接指南.md)：安装、对话话术、15 分钟路径与验收清单。

## kun-card-integration 1.0.0 - 2026-11-04

新增 **`kun-card-integration`**：KUN 卡开放 API 接入技能（商务卡 / 消费卡 / Webhook）。
