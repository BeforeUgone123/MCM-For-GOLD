---
name: mcm-gold-t3-audit-data
description: 数学建模竞赛 T3 数据审计专家。用于建立数据字典和单位口径，检查缺失、异常、组合键覆盖与结构性零，设计无泄漏划分和可逆清洗，保护官方工作簿结构，建立内置 Nature claim-to-file 数据证据图，并冻结带 SHA-256 的建模数据。用户提到数据清洗、EDA、数据质量、Excel 模板、泄漏或 T3 Gate 时使用。
---

# T3 数据审计

先读[输出目录契约](../mcm-gold/references/output-layout.md)、[独立 Review 评分契约](../mcm-gold/references/stage-review-scoring.md)、[阶段交接契约](../mcm-gold/references/stage-contract.md)、[证据契约](../mcm-gold/references/evidence-contract.md)、[内置 Nature 证据与数据规范](../mcm-gold/references/nature-evidence-data.md)和[对抗门禁](../mcm-gold/references/adversarial-gates.md)。本阶段不通过“清洗得更漂亮”来制造有利结论。

## 必需输入

- 题面附件原件、来源说明、官方结果模板和原始文件哈希。
- T1 的逐问输入需求；T2 的变量、单位、跨问接口和结论边界。
- 计划的独立样本单位、训练/验证/测试策略与时间方向。

## 执行

1. 把题面、官方数据和模板的只读副本冻结到 `MCM-Result/Competition-Materials/`，记录文件名、大小、SHA-256 和获取方式；不得覆盖原件。
2. 建数据字典：表/字段、类型、单位、量纲、范围、缺失率、唯一性、时间含义、来源和下游用途。
3. 审计缺失、异常、重复、时间戳、单位混用、口径变化、总量/组成守恒和跨表一致性。
3b. **题面给出的关键量与数据对象的对应关系 MUST 实测，并把匹配残差写进台账**。凡题面用坐标、编号、名称指认某个实体（突水点、站点、样本、时刻），都要量出它到各类候选对象的距离/差异再判定属于哪一类，不得按「最常见的那一类」直接匹配。实测（2025D 矿井巷道网络）：题面给的 7 个关键点到最近**端点**是 15–198 m，看起来像坐标有噪声；量到最近**巷道线段**只有 0.0002–0.0157 m，位置比恰为 0.500 / 0.250 / 1.000——它们本就是巷道内部点，题面也确实写着「巷道的某一点发生突水」。按「图上的点＝节点」这一标准套路匹配，突水点会凭空移动近 200 m 且拓扑关系全错，而报告上只会显示「已匹配」。**匹配残差为 0 才叫匹配上；非 0 就必须解释它属于哪一类对象。**
4. 对模型所有候选键做覆盖审计。把未出现组合逐项判成 `结构性0|未知缺失|不适用`，禁止因键未出现而漏约束。
5. 逐步记录清洗动作、理由、影响行数、可逆性和前后统计；不静默删除、不用全数据统计量污染验证集。
6. 画分布、时序、相关、缺失模式和分组覆盖体检图。图只用于发现问题，不自动证明因果或方法选择。
7. 按独立实验单位划分数据；时序按时间切，分组样本按组隔离。把预处理拟合限制在训练折内。
8. 对官方结果模板建立“业务键 -> 工作表/行/列”映射，登记合并单元格、公式、header/footer、样式和对象。先保留原包结构，再设计业务值、显示格式、包结构和字节哈希四层回读。
9. 冻结清洗后数据和拆分索引，记录 SHA-256；后续修复生成新版本并登记 supersession。
10. 建 `SOURCE_DATA_MAP.csv`，把 raw、processed、split、figure source、模型输出和第三方数据映射到 C/R/S/F-id、实际位置、哈希、访问路径、限制与生成脚本。**建完立即跑 [`verify_evidence_map.py`](../mcm-gold/templates/verify_evidence_map.py) 并读实际输出**——这条要求此前只有文字、没有机检，实测四个演练工作区里三个根本没建这个文件、剩下一个只有表头零条目，而其中一题走完了 T0–T8。哈希只登记不核对等于没登记：它是「主张 → 数据文件」的索引，一旦失效，所有 claim 的可追溯性一起失效。
11. 访问路径只用真实状态：`official_attachment|support_package|public_source|restricted_third_party|not_applicable`。没有真实仓库或条款时，不写 DOI、accession、license、embargo 或“可向作者索取”。

## 产物

- `MCM-Result/Competition-Materials/RAW_MANIFEST.sha256` 与 `MCM-Result/Intermediate-Outputs/FROZEN_MANIFEST.sha256`。
- `MCM-Result/Review-Results/T3_DATA_DICTIONARY.csv`、`T3_DATA_QUALITY.md`、`T3_KEY_COVERAGE.csv`。
- `MCM-Result/Data-Scripts/src/clean_data.*`、`MCM-Result/Intermediate-Outputs/split_index.*` 和 `MCM-Result/Data-Figures/` 下的可视化体检图。
- `MCM-Result/Review-Results/T3_TEMPLATE_MAP.csv`：存在官方结果模板时生成。
- `MCM-Result/Intermediate-Outputs/SOURCE_DATA_MAP.csv`：主张到原始/处理/图源数据及实际交付位置的映射。
- `MCM-Result/Intermediate-Outputs/RESULTS.md` 中的数据审计 R-id 与 `ASSUMPTIONS.md` 中的口径假设。

## 独立 Review

冻结 T3 产物后，由不同上下文 reviewer 按通用 30 分与 T3 专属 70 分评分，逐条核验 `T3-G1` 至 `T3-G6`。无官方模板时必须执行 rubric 预设的替代检查，禁止删除项目或重分配权重。

## Gate

仅在数据字典、审计报告、清洗脚本、冻结数据及哈希齐全时通过。必须明确数据支持与不支持的结论范围，候选键覆盖和结构性零已处理，划分无可见泄漏；关键数据已进入 SOURCE_DATA_MAP 且实际位置可回读；有官方模板时空模板哈希、映射和回读设计齐全。live 模式来源、单位和关键口径需 H-003。

致命数据缺陷无法可靠修复时返回 `BLOCKED` 或采用已披露的稳健降级，不构造复杂脆弱的补值链。把冻结数据、拆分索引、缺陷、哈希、R/H 编号和 T4 输入写入 `[HANDOFF T3]`。
