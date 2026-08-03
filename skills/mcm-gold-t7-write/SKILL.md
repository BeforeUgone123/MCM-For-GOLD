---
name: mcm-gold-t7-write
description: 数学建模竞赛 T7 论文与图表专家。内置 Nature SourceModel、论证架构、figure contract、支撑分级、语言边界和 Office 规格，用于组织逐问叙事，确保正文/图表/RESULTS 一致，写出含数值与边界的摘要，并生成提交版和阅读版供 H-004 确认。用户提到建模论文、摘要、图表、DOCX/PPTX、写作或 T7 Gate 时使用。
---

# T7 论文与图表

先读[阶段交接契约](../mcm-gold/references/stage-contract.md)、[写作与评分](../mcm-gold/references/rubric-and-writing.md)、[证据契约](../mcm-gold/references/evidence-contract.md)、[内置 Nature 证据与数据规范](../mcm-gold/references/nature-evidence-data.md)、[内置 Nature 科学图表规范](../mcm-gold/references/nature-figures.md)、[内置 Nature 写作与 Office 规范](../mcm-gold/references/nature-writing-office.md)和[论文模板](../mcm-gold/templates/paper-templates.md)。从 T4 起滚动写作，不把写作留到最后。

## 必需输入

- T1 逐问字面工件，T2 冻结定义与来源，T4/T5 结果与基线。
- T6 的确认、受限、否决主张及可用表述边界。
- `RESULTS.md`、`SOURCES.md`、claim/figure 台账、规则包和当前论文。

## 执行

1. 先生成唯一 `MCM_SOURCE_MODEL.yaml`：工作类型、论证弧、中心交付、难点、路线、主张、关键证据、信任检验、创新、复用价值、限制和物理工件。只引用已有 C/R/S/F-id。
2. 冻结中心主张、证据层级、适用范围和限制。未经 T6 确认的结果不得进入摘要确定性结论。
3. 为每张主图完成 figure contract：核心结论、角色、archetype、面板、源表、脚本、视觉编码、统计、失败状态和 caption boundary。
4. 图表先行，再写正文。主证据为 hero，验证和控制视觉降级；最终尺寸核查读取真实 SVG/PDF/预览。
5. 按评委读者路径写：题目要求 -> 难点 -> 模型合理性 -> 结果 -> 信任证据 -> 创新 -> 边界。每个小问定位题意接口、数学定义、求解步骤、结果图/表、验证和解释边界。
6. 先修 `work_type -> section role -> paragraph logic -> claim/evidence/boundary`，最后润色句子。不得用流畅语言隐藏证据缺口或让 AI 新造核心论证。
7. 模型假设说明依据与影响；创新点用同预算基线收益表达；失败或不确定性放在结果附近，不埋在结尾。
8. 摘要最后写成微型论文：问题/难点、路线、每问具体数值、信任证据、创新和关键边界。所有数字从 R-id 回读。
9. 逐项核对正文数字 = 图表数字 = `RESULTS.md` 数字，claim 的引用与 `SOURCES.md` 支撑等级对齐，metadata-only 不进入正文。
10. `paper_format=word` 时，从 SourceModel 建 DocumentSpec，并直接用 `officecli` 生成和回读实际 DOCX；LaTeX 主线不绕到 Office。题面要求 PPTX 时从同一 SourceModel 建 SlideSpec 和实际 PPTX，不停在大纲。
11. 论文正文不出现训练状态、内部 H/R 编号、责任边界、支撑清单或不可提交横幅；这些只留在论文外工作区。
12. 若规则要求程序附录，生成完整合规提交版与省略程序的阅读审查版。`paper/main.pdf` 固定为纯论文入口，提交候选显式命名 `*_submission.pdf`。
13. 依据 rubric 自评，优先修复会妨碍评委 5-15 分钟核查的缺口，不为凑页数填充背景。

## 产物

- `paper/main.*` 与 `paper/main.pdf` 阅读审查版。
- `paper/*_submission.*` 与明确打包白名单。
- `MCM_SOURCE_MODEL.yaml`；Word/PPT 路线另含 DocumentSpec/SlideSpec、实际 Office 文件和 QA。
- `T7_FIGURE_CONTRACTS.md`、源表、图表和视觉核查记录。
- `T7_ARGUMENT_AUDIT.md`、`NATURE_QA.csv` 与 `SOURCE_DATA_MAP.csv` 的闭环记录。
- `T7_RUBRIC_REVIEW.md`、更新后的 claim/figure 台账。
- `T7_H004_BRIEF.md`：结果解释、摘要结论、主图和剩余风险。

## Gate

SourceModel、claim/figure/source-data 台账与论文一致；全文数字可追溯；摘要有具体数值和边界；每问六项齐全；图表经真实渲染核查；引用可访问且支撑等级足够；适用 Office 文件经 `officecli validate/view` 回读；提交版和阅读版不混淆；rubric 无单项低于及格线。live 模式必须由人完成 H-004，否则返回 `NEEDS_HUMAN`。

把最终主张、论文文件哈希、主图状态、H-004、剩余表达风险和 T8 打包白名单写入 `[HANDOFF T7]`。
