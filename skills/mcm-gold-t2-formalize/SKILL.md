---
name: mcm-gold-t2-formalize
description: 数学建模竞赛 T2 情报检索与数学形式化专家。用于建立可信来源链和机理清单，执行内置 Nature claim 分段与支撑分级，定义变量、目标、方程、约束和跨问接口，比较主备路线，预注册操作性结论和探索性工件，并准备 H-002/H-003 裁决。用户提到文献调研、机理、数学形式化、路线选择或 T2 Gate 时使用。
---

# T2 情报与数学形式化

先读[阶段交接契约](../mcm-gold/references/stage-contract.md)、[调研路由](../mcm-gold/references/research-and-skill-routing.md)、[方法图谱](../mcm-gold/references/methods-atlas.md)、[证据契约](../mcm-gold/references/evidence-contract.md)、[内置 Nature 证据与数据规范](../mcm-gold/references/nature-evidence-data.md)和[人机责任边界](../mcm-gold/references/human-ai-charter.md)。

## 必需输入

- T1 逐问拆解、所选题原文、附件字段和 H-001 状态。
- 当前可用数据、工具链、联网能力、时间盒与关键风险。
- 用户或赛事提供的规则、领域材料和已知口径。

## 情报协议

1. 用**直接访问官方首页、DOI 或库官方文档 URL**确认联网能力，不用通用搜索引擎做连通性探针。不可用时设置 `research.online=false`，只使用题面、附件和队伍已有且可核验资料。
2. live 竞赛期间只检索标准、数据、论文和官方口径；不浏览、发布或讨论本届赛题的解析、代码和交流内容。
3. **执行[赛事规则](../mcm-gold/references/rules-2026.md)第五节「检索纪律」的禁入域名清单**（参赛规则第 5 条点名 `tieba.baidu.com`、`zhihu.com`、`xiaohongshu.com`、`csdn.net`、`github.com` 等，规则为开放列举，同性质题解/代码分享站同等对待）。live 模式只允许直接访问已判定安全的官方/标准/论文/数据 URL，或使用能在请求前强制域名白名单的检索接口；工具不能强制白名单时，不做开放网页检索。开检索前把白名单、禁入域名和直接 URL 写入 `research/SEARCH_LOG.md`；误开禁入页面时立即关闭、登记 `SEARCH_LOG.md` 与 `RISKS.md`，该页内容不得进入任何产物。需要库文档时改用官方文档站或本地 `pip show` / `help()` / `print(dir(库))`。
4. 来源分为 A 官方/标准/同行评议、B 机构报告/数据文档、C 博客/论坛/AI 线索。C 级永不作为论文论据。
5. 对关键事实、参数区间、方法适用条件和失效模式至少做独立来源交叉验证；每条采用事实立即写 S-id。
6. 经典方法的出处**先查**[可引用书目](../mcm-gold/references/literature-library.md)（AHP/TOPSIS/ARIMA/K-means 等已逐条核验），前沿方法查[前沿卡](../mcm-gold/references/frontier-cards.md)的源列；两处都没有再联网检索。书目库只保证字段正确，**不代表已读过**——未读过的只能引方法出处，不得转述其结论。
7. 先形成来源支持的候选路线矩阵，再建模；禁止模型写完后反向拼引用。
8. 把可引用文本拆成单一 C-id，提取对象、条件、方向、范围和因果强度；为每个 S-id 标 `strong|partial|background|limiting|metadata-only`。
9. 标题或元数据相关不等于支撑。采用来源至少核对摘要或正文；`metadata-only` 永不进入论文，限制/冲突来源必须保留。
10. 用户明确要求 Nature/CNS 时才收窄期刊范围；普通国赛按权威性与适题性选择来源，不把 CNS 当作质量同义词。

## 形式化

1. 建机理清单，逐条标 `采用|不采用|待核`，说明如何进入方程、约束、先验或验证，而非只写背景。
2. 统一符号、单位、索引集合、决策变量、状态变量、参数、随机量和观测量。
3. 对每问写输入、输出、目标/方程/约束、数学类型、识别条件、评价指标、验证方式与禁止外推范围。
4. 显式定义跨问接口：上游文件、字段、单位、哈希、冻结时机与下游用途。
5. 把新假设写入 `ASSUMPTIONS.md`，说明依据、影响、可证伪检查和敏感性计划。
6. 比较主路线、备选路线和最小降级路线，估计运行时间、可复现成本、可验证性与失败触发器。
7. 证据不足以支撑题面字面强结论时，分别预注册 `operational_claim` 与醒目标注的 `literal_artifact`，写清假设、失败指标和禁止用途，不降低题面 Gate。

## 产物

- `research/SEARCH_LOG.md`、`research/MECHANISM_MAP.md`、`SOURCES.md`。
- `T2_FORMALIZATION.md`：统一符号、逐问定义、跨问接口和结论边界。
- `T2_ROUTE_MATRIX.csv`：主、备、降级路线的证据、成本和失败条件。
- `T2_CLAIM_SOURCE_MAP.csv`：C-id、原文、claim 类型、边界、S-id、支撑等级和采用状态。
- `ASSUMPTIONS.md`、`DECISIONS.md` 与 H-002/H-003 待核项。

## Gate

每个小问均有输入、变量/参数、数学对象、物理输出、验证和跨问接口；关键事实有 S-id 与支撑等级，metadata-only 未被采用；`SEARCH_LOG.md` 已登记禁入域名清单且无禁入域名采用记录；假设有检验计划；路线有备选和停止条件。live 模式路线/简化边界等待 H-002，关键事实/单位/口径进入 H-003。等待时返回 `NEEDS_HUMAN`，不得把候选路线写成最终路线。

把冻结定义、来源、假设、路线、接口、D/S/H 编号和 T3/T4 所需数据契约写入 `[HANDOFF T2]`。
