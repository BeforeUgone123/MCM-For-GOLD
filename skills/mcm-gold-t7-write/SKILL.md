---
name: mcm-gold-t7-write
description: 数学建模竞赛 T7 论文与图表专家。内置 Nature SourceModel、论证架构、figure contract、支撑分级、语言边界和 Office 规格，用于组织逐问叙事，确保正文/图表/RESULTS 一致，写出含数值与边界的摘要，并生成提交版和阅读版供 H-004 确认。用户提到建模论文、摘要、图表、DOCX/PPTX、写作或 T7 Gate 时使用。
---

# T7 论文与图表

先读[阶段交接契约](../mcm-gold/references/stage-contract.md)、[写作与评分](../mcm-gold/references/rubric-and-writing.md)、[可引用书目](../mcm-gold/references/literature-library.md)、[证据契约](../mcm-gold/references/evidence-contract.md)、[内置 Nature 证据与数据规范](../mcm-gold/references/nature-evidence-data.md)、[内置 Nature 科学图表规范](../mcm-gold/references/nature-figures.md)、[内置 Nature 写作与 Office 规范](../mcm-gold/references/nature-writing-office.md)和[论文模板](../mcm-gold/templates/paper-templates.md)。从 T4 起滚动写作，不把写作留到最后。

## 必需输入

- T1 逐问字面工件，T2 冻结定义与来源，T4/T5 结果与基线。
- T6 的确认、受限、否决主张及可用表述边界。
- `RESULTS.md`、`SOURCES.md`、`RISKS.md`、claim/figure 台账、规则包和当前论文。
- T1 的逐问接口清单与 T6 的 K-id、检验结论；缺上游证据时相应覆盖项只能标 `WEAK/MISSING`，不得用文字补成通过。

## 执行

1. 先生成唯一 `MCM_SOURCE_MODEL.yaml`：工作类型、论证弧、中心交付、难点、路线、主张、关键证据、信任检验、创新、复用价值、限制和物理工件。只引用已有 C/R/S/F-id。
2. 冻结中心主张、证据层级、适用范围和限制。未经 T6 确认的结果不得进入摘要确定性结论。
3. 为每张主图完成 figure contract：核心结论、角色、archetype、面板、源表、脚本、视觉编码、统计、失败状态和 caption boundary。
4. 图表先行，再写正文。主证据为 hero，验证和控制视觉降级；最终尺寸核查读取真实 SVG/PDF/预览。
5. 按评委读者路径写：题目要求 -> 难点 -> 模型合理性 -> 结果 -> 信任证据 -> 创新 -> 边界。每个小问定位题意接口、数学定义、求解步骤、结果图/表、验证和解释边界。
6. 初始化 `PAPER_COVERAGE_LEDGER.csv`，每问固定 `interface/definition/algorithm/result/validation/boundary` 六行。先从 T1/T6 回填所需内容和 C/K/R/P/V/D-id；完成实际 PDF 渲染后再回填可由 `pdftotext` 检索的 `paper_anchor`、`observed` 与状态。不得用目录标题、代码附录或支撑包路径冒充正文覆盖。
7. 先修 `work_type -> section role -> paragraph logic -> claim/evidence/boundary`，最后润色句子。不得用流畅语言隐藏证据缺口或让 AI 新造核心论证。
8. 模型假设说明依据与影响；创新点用同预算基线收益表达；失败或不确定性放在结果附近，不埋在结尾。
9. 凡把模型输出用于新场景/新数据的结论，正文 MUST 给出支撑域比例与被拒绝的外推部分，并写明对域外样本不给结论的理由。诚实标注拒答范围比给出一个域外的漂亮数字更容易得分——后者评委一核对分布就会当场质疑。
10. 摘要最后写成微型论文：问题/难点、路线、每问具体数值、信任证据、创新和关键边界。所有数字从 R-id 回读。
11. 逐项核对正文数字 = 图表数字 = `RESULTS.md` 数字，claim 的引用与 `SOURCES.md` 支撑等级对齐，metadata-only 不进入正文。
12. 参考文献逐条取自 [`literature-library.md`](../mcm-gold/references/literature-library.md)、前沿卡源列或 `SOURCES.md` 中实际核验过的条目；**禁止凭印象补写卷期页**。环境缺 `bibtex/natbib` 时手写 `thebibliography`，每条著录完成后用 `https://doi.org/<DOI>` 或本地全文实核一次——编造文献按反幻觉铁律视为造假。
13. `paper_format=word` 时，从 SourceModel 建 DocumentSpec，并直接用 `officecli` 生成和回读实际 DOCX；LaTeX 主线不绕到 Office。题面要求 PPTX 时从同一 SourceModel 建 SlideSpec 和实际 PPTX，不停在大纲。
14. 论文正文不出现训练状态、内部 H/R 编号、责任边界、支撑清单或不可提交横幅；这些只留在论文外工作区。
15. 在参考文献之前设置 2026 版“AI 工具使用声明”，从实际 `AI_USAGE.md` 二选一回填原文。使用 AI 时生成 `AI 工具使用详情.pdf` 并逐项回读工具名称/版本或型号、用途环节、提示与过程、采纳/人工修改/核验及核心建模与分析的队员主导证据；不把 AI 工具列入参考文献，不沿用 2025 版正文逐处标注旧模板。
16. LaTeX 路线只维护一个 `paper/body.tex` 科学正文源；`main.tex` 只引入正文，`*_submission.tex` 引入同一正文后追加由最终支撑目录实际遍历生成的文件列表与全部 `\lstinputlisting` 源程序。Word 路线也必须从同一 DocumentSpec 生成两版并做正文回读比对。
17. 逐行填写固定七维 `T7_RUBRIC_REVIEW.csv`。总分低于 `CONFIG.target.rubric_threshold` 或任一单项低于及格线时，修复实质缺口并让论文契约返回 `NEEDS_EXPANSION`；T7 阶段不得 `PASS/PASS_WITH_LIMITATIONS`，不能以自创评分表绕过。
18. 对最终阅读版、提交版、覆盖账本、rubric 和实际支撑/源程序目录运行 [`../mcm-gold/templates/verify_paper_contract.py`](../mcm-gold/templates/verify_paper_contract.py)，保存 `T7_PAPER_CONTRACT.json`。契约错误必须修复；明显短文只触发 `DEPTH_REVIEW_REQUIRED`，由 H-004 判断是否过度压缩，不按页数填充。
19. H-004 必须阅读实际 `main.pdf`，逐问确认解释、结果、主图、验证和边界。演练只能把覆盖行写成 `PROXY_REHEARSAL`，最终状态不得冒充正式 `PASS`。

## 产物

- `paper/main.*` 与 `paper/main.pdf` 阅读审查版。
- `paper/*_submission.*` 与明确打包白名单。
- `PAPER_COVERAGE_LEDGER.csv`、`T7_RUBRIC_REVIEW.csv` 与 `T7_PAPER_CONTRACT.json`。
- `MCM_SOURCE_MODEL.yaml`；Word/PPT 路线另含 DocumentSpec/SlideSpec、实际 Office 文件和 QA。
- `T7_FIGURE_CONTRACTS.md`、源表、图表和视觉核查记录。
- 从 `PAPER_COVERAGE_LEDGER.csv` 派生的 `T7_ARGUMENT_AUDIT.md`、`NATURE_QA.csv` 与 `SOURCE_DATA_MAP.csv` 闭环记录。
- 更新后的 claim/figure 台账。
- `T7_H004_BRIEF.md`：结果解释、摘要结论、主图和剩余风险。

## Gate

SourceModel、claim/figure/source-data 台账与论文一致；全文数字可追溯；摘要有具体数值和边界；`PAPER_COVERAGE_LEDGER.csv` 每问六项无 `WEAK/MISSING` 且锚点能在实际阅读版检索，validation 与主要 K-id 和检验证据闭环；图表经真实渲染核查；引用可访问且支撑等级足够，每条参考文献可追到书目库、前沿卡源列或已核验 S-id；2026 版 AI 声明位于参考文献之前且与过程记录一致；适用 Office 文件经 `officecli validate/view` 回读；两版共享科学正文且提交版确含实际文件列表和完整源程序；固定七维 rubric 总分达到目标且无单项低于及格线。live 模式的 `T7_PAPER_CONTRACT.json` 必须为 `PASS` 且由人完成 H-004，否则阶段返回 `NEEDS_HUMAN` 或 `BLOCKED`；无人演练契约上限为 `PROXY_REHEARSAL`，只能以非正式演练状态交接。

把最终主张、论文文件哈希、主图状态、H-004、剩余表达风险和 T8 打包白名单写入 `[HANDOFF T7]`。
