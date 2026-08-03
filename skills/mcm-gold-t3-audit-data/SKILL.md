---
name: mcm-gold-t3-audit-data
description: 数学建模竞赛 T3 数据审计专家。用于建立数据字典和单位口径，检查缺失、异常、组合键覆盖与结构性零，设计无泄漏划分和可逆清洗，保护官方工作簿结构，建立内置 Nature claim-to-file 数据证据图，并冻结带 SHA-256 的建模数据。用户提到数据清洗、EDA、数据质量、Excel 模板、泄漏或 T3 Gate 时使用。
---

# T3 数据审计

先读[阶段交接契约](../mcm-gold/references/stage-contract.md)、[证据契约](../mcm-gold/references/evidence-contract.md)、[内置 Nature 证据与数据规范](../mcm-gold/references/nature-evidence-data.md)和[对抗门禁](../mcm-gold/references/adversarial-gates.md)。本阶段不通过“清洗得更漂亮”来制造有利结论。

## 必需输入

- 题面附件原件、来源说明、官方结果模板和原始文件哈希。
- T1 的逐问输入需求；T2 的变量、单位、跨问接口和结论边界。
- 计划的独立样本单位、训练/验证/测试策略与时间方向。

## 执行

1. 冻结原始文件，记录文件名、大小、SHA-256、获取方式和只读副本；不得覆盖原件。
2. 建数据字典：表/字段、类型、单位、量纲、范围、缺失率、唯一性、时间含义、来源和下游用途。
3. 审计缺失、异常、重复、时间戳、单位混用、口径变化、总量/组成守恒和跨表一致性。
4. 对模型所有候选键做覆盖审计。把未出现组合逐项判成 `结构性0|未知缺失|不适用`，禁止因键未出现而漏约束。
5. 逐步记录清洗动作、理由、影响行数、可逆性和前后统计；不静默删除、不用全数据统计量污染验证集。
6. 画分布、时序、相关、缺失模式和分组覆盖体检图。图只用于发现问题，不自动证明因果或方法选择。
7. 按独立实验单位划分数据；时序按时间切，分组样本按组隔离。把预处理拟合限制在训练折内。
8. 对官方结果模板建立“业务键 -> 工作表/行/列”映射，登记合并单元格、公式、header/footer、样式和对象。先保留原包结构，再设计业务值、显示格式、包结构和字节哈希四层回读。
9. 冻结清洗后数据和拆分索引，记录 SHA-256；后续修复生成新版本并登记 supersession。
10. 建 `SOURCE_DATA_MAP.csv`，把 raw、processed、split、figure source、模型输出和第三方数据映射到 C/R/S/F-id、实际位置、哈希、访问路径、限制与生成脚本。
11. 访问路径只用真实状态：`official_attachment|support_package|public_source|restricted_third_party|not_applicable`。没有真实仓库或条款时，不写 DOI、accession、license、embargo 或“可向作者索取”。

## 产物

- `data/RAW_MANIFEST.sha256`、`data/FROZEN_MANIFEST.sha256`。
- `T3_DATA_DICTIONARY.csv`、`T3_DATA_QUALITY.md`、`T3_KEY_COVERAGE.csv`。
- `src/clean_data.*`、`data/split_index.*` 和可视化体检图。
- `T3_TEMPLATE_MAP.csv`：存在官方结果模板时生成。
- `SOURCE_DATA_MAP.csv`：主张到原始/处理/图源数据及实际交付位置的映射。
- `RESULTS.md` 中的数据审计 R-id 与 `ASSUMPTIONS.md` 中的口径假设。

## Gate

仅在数据字典、审计报告、清洗脚本、冻结数据及哈希齐全时通过。必须明确数据支持与不支持的结论范围，候选键覆盖和结构性零已处理，划分无可见泄漏；关键数据已进入 SOURCE_DATA_MAP 且实际位置可回读；有官方模板时空模板哈希、映射和回读设计齐全。live 模式来源、单位和关键口径需 H-003。

致命数据缺陷无法可靠修复时返回 `BLOCKED` 或采用已披露的稳健降级，不构造复杂脆弱的补值链。把冻结数据、拆分索引、缺陷、哈希、R/H 编号和 T4 输入写入 `[HANDOFF T3]`。
